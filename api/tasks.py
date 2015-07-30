# -*- coding: utf-8 -*-

from celery import Celery
from contextlib import closing
from datetime import datetime
from dateutil import parser
from faker import Faker
from random import choice, randint
from re import compile, IGNORECASE
from requests import get
from scrapy.selector import Selector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import false
from sqlalchemy.sql.expression import func

from modules import database
from modules import models

from server import application
from settings import dictionary

celery = Celery('tasks')
celery.conf.add_defaults(application.config)


def get_graph(profile, url):
    contents = get_response(url).json()

    if 'error' in contents:
        raise Exception('Invalid URL')

    if 'id' in contents:
        profile.facebook_id = contents['id']
    if 'name' in contents:
        profile.name = contents['name']
    if 'about' in contents:
        profile.description = contents['about']
    if 'location' in contents:
        profile.location = []
        if 'street' in contents['location']:
            profile.location.append(contents['location']['street'])
        if 'city' in contents['location']:
            profile.location.append(contents['location']['city'])
        if 'state' in contents['location']:
            profile.location.append(contents['location']['state'])
        if 'country' in contents['location']:
            profile.location.append(contents['location']['country'])
        if 'zip' in contents['location']:
            profile.location.append(contents['location']['zip'])
        profile.location = ', '.join(profile.location)
    if 'category' in contents:
        profile.categories_primary = contents['category']
    if 'link' in contents:
        profile.urls_local = contents['link'].replace('http://', 'https://')
    if 'website' in contents:
        profile.urls_remote = contents['website']
    if 'likes' in contents:
        profile.set_likes(contents['likes'])
    if 'talking_about_count' in contents:
        profile.set_discussions(contents['talking_about_count'])
    return profile


def get_www(profile, url):
    contents = get_response(url).text

    if 'Security Check' in contents:
        raise Exception('Security Check')

    image = None
    match = compile(
        '<a.*?class="profilePicThumb".*?><img.*?src="(.*?)".*?>',
        IGNORECASE
    ).search(contents)
    if match:
        image = match.group(1)
    if image:
        profile.image = image

    return profile


def get_www_info(profile, url):
    contents = get_response(url).text

    if 'Security Check' in contents:
        raise Exception('Security Check')

    date = None
    match = compile((
        '<th class="label">('
        'Founded'
        '|'
        'Joined Facebook'
        '|'
        'Opened'
        ')</th><td class="data">(.*?)</td>'
    ), IGNORECASE).search(contents)
    if match:
        date = parser.parse(match.group(2)).date().isoformat()
    if date:
        profile.date = date

    return profile


def get_www_likes(profile, url):
    contents = get_response(url).text

    if 'Security Check' in contents:
        raise Exception('Security Check')

    selector = Selector(text=contents)

    others_age_group = None
    try:
        others_age_group = selector.xpath(
            '//span[@class="fsm fcg"]'
            '[contains(text(), "Most Popular Age Group")]/'
            'preceding-sibling::div/text()'
        ).extract()[0]
    except IndexError:
        pass
    if others_age_group:
        profile.others_age_group = others_age_group

    return profile


def get_proxies():
    # DEBUG
    return {
        'https': 'http://198.61.215.37:%(port)d' % {
            'port': (9151 + randint(1, 50)),
        },
    }
    # DEBUG
    return {} if dictionary['DEBUG'] else {
        'https': choice(dictionary['SERVERS']),
    }


def get_response(url):
    try:
        response = get(
            url,
            headers={
                'User-Agent': Faker().chrome(),
            },
            proxies=get_proxies(),
            timeout=15,
        )
        if response.status_code == 200:
            return response
        raise Exception(str(response.status_code))
    except Exception:
        raise


@celery.task
def process_profile(id):
    with closing(database.postgresql['session']()) as session:
        profile = session.query(models.profile).get(id)

        if not profile:
            return

        urls = profile.get_urls()
        if not urls:
            raise Exception('Invalid URLs')

        profile = get_graph(profile, urls['graph'])
        profile = get_www(profile, urls['www'])
        profile = get_www_info(profile, urls['www_info'])
        profile = get_www_likes(profile, urls['www_likes'])
        profile.timestamp = datetime.now()
        session.add(profile)
        session.commit()
        session.refresh(profile)
        profile.refresh()
        session.add(profile)
        session.commit()


@celery.task
def process_result(id):
    with closing(database.postgresql['session']()) as session:
        result = session.query(models.result).get(id)

        if not result:
            return
        if result.status:
            return

        contents = get_response(result.get_url()).text

        if 'Security Check' in contents:
            raise Exception('Security Check')

        selector = Selector(text=contents)
        for td in selector.xpath(
            '//table[@class="uiGrid _51mz mam"]/tbody/tr/td'
        ):
            name = None
            try:
                name = td.xpath('div/a/@title').extract()[0]
            except IndexError:
                pass
            if not name:
                raise Exception('Invalid Name')

            image = None
            try:
                image = td.xpath('div/a/img/@src').extract()[0]
            except IndexError:
                pass
            if not image:
                raise Exception('Invalid Image')

            categories_primary = None
            try:
                categories_primary = td.xpath(
                    'div/div/div/div/div/text()'
                ).extract()[0]
            except IndexError:
                pass

            urls_local = None
            try:
                urls_local = td.xpath('div/a/@href').extract()[0].replace(
                    'http://', 'https://'
                )
            except IndexError:
                pass
            if not urls_local:
                raise Exception('Invalid URL')

            profile = session.query(
                models.profile,
            ).filter(
                models.profile.urls_local == urls_local,
            ).first()
            if not profile:
                profile = models.profile()
            profile.name = name
            profile.image = image
            profile.categories_primary = categories_primary
            profile.urls_local = urls_local
            try:
                session.add(profile)
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise
        result.status = True
        session.add(result)
        session.commit()


@celery.task
def process_segment(id):
    with closing(database.postgresql['session']()) as session:
        segment = session.query(models.segment).get(id)

        if not segment:
            return
        if segment.status:
            return

        profile = models.profile()
        profile = get_graph(profile, segment.get_url())
        profile.urls_local = get_response(
            'https://www.facebook.com/%(value)s' % {
                'value': segment.value,
            }
        ).url.replace('http://', 'https://')
        if profile.urls_local:
            urls = profile.get_urls()
            if urls:
                profile = get_www(profile, urls['www'])
                profile = get_www_info(profile, urls['www_info'])
                profile = get_www_likes(profile, urls['www_likes'])
        session.add(profile)
        session.commit()
        session.refresh(profile)
        profile.refresh()
        session.add(profile)
        session.commit()

        segment.status = True
        session.add(segment)
        session.commit()

if __name__ == '__main__':
    with closing(database.postgresql['session']()) as session:
        '''
        for profile in session.query(
            models.profile,
        ).order_by('timestamp ASC')[0:1000]:
            process_profile.delay(profile.id)
        '''

        for result in session.query(
            models.result,
        ).filter(
            models.result.status == false(),
        ).order_by(func.random())[0:1000]:
            process_result.delay(result.id)

        '''
        for segment in session.query(
            models.segment,
        ).filter(
            models.segment.status == false(),
        ).order_by(func.random())[0:1000]:
            process_segment.delay(segment.id)
        '''

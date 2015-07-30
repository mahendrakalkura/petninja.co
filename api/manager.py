# -*- coding: utf-8 -*-

from contextlib import closing
from faker import Faker
from flask.ext.script import Manager
from logging import getLogger
from random import choice
from grequests import get, map
from string import ascii_uppercase
from sqlalchemy import or_
from sqlalchemy.sql import false
from sqlalchemy.sql.expression import func
from webassets.script import CommandLineEnvironment

from modules import database
from modules import decorators
from modules import log
from modules import models

from server import application, assets
from settings import dictionary
from tasks import process_profile, process_result, process_segment

manager = Manager(application, with_default_commands=False)


@manager.command
@decorators.profile(0)
def assets_build():
    CommandLineEnvironment(assets, getLogger('flask')).build()


@manager.command
@decorators.profile(0)
def assets_watch():
    CommandLineEnvironment(assets, getLogger('flask')).watch()


@manager.command
@decorators.profile(0)
def database_optimize():
    database.optimize()


@manager.command
@decorators.profile(0)
def models_optimize():
    models.optimize()


@manager.command
@decorators.profile(0)
def process_profile_():
    with closing(database.postgresql['session']()) as session:
        process_profile(
            session.query(models.profile).order_by(func.random()).first().id
        )


@manager.command
@decorators.profile(0)
def process_result_():
    with closing(database.postgresql['session']()) as session:
        process_result(
            session.query(
                models.result,
            ).filter(
                models.result.status == false(),
            ).order_by(func.random()).first().id
        )


@manager.command
@decorators.profile(0)
def process_segment_():
    with closing(database.postgresql['session']()) as session:
        process_segment(
            session.query(
                models.segment
            ).filter(
                models.segment.status == false(),
            ).order_by(func.random()).first().id
        )


@manager.command
@decorators.profile(0)
def profiles_and_profiles_discussions_and_profiles_likes():
    with closing(database.postgresql['session']()) as session:
        log.write(10, 'profiles', 1)
        for profile in session.query(
            models.profile,
        ).filter(or_(
            models.profile.numbers_likes > 0,
            models.profile.numbers_discussions_absolute > 0,
            models.profile.numbers_discussions_relative > 0,
        )).all():
            log.write(10, profile.id, 2)
            log.write(10, 'profiles_discussions', 3)
            for index, profile_discussion in enumerate(
                profile.discussions.order_by('timestamp desc')[1:]
            ):
                log.write(10, index + 2, 4)
                session.delete(profile_discussion)
                session.commit()
            log.write(10, 'profiles_likes', 3)
            for index, profile_like in enumerate(
                profile.likes.order_by('timestamp desc')[1:]
            ):
                log.write(10, index + 2, 4)
                session.delete(profile_like)
                session.commit()
        log.write(10, 'profiles_discussions', 1)
        for profile_discussion in session.query(
            models.profile_discussion
        ).all():
            profile_discussion.profile.refresh()
            session.add(profile_discussion)
            session.commit()
            log.write(10, profile_discussion.profile.id, 2)
        log.write(10, 'profiles_likes', 1)
        for profile_like in session.query(models.profile_like).all():
            profile_like.profile.refresh()
            session.add(profile_like)
            session.commit()
            log.write(10, profile_like.profile.id, 2)


@manager.command
@decorators.profile(0)
def proxies():
    fake = Faker()
    requests = []
    for server in dictionary['SERVERS']:
        requests.append(get(
            'https://www.facebook.com/directory/pages/%(alphabet)s' % {
                'alphabet': choice(list(ascii_uppercase) + ['others']),
            },
            headers={
                'User-Agent': fake.user_agent(),
            },
            proxies={
                'https': server,
            },
            timeout=15,
        ))
    responses = map(requests)
    for index, _ in enumerate(dictionary['SERVERS']):
        status = 'OK'
        if (
            not responses[index]
            or
            not responses[index].status_code == 200
            or
            'Security Check' in responses[index].text
        ):
            status = 'Not OK'
        log.write(10, '%(server)-46s %(status)s' % {
            'server': dictionary['SERVERS'][index],
            'status': status,
        }, 1)

if __name__ == '__main__':
    manager.run()

# -*- coding: utf-8 -*-

from contextlib import closing
from re import compile
from simplejson import dumps, loads
from sqlalchemy import Column, exc
from sqlalchemy.event import listen
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import backref, relationship
from sqlalchemy.types import TEXT, TypeDecorator
from warnings import catch_warnings, simplefilter

from modules import database


class json(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return dumps(value)

    def process_result_value(self, value, dialect):
        return loads(value)


class mutators_dict(Mutable, dict):

    @classmethod
    def coerce(class_, key, value):
        if not isinstance(value, mutators_dict):
            if isinstance(value, dict):
                return mutators_dict(value)
            return Mutable.coerce(key, value)
        return value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

with catch_warnings():
    simplefilter('ignore', category=exc.SAWarning)

    class user(database.mysql['base']):
        __tablename__ = 'wp_users'
        __table_args__ = {
            'autoload': True,
        }

        memberships = relationship(
            'membership',
            backref='user',
            lazy='dynamic',
            primaryjoin='user.ID==foreign(membership.user_id)',
        )

        meta = relationship(
            'meta',
            backref='user',
            lazy='dynamic',
            primaryjoin='user.ID==foreign(meta.user_id)',
        )

        def get_plan(self):
            if self.is_administrator():
                return 'Pro'
            instance = self.memberships.filter(
                membership.status == 'active'
            ).order_by('id desc').first()
            if not instance:
                return ''
            if instance.membership_id == 1:
                return 'Free'
            if instance.membership_id == 2:
                return 'Personal'
            if instance.membership_id == 3:
                return 'Pro'
            return ''

        def is_administrator(self):
            if self.meta.filter(
                meta.meta_key == 'wp_capabilities',
                meta.meta_value.like('%administrator%')
            ).count():
                return True
            return False

    class membership(database.mysql['base']):
        __tablename__ = 'wp_pmpro_memberships_users'
        __table_args__ = {
            'autoload': True,
        }

    class meta(database.mysql['base']):
        __tablename__ = 'wp_usermeta'
        __table_args__ = {
            'autoload': True,
        }

    class option(database.mysql['base']):
        __tablename__ = 'wp_options'
        __table_args__ = {
            'autoload': True,
        }

        @staticmethod
        def get_dictionary(session):
            d = {}
            for option_name, option_value in {
                'facebook_search_engine_searches': 25,
                'facebook_search_engine_watchlists': 25,
            }.items():
                d[option_name] = int(session.query(
                    option,
                ).filter(
                    option.option_name == option_name,
                ).first().option_value)
            return d

    class result(database.postgresql['base']):
        __tablename__ = 'results'
        __table_args__ = {
            'autoload': True,
        }

        def get_url(self):
            return (
                'https://www.facebook.com/directory/pages/'
                '%(alphabet)s-%(start)s-%(stop)s'
            ) % {
                'alphabet': self.alphabet,
                'start': self.start,
                'stop': self.stop,
            }

    class segment(database.postgresql['base']):
        __tablename__ = 'segments'
        __table_args__ = {
            'autoload': True,
        }

        def get_url(self):
            return 'https://graph.facebook.com/%(value)s' % {
                'value': self.value,
            }

    class profile(database.postgresql['base']):
        __tablename__ = 'profiles'
        __table_args__ = {
            'autoload': True,
        }

        def refresh(self):
            discussion = self.discussions.order_by('timestamp desc').first()
            if discussion:
                self.numbers_discussions_absolute = discussion.number
            like = self.likes.order_by('timestamp desc').first()
            if like:
                self.numbers_likes = like.number
            if self.numbers_likes:
                self.numbers_discussions_relative = ((
                    self.numbers_discussions_absolute * 100.00
                ) / (self.numbers_likes * 1.00))

        def get_keywords(self):
            if not self.description:
                return ''
            keywords = {}
            for word in compile('[ ]([a-z]+)[ ]').findall(self.description):
                if len(word) <= 2:
                    continue
                if not word in keywords:
                    keywords[word] = 0
                keywords[word] += 1
            return '|'.join([keyword[0] for keyword in sorted(
                keywords.items(), key=lambda keyword: keyword[1], reverse=True
            )[0:10]])

        def get_segment(self):
            match = compile(
                '^https://www\.facebook\.com/(\d+)$'
            ).search(self.urls_local)
            if match:
                return match.group(1)
            match = compile(
                '^https://www\.facebook\.com/pages/[^/]+/(\d+)$'
            ).search(self.urls_local)
            if match:
                return match.group(1)
            match = compile(
                '^https://www\.facebook\.com/([^/]+)$'
            ).search(self.urls_local)
            if match:
                return match.group(1)

        def get_urls(self):
            segment = self.get_segment()
            if not segment:
                return
            graph = 'https://graph.facebook.com/%(segment)s' % {
                'segment': segment,
            }
            www = 'https://www.facebook.com/%(segment)s?_fb_noscript=1' % {
                'segment': segment,
            }
            if '/pages/' in self.urls_local:
                www = '%(url)s?id=%(segment)s' % {
                    'segment': segment,
                    'url': self.urls_local,
                }
            www_info = (
                'https://www.facebook.com/%(segment)s/info?_fb_noscript=1'
            ) % {
                'segment': segment,
            }
            if '/pages/' in self.urls_local:
                www_info = '%(url)s?_fb_noscript=1&id=%(segment)s&sk=info' % {
                    'segment': segment,
                    'url': self.urls_local,
                }
            www_likes = (
                'https://www.facebook.com/%(segment)s/likes?_fb_noscript=1'
            ) % {
                'segment': segment,
            }
            if '/pages/' in self.urls_local:
                www_likes = (
                    '%(url)s?_fb_noscript=1&id=%(segment)s&sk=likes'
                ) % {
                    'segment': segment,
                    'url': self.urls_local,
                }
            return {
                'graph': graph,
                'www': www,
                'www_info': www_info,
                'www_likes': www_likes,
            }

        def set_discussions(self, number):
            self.discussions.append(profile_discussion(**{
                'number': number,
            }))

        def set_likes(self, number):
            self.likes.append(profile_like(**{
                'number': number,
            }))

    class profile_discussion(database.postgresql['base']):
        __tablename__ = 'profiles_discussions'
        __table_args__ = {
            'autoload': True,
        }

        profile = relationship(
            'profile',
            backref=backref(
                'discussions',
                cascade='all',
                lazy='dynamic',
            ),
        )

    class profile_like(database.postgresql['base']):
        __tablename__ = 'profiles_likes'
        __table_args__ = {
            'autoload': True,
        }

        profile = relationship(
            'profile',
            backref=backref(
                'likes',
                cascade='all',
                lazy='dynamic',
            ),
        )

    class search(database.postgresql['base']):
        __tablename__ = 'searches'
        __table_args__ = {
            'autoload': True,
        }

        contents = Column(mutators_dict.as_mutable(json))

        def before_flush(self):
            if not self.contents:
                self.contents = {}

    class watchlist(database.postgresql['base']):
        __tablename__ = 'watchlists'
        __table_args__ = {
            'autoload': True,
        }

        contents = Column(mutators_dict.as_mutable(json))

        profile = relationship(
            'profile',
            backref=backref(
                'watchlists',
                cascade='all',
                lazy='dynamic',
            ),
        )

        def to_dictionary(self):
            return {
                'contents': self.contents,
                'id': self.id,
                'profile': self.profile.to_dictionary(),
            }

        def before_flush(self):
            if not self.contents:
                self.contents = {
                    'discussions': {
                        'operand': '+',
                        'quantity': '20.00',
                        'status': True,
                    },
                    'likes': {
                        'operand': '+',
                        'quantity': '5.00',
                        'status': True,
                    },
                }

    def postgresql_before_flush(session, context, instances):
        for instance in session.new:
            if isinstance(instance, search):
                instance.before_flush()
            if isinstance(instance, watchlist):
                instance.before_flush()
        for instance in session.dirty:
            if isinstance(instance, search):
                instance.before_flush()
            if isinstance(instance, watchlist):
                instance.before_flush()

    listen(
        database.postgresql['session'], 'before_flush', postgresql_before_flush
    )


def optimize():
    ids = []
    with closing(database.mysql['session']()) as session:
        ids = [
            u.ID for u in session.query(user).order_by('ID asc').all()
        ]
    with closing(database.postgresql['session']()) as session:
        session.query(
            search,
        ).filter(
            search.user_id.in_(ids),
        ).delete(synchronize_session=False)

        session.query(
            watchlist,
        ).filter(
            watchlist.user_id.in_(ids),
        ).delete(synchronize_session=False)

        session.commit()

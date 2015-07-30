# -*- coding: utf-8 -*-

from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import ThreadLocalMetaData

from modules import system

from settings import dictionary


def to_dictionary(instance):
    d = {}
    for column in instance.__table__.columns:
        d[column.name] = getattr(instance, column.name)
        if isinstance(d[column.name], datetime):
            d[column.name] = d[column.name].isoformat(' ')
        if isinstance(d[column.name], date):
            d[column.name] = d[column.name].isoformat()
    return d

mysql = {}
mysql['engine'] = create_engine(
    URL(**dictionary['MYSQL']),
    convert_unicode=True,
    echo=False,
    pool_recycle=15,
    pool_size=25,
    pool_timeout=15,
    strategy='threadlocal',
)
mysql['base'] = declarative_base(
    bind=mysql['engine'], metadata=ThreadLocalMetaData()
)
mysql['base'].to_dictionary = to_dictionary
mysql['session'] = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=mysql['engine'],
    expire_on_commit=True
))

postgresql = {}
postgresql['engine'] = create_engine(
    URL(**dictionary['POSTGRESQL']),
    convert_unicode=True,
    echo=False,
    pool_recycle=15,
    pool_size=25,
    pool_timeout=15,
    strategy='threadlocal',
)
postgresql['base'] = declarative_base(
    bind=postgresql['engine'], metadata=ThreadLocalMetaData()
)
postgresql['base'].to_dictionary = to_dictionary
postgresql['session'] = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=postgresql['engine'],
    expire_on_commit=True
))


def optimize():
    for command in [
        ' '.join([
            'mysqlcheck',
            '--all-in-1',
            '--auto-repair',
            '--check',
            '--databases %(database)s',
            '--host=%(host)s',
            '--password=%(password)s',
            '--port="%(port)s"',
            '--user=%(username)s',
        ]),
        ' '.join([
            'mysqlcheck',
            '--all-in-1',
            '--auto-repair',
            '--databases %(database)s',
            '--host=%(host)s',
            '--optimize',
            '--password=%(password)s',
            '--port="%(port)s"',
            '--user=%(username)s',
        ]),
        ' '.join([
            'mysqlcheck',
            '--all-in-1',
            '--auto-repair',
            '--databases %(database)s',
            '--host=%(host)s',
            '--password=%(password)s',
            '--port="%(port)s"',
            '--repair',
            '--user=%(username)s',
        ]),
        ' '.join([
            'mysqlcheck',
            '--all-in-1',
            '--analyze',
            '--auto-repair',
            '--databases %(database)s',
            '--host=%(host)s',
            '--password=%(password)s',
            '--port="%(port)s"',
            '--user=%(username)s',
        ]),
    ]:
        system.get_output(command % {
            'database': dictionary['MYSQL']['database'],
            'host': dictionary['MYSQL']['host'],
            'password': dictionary['MYSQL']['password'],
            'port': dictionary['MYSQL']['port'],
            'username': dictionary['MYSQL']['username'],
        })
    for command in [
        'VACUUM FULL',
        'VACUUM ANALYZE',
        'REINDEX SYSTEM %(database)s' % {
            'database': dictionary['POSTGRESQL']['database'],
        },
    ]:
        system.get_output(' '.join([
            'PGPASSWORD=%(password)s',
            'psql',
            '--command="%(command)s"',
            '--dbname="%(database)s"',
            '--host="%(host)s"',
            '--port="%(port)s"',
            '--quiet',
            '--username="%(username)s"',
        ]) % {
            'command': command,
            'database': dictionary['POSTGRESQL']['database'],
            'host': dictionary['POSTGRESQL']['host'],
            'port': dictionary['POSTGRESQL']['port'],
            'password': dictionary['POSTGRESQL']['password'],
            'username': dictionary['POSTGRESQL']['username'],
        })

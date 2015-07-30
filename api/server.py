# -*- coding: utf-8 -*-

from cStringIO import StringIO
from csv import QUOTE_ALL, writer
from flask import (
    abort,
    Flask,
    g,
    jsonify,
    render_template,
    request,
    Response,
    session,
    url_for
)
from flask.ext.assets import Bundle, Environment
from hashlib import md5
from os.path import abspath, dirname, isfile, join
from simplejson import loads
from sqlalchemy import distinct

from modules import classes
from modules import database
from modules import decorators
from modules import models
from modules import utilities

from settings import dictionary


def url_for_(rule, **kwargs):
    kwargs.setdefault('_external', True)
    return url_for(rule, **kwargs)

application = Flask(
    __name__,
    static_folder=join(abspath(dirname(__file__)), 'resources')
)

application.config.update(dictionary)

application.jinja_env.add_extension('jinja2.ext.do')
application.jinja_env.add_extension('jinja2.ext.loopcontrols')
application.jinja_env.add_extension('jinja2.ext.with_')

application.jinja_env.globals['url_for'] = url_for_

assets = Environment(application)

assets.cache = False
assets.debug = application.config['DEBUG']
assets.directory = application.static_folder
assets.manifest = 'json:assets/versions.json'
assets.url = application.static_url_path
assets.url_expire = True
assets.versions = 'timestamp'

assets.register('stylesheets', Bundle(
    Bundle(
        'stylesheets/all.less',
        filters='less',
        output='stylesheets/all.css'
    ),
    filters=None if application.config['DEBUG'] else 'cssmin,cssrewrite',
    output='assets/compressed.css'
))
assets.register('javascripts', Bundle(
    'vendors/lodash/dist/lodash.js',
    'vendors/jquery/dist/jquery.js',
    'vendors/angular/angular.js',
    'vendors/angular-route/angular-route.js',
    'vendors/restangular/dist/restangular.js',
    'vendors/bootstrap/dist/js/bootstrap.js',
    'vendors/typeahead.js/dist/typeahead.bundle.js',
    'javascripts/all.js',
    filters=None if application.config['DEBUG'] else 'rjsmin',
    output='assets/compressed.js'
))

columns = [
    ('name', 'Name'),
    ('location', 'Location'),
    ('categories_primary', 'Category'),
    ('numbers_likes', 'Likes'),
    ('numbers_discussions_absolute', 'Talking About'),
]
directions = [
    ('asc', 'Low to High'),
    ('desc', 'High to Low'),
]


@application.before_request
def before_request():

    def get_id_and_signature():
        try:
            return (
                request.headers['User-Id'], request.headers['User-Signature']
            )
        except KeyError:
            if application.config['DEBUG']:
                id = '1'
                return id, get_signature(id)
        return '', ''

    def get_plan():
        if g.user:
            return g.user.get_plan()
        return ''

    def get_signature(id):
        return md5(
            dictionary['SECRET_KEY'] + id + dictionary['SECRET_KEY']
        ).hexdigest()

    def get_user():
        id, signature = get_id_and_signature()
        if get_signature(id) == signature:
            return g.mysql.query(models.user).get(id)

    g.mysql = database.mysql['session']()
    g.postgresql = database.postgresql['session']()
    g.user = get_user()
    g.plan = get_plan()
    session.permanent = True


@application.after_request
def after_request(response):
    g.mysql.close()
    g.postgresql.close()
    response.headers['Access-Control-Allow-Headers'] = ', '.join([
        'Accept',
        'Content-Type',
        'Origin',
        'User-Id',
        'User-Signature',
        'X-Requested-With',
    ])
    response.headers['Access-Control-Allow-Methods'] = ', '.join([
        'DELETE',
        'GET',
        'HEAD',
        'OPTIONS',
        'POST',
        'PUT',
    ])
    response.headers['Access-Control-Allow-Origin'] = ', '.join([
        '*',
    ])
    response.headers['Access-Control-Max-Age'] = '86400'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@application.route('/searches/overview', methods=['GET'])
@decorators.authorize(['Free', 'Personal', 'Pro'])
def searches_overview():
    return render_template(
        'views/searches_overview.html', columns=columns, directions=directions
    )


@application.route('/searches/export', methods=['GET'])
@decorators.authorize(['Free', 'Personal', 'Pro'])
def searches_export():
    profiles, _ = get_profiles_and_pager(
        loads(request.args.get('filter')),
        loads(request.args.get('order_by')),
        int(request.args.get('limit', '25')),
        int(request.args.get('page', '1')),
    )
    csv = StringIO()
    writer(
        csv,
        delimiter=',',
        doublequote=True,
        lineterminator='\n',
        quotechar='"',
        quoting=QUOTE_ALL,
        skipinitialspace=True,
    ).writerows([[
        'Age Group',
        'Date',
        'Description',
        'Facebook ID',
        'Image',
        'Likes',
        'Local URL',
        'Location',
        'Name',
        'Primary Category',
        'Remote URL',
        'Secondary Category',
        'Talking About (%)',
        'Talking About',
    ]] + [[
        profile.others_age_group.encode('utf-8')
        if profile.others_age_group else '',
        profile.date.encode('utf-8') if profile.date else '',
        profile.description.encode('utf-8') if profile.description else '',
        profile.facebook_id if profile.facebook_id else '',
        profile.image.encode('utf-8'),
        utilities.get_integer(profile.numbers_likes),
        profile.urls_local.encode('utf-8'),
        profile.location.encode('utf-8') if profile.location else '',
        profile.name.encode('utf-8'),
        profile.categories_primary.encode('utf-8')
        if profile.categories_primary else '',
        profile.urls_remote.encode('utf-8')
        if profile.urls_remote else '',
        profile.categories_secondary.encode('utf-8')
        if profile.categories_secondary else '',
        utilities.get_float(profile.numbers_discussions_relative),
        utilities.get_integer(profile.numbers_discussions_absolute),
    ] for profile in profiles])
    return Response(
        csv.getvalue(),
        headers={
            'Content-Disposition': 'attachment; filename=export.csv',
        },
        mimetype='text/csv'
    )


@application.route('/watchlists/overview', methods=['GET'])
@decorators.authorize(['Pro'])
def watchlists_overview():
    return render_template('views/watchlists_overview.html')


@application.route('/restangular/profiles', methods=['GET'])
@decorators.authorize(['Free', 'Personal', 'Pro'])
def restangular_profiles():
    profiles, pager = get_profiles_and_pager(
        loads(request.args.get('filter')),
        loads(request.args.get('order_by')),
        int(request.args.get('limit', '25')),
        int(request.args.get('page', '1')),
    )
    return jsonify({
        'profiles': [profile.to_dictionary() for profile in profiles],
        'pager': {
            'count': pager.count,
            'first': pager.first,
            'last': pager.last,
            'next': pager.next,
            'pages_1': pager.get_pages(3),
            'pages_2': pager.pages,
            'previous': pager.previous,
        }
    })


@application.route('/restangular/profiles/<int:id>')
@decorators.authorize(['Personal', 'Pro'])
def restangular_profiles_get(id):

    def get_result_and_status():
        result = g.postgresql.query(models.profile).get(id)
        if not result:
            return {}, False
        return result.to_dictionary(), True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/searches', methods=['GET'])
@decorators.authorize(['Pro'])
def restangular_searches_get():
    return jsonify({
        'output': [
            search.to_dictionary()
            for search in g.postgresql.query(
                models.search,
            ).filter(
                models.search.user_id == g.user.ID,
            ).order_by('id asc').all()
        ],
    })


@application.route('/restangular/searches', methods=['POST'])
@decorators.authorize(['Pro'])
def restangular_searches_post():

    def get_result_and_status():
        name = request.json['name']
        if g.postgresql.query(
            models.search
        ).filter(
            models.search.user_id == g.user.ID,
            models.search.name == name,
        ).first():
            return 'Duplicate Name', False
        d = models.option.get_dictionary(g.mysql)
        if d[
            'facebook_search_engine_searches'
        ] < g.postgresql.query(models.search.user_id == g.user.ID).count():
            return 'You cannot save more than %(count)s searches.' % {
                'count': d['facebook_search_engine_searches'],
            }, False
        g.postgresql.add(models.search(**{
            'contents': request.json['contents'],
            'name': name,
            'user_id': g.user.ID,
        }))
        g.postgresql.commit()
        return 'The selected search was sucessfully saved.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/searches/<int:id>', methods=['PUT'])
@decorators.authorize(['Pro'])
def restangular_searches_put(id):

    def get_result_and_status():
        name = request.json['name']
        if g.postgresql.query(
            models.search
        ).filter(
            models.search.id != id,
            models.search.user_id == g.user.ID,
            models.search.name == name,
        ).first():
            return 'Duplicate Name', False
        search = g.postgresql.query(
            models.search
        ).filter(
            models.search.id == id,
            models.search.user_id == g.user.ID,
        ).first()
        if not search:
            return 'Invalid Search', False
        search.name = name
        search.contents = request.json['contents']
        g.postgresql.add(search)
        g.postgresql.commit()
        return 'The selected search was sucessfully updated.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/searches/<int:id>', methods=['DELETE'])
@decorators.authorize(['Pro'])
def restangular_searches_delete(id):

    def get_result_and_status():
        search = g.postgresql.query(
            models.search
        ).filter(
            models.search.id == id,
            models.search.user_id == g.user.ID,
        ).first()
        if not search:
            return 'Invalid Search', False
        g.postgresql.delete(search)
        g.postgresql.commit()
        return 'The selected search was sucessfully deleted.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/watchlists', methods=['GET'])
@decorators.authorize(['Pro'])
def restangular_watchlists_get():
    return jsonify({
        'output': [
            watchlist.to_dictionary()
            for watchlist in g.postgresql.query(
                models.watchlist,
            ).filter(
                models.watchlist.user_id == g.user.ID,
            ).order_by('id asc').all()
        ],
    })


@application.route('/restangular/watchlists', methods=['POST'])
@decorators.authorize(['Pro'])
def restangular_watchlists_post():

    def get_result_and_status():
        profile_id = request.json['profile_id']
        if g.postgresql.query(
            models.watchlist
        ).filter(
            models.watchlist.user_id == g.user.ID,
            models.watchlist.profile_id == profile_id,
        ).first():
            return '', True
        d = models.option.get_dictionary(g.mysql)
        if not d[
            'facebook_search_engine_watchlists'
        ] > g.postgresql.query(models.watchlist.user_id == g.user.ID).count():
            return 'You cannot watch more than %(count)s groups.' % {
                'count': d['facebook_search_engine_watchlists'],
            }, False
        g.postgresql.add(models.watchlist(**{
            'profile_id': profile_id,
            'user_id': g.user.ID,
        }))
        g.postgresql.commit()
        return 'The selected watchlist was sucessfully saved.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/watchlists/<int:id>', methods=['PUT'])
@decorators.authorize(['Pro'])
def restangular_watchlists_put(id):

    def get_result_and_status():
        watchlist = g.postgresql.query(
            models.watchlist
        ).filter(
            models.watchlist.id == id,
            models.watchlist.user_id == g.user.ID,
        ).first()
        if not watchlist:
            return 'Invalid Watchlist', False
        watchlist.contents = request.json['contents']
        g.postgresql.add(watchlist)
        g.postgresql.commit()
        return 'The selected watchlist was successfully updated.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/restangular/watchlists/<int:id>', methods=['DELETE'])
@decorators.authorize(['Pro'])
def restangular_watchlists_delete(id):

    def get_result_and_status():
        watchlist = g.postgresql.query(
            models.watchlist
        ).filter(
            models.watchlist.id == id,
            models.watchlist.user_id == g.user.ID,
        ).first()
        if not watchlist:
            return 'Invalid Watchlist', False
        g.postgresql.delete(watchlist)
        g.postgresql.commit()
        return 'The selected watchlist was successfully deleted.', True

    result, status = get_result_and_status()

    return jsonify({
        'result': result,
        'status': status,
    })


@application.route('/typeahead')
@decorators.authorize(['Free', 'Personal', 'Pro'])
def typeahead():

    def get_values():
        attribute = request.args.get('attribute', '')
        if not attribute in ['category', 'location']:
            return []
        query = request.args.get('query', '')
        if not query:
            return []
        if attribute == 'category':
            return g.postgresql.query(
                distinct(models.profile.categories_primary)
            ).filter(models.profile.categories_primary.ilike(
                '%%%(query)s%%' % {
                    'query': query,
                }
            ))[0:10]
        if attribute == 'location':
            return g.postgresql.query(
                distinct(models.profile.location)
            ).filter(models.profile.location.ilike(
                '%%%(query)s%%' % {
                    'query': query,
                }
            ))[0:10]
        return []

    return jsonify({
        'options': [{'value': value[0]} for value in get_values()],
    })


@application.route('/templates/<path:name>')
def templates(name):
    if not isfile(join(dirname(__file__), 'templates', name)):
        abort(404)
    return render_template(name)


@application.route('/403')
def error_403(error=None):
    return render_template('views/error_403.html'), 403


@application.route('/404')
@application.errorhandler(404)
def error_404(error=None):
    return render_template('views/error_404.html'), 404


@application.route('/500')
@application.errorhandler(500)
def error_500(error=None):
    return render_template('views/error_500.html'), 500


def get_profiles_and_pager(filter, order_by, limit, page):
    filter['category'] = filter['category'].strip()
    filter['location'] = filter['location'].strip()
    filter['likes_maximum'] = int(
        filter['likes_maximum']
    ) if filter['likes_maximum'] else 0
    filter['likes_minimum'] = int(
        filter['likes_minimum']
    ) if filter['likes_minimum'] else 0
    filter['discussions_maximum'] = float(
        filter['discussions_maximum']
    ) if filter['discussions_maximum'] else 0.00
    filter['discussions_minimum'] = float(
        filter['discussions_minimum']
    ) if filter['discussions_minimum'] else 0.00
    filter['name'] = filter['name'].strip()
    filter['profile_id'] = int(
        filter['profile_id']
    ) if filter['profile_id'] else 0
    query = g.postgresql.query(models.profile)
    if g.plan in ['Free']:
        page = 1
        filter['profile_id'] = 0
    if filter['category']:
        query = query.filter(models.profile.categories_primary.ilike(
            '%%%(category)s%%' % {
                'category': filter['category'],
            }
        ))
    if filter['location']:
        query = query.filter(
            models.profile.location.ilike('%%%(location)s%%' % {
                'location': filter['location'],
            })
        )
    if filter['likes_maximum']:
        query = query.filter(
            models.profile.numbers_likes <= filter['likes_maximum'],
        )
    if filter['likes_minimum']:
        query = query.filter(
            models.profile.numbers_likes >= filter['likes_minimum'],
        )
    if filter['discussions_maximum']:
        query = query.filter(
            models.profile.numbers_discussions_relative
            <=
            filter['discussions_maximum'],
        )
    if filter['discussions_minimum']:
        query = query.filter(
            models.profile.numbers_discussions_relative
            >=
            filter['discussions_minimum'],
        )
    if filter['name']:
        query = query.filter(models.profile.name.ilike('%%%(name)s%%' % {
            'name': filter['name'],
        }))
    profile = g.postgresql.query(
        models.profile,
    ).get(filter['profile_id']) if filter['profile_id'] else None
    if profile:
        query = query.filter(
            models.profile.id != profile.id,
            models.profile.description.op('~')(profile.get_keywords()),
            models.profile.location == profile.location,
        )
    pager = classes.pager(query.count(), limit, page)
    return query.order_by('%(column)s %(direction)s' % {
        'column':
        order_by['column']
        if order_by['column'] in [column[0] for column in columns]
        else 'id',
        'direction':
        order_by['direction']
        if order_by['direction'] in [direction[0] for direction in directions]
        else 'asc'
    })[pager.prefix:pager.suffix], pager

if __name__ == '__main__':
    application.run(port=5002, processes=10)

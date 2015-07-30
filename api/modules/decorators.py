# -*- coding: utf-8 -*-

from flask import g, render_template
from functools import wraps

from modules import log
from modules import timer


def authorize(plans):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not g.user or not g.plan in plans:
                return render_template('views/error_403.html')
            return function(*args, **kwargs)
        return decorated_function
    return decorator


def profile(indent):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            log.write(10, '%(function)s()' % {
                'function': function.__name__
            }, indent)
            timer.start(function.__name__)
            output = function(*args, **kwargs)
            timer.stop(function.__name__)
            log.write(10, '%(seconds).3f seconds' % {
                'seconds': timer.get_seconds(function.__name__),
            }, indent)
            return output
        return decorated_function
    return decorator

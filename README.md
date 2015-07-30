Install
=======

Step 1
------

```
$ cd petninja.co
$ git clone git@github.com:mahendrakalkura/petninja.co.git .
```

Step 2
------

```
$ cd petninja.co/api
$ mkvirtualenv petninja.co
$ pip install -r requirements.txt
$ deactivate
```

Step 3
------

```
$ cd petninja.co/api
$ npm install -g bower
$ npm install -g less
$ bower install
```

Step 4
------
```
$ cp api/variables.py.sample api/variables.py
$ cp www/wp-config-sample.php www/wp-config.php
$ cp www/wp-content/plugins/facebook-search-engine/others/variables-sample.php www/wp-content/plugins/facebook-search-engine/others/variables.php
```

Assets
======

```
$ cd petninja.co/api
$ workon petninja.co
$ python manager.py assets_
$ deactivate
```

Run
===

```
$ cd petninja.co/api
$ workon petninja.co
$ python server.py
$ deactivate
```

Others
======

crontab
-------

```
0 * * * * cd {{ path }} && {{ virtualenv }}/python manager.py profiles_and_profiles_discussions_and_profiles_likes
```

supervisor
----------

```
[program:petninja.co]
autorestart=true
autostart=true
command={{ virtualenv }}/celery worker --app=tasks --concurrency=50 --loglevel=WARNING --pool=processes
directory={{ path }}
group={{ group }}
user={{ user }}
```

# -*- coding: utf-8 -*-
"""
    tests.templating
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Template functionality

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import flask
import unittest
import logging
from jinja2 import TemplateNotFound




def test_context_processing():
    app = flask.Flask(__name__)
    @app.context_processor
    def context_processor():
        return {'injected_value': 42}
    @app.route('/')
    def index():
        return flask.render_template('context_template.html', value=23)
    rv = app.test_client().get('/')
    assert rv.data == b'<p>23|42'

def test_original_win():
    app = flask.Flask(__name__)
    @app.route('/')
    def index():
        return flask.render_template_string('{{ config }}', config=42)
    rv = app.test_client().get('/')
    assert rv.data == b'42'

def test_request_less_rendering():
    app = flask.Flask(__name__)
    app.config['WORLD_NAME'] = 'Special World'
    @app.context_processor
    def context_processor():
        return dict(foo=42)

    with app.app_context():
        rv = flask.render_template_string('Hello {{ config.WORLD_NAME }} '
                                          '{{ foo }}')
        assert rv == 'Hello Special World 42'

def test_standard_context():
    app = flask.Flask(__name__)
    app.secret_key = 'development key'
    @app.route('/')
    def index():
        flask.g.foo = 23
        flask.session['test'] = 'aha'
        return flask.render_template_string('''
            {{ request.args.foo }}
            {{ g.foo }}
            {{ config.DEBUG }}
            {{ session.test }}
        ''')
    rv = app.test_client().get('/?foo=42')
    assert rv.data.split() == [b'42', b'23', b'False', b'aha']

def test_escaping():
    text = '<p>Hello World!'
    app = flask.Flask(__name__)
    @app.route('/')
    def index():
        return flask.render_template('escaping_template.html', text=text,
                                     html=flask.Markup(text))
    lines = app.test_client().get('/').data.splitlines()
    assert lines == [
        b'&lt;p&gt;Hello World!',
        b'<p>Hello World!',
        b'<p>Hello World!',
        b'<p>Hello World!',
        b'&lt;p&gt;Hello World!',
        b'<p>Hello World!'
    ]

def test_no_escaping():
    app = flask.Flask(__name__)
    with app.test_request_context():
        assert flask.render_template_string(
            '{{ foo }}', foo='<test>') == '<test>'
        assert flask.render_template('mail.txt', foo='<test>') == \
            '<test> Mail'

def test_macros():
    app = flask.Flask(__name__)
    with app.test_request_context():
        macro = flask.get_template_attribute('_macro.html', 'hello')
        assert macro('World') == 'Hello World!'

def test_template_filter():
    app = flask.Flask(__name__)
    @app.template_filter()
    def my_reverse(s):
        return s[::-1]
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'

def test_add_template_filter():
    app = flask.Flask(__name__)
    def my_reverse(s):
        return s[::-1]
    app.add_template_filter(my_reverse)
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'

def test_template_filter_with_name():
    app = flask.Flask(__name__)
    @app.template_filter('strrev')
    def my_reverse(s):
        return s[::-1]
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'

def test_add_template_filter_with_name():
    app = flask.Flask(__name__)
    def my_reverse(s):
        return s[::-1]
    app.add_template_filter(my_reverse, 'strrev')
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'

def test_template_filter_with_template():
    app = flask.Flask(__name__)
    @app.template_filter()
    def super_reverse(s):
        return s[::-1]
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_add_template_filter_with_template():
    app = flask.Flask(__name__)
    def super_reverse(s):
        return s[::-1]
    app.add_template_filter(super_reverse)
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_template_filter_with_name_and_template():
    app = flask.Flask(__name__)
    @app.template_filter('super_reverse')
    def my_reverse(s):
        return s[::-1]
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_add_template_filter_with_name_and_template():
    app = flask.Flask(__name__)
    def my_reverse(s):
        return s[::-1]
    app.add_template_filter(my_reverse, 'super_reverse')
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_template_test():
    app = flask.Flask(__name__)
    @app.template_test()
    def boolean(value):
        return isinstance(value, bool)
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == boolean
    assert app.jinja_env.tests['boolean'](False)

def test_add_template_test():
    app = flask.Flask(__name__)
    def boolean(value):
        return isinstance(value, bool)
    app.add_template_test(boolean)
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == boolean
    assert app.jinja_env.tests['boolean'](False)

def test_template_test_with_name():
    app = flask.Flask(__name__)
    @app.template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)

def test_add_template_test_with_name():
    app = flask.Flask(__name__)
    def is_boolean(value):
        return isinstance(value, bool)
    app.add_template_test(is_boolean, 'boolean')
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)

def test_template_test_with_template():
    app = flask.Flask(__name__)
    @app.template_test()
    def boolean(value):
        return isinstance(value, bool)
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_add_template_test_with_template():
    app = flask.Flask(__name__)
    def boolean(value):
        return isinstance(value, bool)
    app.add_template_test(boolean)
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_template_test_with_name_and_template():
    app = flask.Flask(__name__)
    @app.template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_add_template_test_with_name_and_template():
    app = flask.Flask(__name__)
    def is_boolean(value):
        return isinstance(value, bool)
    app.add_template_test(is_boolean, 'boolean')
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_add_template_global():
    app = flask.Flask(__name__)
    @app.template_global()
    def get_stuff():
        return 42
    assert 'get_stuff' in app.jinja_env.globals.keys()
    assert app.jinja_env.globals['get_stuff'] == get_stuff
    assert app.jinja_env.globals['get_stuff'](), 42
    with app.app_context():
        rv = flask.render_template_string('{{ get_stuff() }}')
        assert rv == '42'

def test_custom_template_loader():
    class MyFlask(flask.Flask):
        def create_global_jinja_loader(self):
            from jinja2 import DictLoader
            return DictLoader({'index.html': 'Hello Custom World!'})
    app = MyFlask(__name__)
    @app.route('/')
    def index():
        return flask.render_template('index.html')
    c = app.test_client()
    rv = c.get('/')
    assert rv.data == b'Hello Custom World!'

def test_iterable_loader():
    app = flask.Flask(__name__)
    @app.context_processor
    def context_processor():
        return {'whiskey': 'Jameson'}
    @app.route('/')
    def index():
        return flask.render_template(
            ['no_template.xml', # should skip this one
            'simple_template.html', # should render this
            'context_template.html'],
            value=23)

    rv = app.test_client().get('/')
    assert rv.data == b'<h1>Jameson</h1>'

def test_templates_auto_reload():
    app = flask.Flask(__name__)
    assert app.config['TEMPLATES_AUTO_RELOAD']
    assert app.jinja_env.auto_reload
    app = flask.Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    assert not app.jinja_env.auto_reload

def test_template_loader_debugging(test_apps):
    from blueprintapp import app

    called = []
    class _TestHandler(logging.Handler):
        def handle(x, record):
            called.append(True)
            text = str(record.msg)
            assert '1: trying loader of application "blueprintapp"' in text
            assert ('2: trying loader of blueprint "admin" '
                    '(blueprintapp.apps.admin)') in text
            assert ('trying loader of blueprint "frontend" '
                    '(blueprintapp.apps.frontend)') in text
            assert 'Error: the template could not be found' in text
            assert ('looked up from an endpoint that belongs to '
                    'the blueprint "frontend"') in text
            assert 'See http://flask.pocoo.org/docs/blueprints/#templates' in text

    with app.test_client() as c:
        try:
            old_load_setting = app.config['EXPLAIN_TEMPLATE_LOADING']
            old_handlers = app.logger.handlers[:]
            app.logger.handlers = [_TestHandler()]
            app.config['EXPLAIN_TEMPLATE_LOADING'] = True

            with pytest.raises(TemplateNotFound) as excinfo:
                c.get('/missing')

            assert 'missing_template.html' in str(excinfo.value)
        finally:
            app.logger.handlers[:] = old_handlers
            app.config['EXPLAIN_TEMPLATE_LOADING'] = old_load_setting

    assert len(called) == 1

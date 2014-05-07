# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.routing import BaseConverter
from werkzeug.contrib.cache import MemcachedCache
from functools import wraps
import evernote_wrapper, string
from paginator import Paginator

app = Flask(__name__)

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    EVERNOTE_TOKEN='',
    SANDBOX=False,
    NOTEBOOK='',
    NOTEIMAGES='static/noteimages/',
    THUMBNAILS='static/thumbnails/',
    RECIPE_IMAGES=True,
))
app.config.from_envvar('VMENU_SETTINGS', silent=True)

# A helper to return a set of letters for the footer links.
def footer_links():
    return [['a - e', 'a'], ['f - j', 'f'], ['k - n', 'k'], ['o - r', 'o'], ['s - v', 's'], ['w - z', 'w']]
app.jinja_env.globals.update(footer_links=footer_links)

cache = MemcachedCache(['127.0.0.1:11211'])

def cached(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cache_key = request.path.replace(' ', '_')
        rv = cache.get(cache_key)
        if rv is not None:
            return rv
        rv = f(*args, **kwargs)
        cache.set(cache_key, rv, 3600)
        return rv
    return decorated_function

@app.route('/')
@app.route('/<regex("[a-zA-Z]{1}"):start>/')
@app.route('/<regex("-?[0-9]*"):page>/')
@app.route('/<regex("[a-zA-Z]{1}"):start>/<regex("-?[0-9]*"):page>/')
@cached
def show_tags(start='a', page=0):
    tags = evernote_wrapper.get_tags()
    paginator = Paginator(tags, 'name', start, int(page), 6)
    start += '/'
    return render_template('tags.html', tags=paginator.page(), tagurl='/', start=start, page=int(page))

@app.route('/tag/<tag>/')
@app.route('/tag/<tag>/<regex("[a-zA-Z]{1}"):start>/')
@app.route('/tag/<tag>/<regex("[0-9]*"):page>/')
@app.route('/tag/<tag>/<regex("[a-zA-Z]{1}"):start>/<regex("-?[0-9]*"):page>/')
@cached
def show_recipes(tag, start='a', page=0):
    recipes = evernote_wrapper.get_recipes(tag)
    print "%s recipes" % len(recipes)
    paginator = Paginator(recipes, 'title', start, int(page), 6)
    tagurl = '/tag/%s/' % tag
    start += '/'
    return render_template('recipes.html', recipes=paginator.page(), tagurl=tagurl, start=start, page=int(page))

@app.route('/recipe/<recipe>/')
@cached
def show_recipe(recipe):
    recipe = evernote_wrapper.get_recipe(recipe)
    return render_template('recipe.html', recipe=recipe)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

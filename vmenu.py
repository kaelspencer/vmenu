# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.routing import BaseConverter
from functools import wraps
import evernote_wrapper, string, logging, urllib, urllib2
from paginator import Paginator
from trace import trace
from tasks import make_celery

app = Flask(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s', level=logging.DEBUG)

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
    RECIPE_IMAGES=False,
    CACHE_PREFIX='vmenu:', # Intentionally not including this in the default config file, since no one really needs to change it. They can, but why?
    CELERY_BROKER_URL='amqp://',
    CELERY_RESULT_BACKEND='amqp://',
))
app.config.from_envvar('VMENU_SETTINGS', silent=True)

celery = make_celery(app)

def logrequest(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logging.info(request.path)
        return trace(f, *args, **kwargs)
    return decorated_function

# A helper to return a set of letters for the footer links.
def footer_links():
    return [['a - e', 'a'], ['f - j', 'f'], ['k - n', 'k'], ['o - r', 'o'], ['s - v', 's'], ['w - z', 'w']]
app.jinja_env.globals.update(footer_links=footer_links)

# Download a file via authed HTTP post. This should be in evernote_wrapper.py but I'm having trouble with the celery object.
@celery.task(ignore_result=True, name="vmenu.download_file")
def download_file(url, path):
    # First, see if the file already exists.
    print 'Retrieved %s' % url
    try:
        f = open(path, "r")
        return
    except:
        pass

    logging.info('Fetching file from Evernote: %s', url)
    body = {'auth': app.config['EVERNOTE_TOKEN']}
    header = {'Content-type': 'application/x-www-form-urlencoded'}
    request = urllib2.Request(url, urllib.urlencode(body), header)
    response = urllib2.urlopen(request)

    f = open(path, "w+")
    f.write(response.read())
    f.close()
    logging.info('Finished fetching file from Evernote: %s', url)

@app.route('/')
@app.route('/<regex("[a-zA-Z]{1}"):start>/')
@app.route('/<regex("-?[0-9]*"):page>/')
@app.route('/<regex("[a-zA-Z]{1}"):start>/<regex("-?[0-9]*"):page>/')
@logrequest
def show_tags(start='a', page=0):
    tags = evernote_wrapper.get_tags()
    paginator = Paginator(tags, 'name', start, int(page), 6)
    start += '/'
    return render_template('tags.html', tags=paginator.page(), tagurl='/', start=start, page=int(page))

@app.route('/tag/<tag>/')
@app.route('/tag/<tag>/<regex("[a-zA-Z]{1}"):start>/')
@app.route('/tag/<tag>/<regex("[0-9]*"):page>/')
@app.route('/tag/<tag>/<regex("[a-zA-Z]{1}"):start>/<regex("-?[0-9]*"):page>/')
@logrequest
def show_recipes(tag, start='a', page=0):
    recipes = evernote_wrapper.get_recipes(tag)
    logging.info('%s recipes', len(recipes))
    paginator = Paginator(recipes, 'title', start, int(page), 6)
    tagurl = '/tag/%s/' % tag
    start += '/'
    return render_template('recipes.html', recipes=paginator.page(), tagurl=tagurl, start=start, page=int(page))

@app.route('/recipe/<recipe>/')
@logrequest
def show_recipe(recipe):
    recipe = evernote_wrapper.get_recipe(recipe)
    return render_template('recipe.html', recipe=recipe)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

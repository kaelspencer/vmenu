# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.routing import BaseConverter
import evernote_wrapper

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
))
app.config.from_envvar('VMENU_SETTINGS', silent=True)

@app.route('/')
def show_tags():
    tags = evernote_wrapper.get_tags()
    return render_template('tags.html', tags=tags)

@app.route('/tag/<tag>/')
@app.route('/tag/<tag>/<regex("[a-zA-Z]{1}"):start>/')
def show_recipes(tag, start='a'):
    recipes = evernote_wrapper.get_recipes(tag)
    return render_template('recipes.html', recipes=recipes, start=start.lower())

@app.route('/recipe/<recipe>/')
def show_recipe(recipe):
    recipe = evernote_wrapper.get_recipe(recipe)
    return render_template('recipe.html', recipe=recipe)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

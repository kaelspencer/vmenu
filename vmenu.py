# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import evernote_wrapper

app = Flask(__name__)

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
def show_recipes(tag):
    recipes = evernote_wrapper.get_recipes(tag)
    return render_template('recipes.html', recipes=recipes)

@app.route('/recipe/<recipe>/')
def show_recipe(recipe):
    recipe = evernote_wrapper.get_recipe(recipe)
    return render_template('recipe.html', recipe=recipe)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

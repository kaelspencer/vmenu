# vmenu
vmenu is a recipe browser backed by Evernote designed to be used on the [Visionect V-Tablet](http://www.visionect.com/)

# Installation
You should really consider installing vmenu in virtualenv. Clone the [repository](https://github.com/kaelspencer/vmenu), create an environment, and install the requirements.

    git clone https://github.com/kaelspencer/vmenu.git
    cd vmenu
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

## Configuration
Copy `config.cfg` to `debug.cfg` (or edit in place, just don't check it in!). The values should be fairly self explanatory. Get your token from from Evernote. If you want to use the sandbox server be sure to set `SANDBOX=True`. After you have configured it, run `export VMENU_SETTINGS=debug.cfg`. This tells vmenu to load that file to update settings.

## Static Files
Thumbnails and images in the recipes are downloaded and saved locally. These locations are referenced in the config file. vmenu needs to be able to write to them. When in production, the web server should be the one to server up these static files. The path in the config file will be used as a base in HTML to reference the images.

## Caching
If you have a big Evernote recipe book, using memcached is an absolute necessity. vmenu fetches notes through the regular API and does not use the full synchronization option. This can be very slow! Especially the fetching of the thumbnails. I'm trying to do some tricky things with memcached, so install it. Seriously.

## Task Queue
Celery is used so you'll need to install some kind of message broker. I'm using RabbitMQ and the default config settings point to this. Update `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` appropriately.

from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from werkzeug.contrib.cache import MemcachedCache
from trace import trace, tracen
import binascii, re, urllib, urllib2, logging, vmenu

cache = MemcachedCache(['127.0.0.1:11211'])

# Get all of the tags used in the default notebook.
def get_tags():
    key = vmenu.app.config['CACHE_PREFIX'] + 'tags'
    tags = cache.get(key)

    if tags is None:
        logging.info('Cache miss for %s', key)
        client = trace(get_client)
        notestore = trace(client.get_note_store)
        notebook = trace(get_notebook, notestore, vmenu.app.config['NOTEBOOK'])
        tags = tracen('listTagsByNotebook', notestore.listTagsByNotebook, notebook.guid)

        tags = sorted(tags, key = lambda Tag: Tag.name)
        cache.set(key, tags)

    return tags

# Get all of the notes that are tagged with the provided tag in the default notebook.
# Tag is a guid.
def get_recipes(tag):
    key = vmenu.app.config['CACHE_PREFIX'] + 'recipes-' + tag
    results = cache.get(key)

    if results is None:
        logging.info('Cache miss for %s', key)
        client = trace(get_client)
        notestore = trace(client.get_note_store)
        notebook = trace(get_notebook, notestore, vmenu.app.config['NOTEBOOK'])

        tag_guids = [tag]
        filter = NoteFilter(notebookGuid=notebook.guid, tagGuids=tag_guids)
        offset = 0
        max_notes = 500
        result_spec = NotesMetadataResultSpec(includeTitle=True)
        notes_result = trace(notestore.findNotesMetadata, filter, offset, max_notes, result_spec)
        notes = sorted(notes_result.notes, key = lambda NoteMetadata: NoteMetadata.title)
        results = []

        def process_notes():
            for n in notes:
                result = {
                    'guid': n.guid,
                    'title': n.title,
                    'thumbnail': trace(get_thumbnail, n.guid)
                }
                results.append(result)
        trace(process_notes)

        cache.set(key, results);

    return results

# Get the recipe. The parameter is a guid.
def get_recipe(recipe):
    client = trace(get_client)
    notestore = trace(client.get_note_store)

    # Get the note metadata without a body or resources. This result contains
    # the body hash used for caching.
    partial = trace(notestore.getNote, recipe, False, False, False, False)

    # Check the cache for this note.
    key = '%s%s_%s' % (vmenu.app.config['CACHE_PREFIX'], binascii.hexlify(partial.contentHash), vmenu.app.config['RECIPE_IMAGES'])
    content = cache.get(key)
    if content is None:
        logging.info('Cache miss for %s', key)
        full = trace(notestore.getNote, recipe, True, False, False, False)
        content = strip_tags(full.content.decode('utf-8'))

        def process():
            if full.resources is not None and vmenu.app.config['RECIPE_IMAGES']:
                for resource in full.resources:
                    content = trace(update_resource, content, resource)
        trace(process)

        # Cache the content. The key is the MD5 hash of the server stored content
        # but the stored value in this cache has stripped out tags.
        cache.set(key, content)

    return { "content": content }

def get_notebook(notestore, name):
    for notebook in trace(notestore.listNotebooks):
        if notebook.name == name:
            return notebook
    raise LookupError

# Get the client. This is wrapped in a helper because it probably should
# be cached in the future.
def get_client():
    # TODO: Caching?
    return EvernoteClient(token=vmenu.app.config['EVERNOTE_TOKEN'], sandbox=vmenu.app.config['SANDBOX'])

# Remove a few of the Evernote specific tags that aren't meaningful.
def strip_tags(content):
    start = '''<\?xml version="1.0" encoding="UTF-8"\?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>'''
    end = '</en-note>'

    content = re.sub(start, '', content);
    return re.sub(end, '', content);

# Replace the content's resource with an img tag pointing to the dowloaded
# resource.
def update_resource(content, resource):
    posturl = "%s/res/%s" % (get_url_prefix(), resource.guid)
    path = vmenu.app.config["NOTEIMAGES"] + resource.guid
    download_file(posturl, path)
    hash = binascii.hexlify(resource.data.bodyHash)
    return re.sub(r'(<en-media hash="' + hash + '.*</en-media>)', '<img src="/' + path + '" />', content, flags=re.DOTALL)

# Retrieve the thumbnail. It may already be cached.
def get_thumbnail(guid):
    posturl = "%s/thm/note/%s.jpg" % (get_url_prefix(), guid)
    path = vmenu.app.config["THUMBNAILS"] + guid + '.jpg'
    download_file(posturl, path)
    return '/' + path

# Get the URL prefix.
def get_url_prefix():
    user_store = get_client().get_user_store()
    username = user_store.getUser().username
    user_info = user_store.getPublicUserInfo(username)
    return user_info.webApiUrlPrefix

# Download a file via authed HTTP post.
def download_file(url, path):
    # First, see if the file already exists.
    try:
        f = open(path, "r")
        return
    except:
        pass

    logging.info('Fetching file from Evernote: %s', url)
    body = {'auth': vmenu.app.config['EVERNOTE_TOKEN']}
    header = {'Content-type': 'application/x-www-form-urlencoded'}
    request = urllib2.Request(url, urllib.urlencode(body), header)
    response = urllib2.urlopen(request)

    f = open(path, "w+")
    f.write(response.read())
    f.close()
    logging.info('Finished fetching file from Evernote: %s', url)

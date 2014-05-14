from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from werkzeug.contrib.cache import MemcachedCache
from trace import trace, tracen
import binascii, re, logging, vmenu

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
            url_prefix = trace(get_url_prefix)
            for n in notes:
                result = {
                    'guid': n.guid,
                    'title': n.title,
                    'thumbnail': trace(get_thumbnail, url_prefix, n.guid)
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
            url_prefix = trace(get_url_prefix)
            if full.resources is not None and vmenu.app.config['RECIPE_IMAGES']:
                for resource in full.resources:
                    content = trace(update_resource, url_prefix, content, resource)
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
def update_resource(url_prefix, content, resource):
    posturl = "%s/res/%s" % (url_prefix, resource.guid)
    path = vmenu.app.config["NOTEIMAGES"] + resource.guid
    vmenu.download_file.delay(posturl, path)
    hash = binascii.hexlify(resource.data.bodyHash)
    return re.sub(r'(<en-media hash="' + hash + '.*</en-media>)', '<img src="/' + path + '" />', content, flags=re.DOTALL)

# Retrieve the thumbnail. It may already be cached.
def get_thumbnail(url_prefix, guid):
    posturl = "%s/thm/note/%s.jpg" % (url_prefix, guid)
    path = vmenu.app.config["THUMBNAILS"] + guid + '.jpg'
    vmenu.download_file.delay(posturl, path)
    return '/' + path

# Get the URL prefix.
def get_url_prefix():
    key = vmenu.app.config['CACHE_PREFIX'] + 'url_prefix'
    url_prefix = cache.get(key)

    if url_prefix is None:
        logging.info('Cache miss for %s', key)

        user_store = get_client().get_user_store()
        user_info = user_store.getPublicUserInfo(user_store.getUser().username)
        url_prefix = user_info.webApiUrlPrefix

        cache.set(key, url_prefix, timeout=60 * 60);

    return url_prefix

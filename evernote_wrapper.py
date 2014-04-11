from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import binascii, re, urllib, urllib2
from vmenu import app

# Get all of the tags used in the default notebook.
def get_tags():
    notestore = get_client().get_note_store()
    notebook = get_notebook(notestore, app.config['NOTEBOOK'])
    tags = notestore.listTagsByNotebook(notebook.guid)
    return tags

# Get all of the notes that are tagged with the provided tag in the default notebook.
# Tag is a guid.
def get_recipes(tag):
    notestore = get_client().get_note_store()
    notebook = get_notebook(notestore, app.config['NOTEBOOK'])

    tag_guids = [tag]
    filter = NoteFilter(notebookGuid=notebook.guid, tagGuids=tag_guids)
    offset = 0
    max_notes = 10
    result_spec = NotesMetadataResultSpec(includeTitle=True)
    notes_result = notestore.findNotesMetadata(filter, offset, max_notes, result_spec)
    notes = notes_result.notes
    results = []

    for n in notes:
        note = notestore.getNote(n.guid, False, False, False, False)
        result = {
            'guid': note.guid,
            'title': note.title,
            'thumbnail': get_thumbnail(n.guid)
        }
        results.append(result)

    return results

# Get the recipe. The parameter is a guid.
def get_recipe(recipe):
    notestore = get_client().get_note_store()
    full = notestore.getNote(recipe, True, False, False, False)
    content = strip_tags(full.content.decode('utf-8'))

    if full.resources is not None:
        for resource in full.resources:
            content = update_resource(content, resource)

    return { "content": content }

def get_notebook(notestore, name):
    for notebook in notestore.listNotebooks():
        if notebook.name == name:
            return notebook
    raise LookupError

# Get the client. This is wrapped in a helper because it probably should
# be cached in the future.
def get_client():
    # TODO: Caching?
    return EvernoteClient(token=app.config['EVERNOTE_TOKEN'])

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
    path = app.config["NOTEIMAGES"] + resource.guid
    download_file(posturl, path)
    hash = binascii.hexlify(resource.data.bodyHash)
    return re.sub(r'(<en-media hash="' + hash + '.*</en-media>)', '<img src="/' + path + '" />', content, flags=re.DOTALL)

# Retrieve the thumbnail. It may already be cached.
def get_thumbnail(guid):
    posturl = "%s/thm/note/%s.jpg" % (get_url_prefix(), guid)
    path = app.config["THUMBNAILS"] + guid + '.jpg'
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

    body = {'auth': app.config['EVERNOTE_TOKEN']}
    header = {'Content-type': 'application/x-www-form-urlencoded'}
    request = urllib2.Request(url, urllib.urlencode(body), header)
    response = urllib2.urlopen(request)

    f = open(path, "w+")
    f.write(response.read())
    f.close()

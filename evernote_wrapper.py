from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import binascii
import re
from vmenu import app

# Get all of the tags used in the default notebook.
def get_tags():
    notestore = get_notestore()
    notebook = get_notebook(get_notestore(), app.config['NOTEBOOK'])
    tags = notestore.listTagsByNotebook(notebook.guid)
    return tags

# Get all of the notes that are tagged with the provided tag in the default notebook.
# Tag is a guid.
def get_recipes(tag):
    notestore = get_notestore()
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
        results.append(notestore.getNote(n.guid, False, False, False, False))

    return results

# Get the recipe. The parameter is a guid.
def get_recipe(recipe):
    notestore = get_notestore()
    full = notestore.getNote(recipe, True, False, False, False)
    content = strip_tags(full.content.decode('utf-8'))

    for resource in full.resources:
        content = update_resource(content, resource)

    return { "content": content }

def get_notebook(notestore, name):
    for notebook in notestore.listNotebooks():
        if notebook.name == name:
            return notebook
    raise LookupError

def get_notestore():
    # TODO: Caching?
    client = EvernoteClient(token=app.config['EVERNOTE_TOKEN'])
    return client.get_note_store()

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
    imageurl = app.config["NOTEIMAGES"] + resource.guid
    download_file(resource.guid, imageurl)
    hash = binascii.hexlify(resource.data.bodyHash)
    return re.sub(r'(<en-media hash="' + hash + '.*</en-media>)', '<img src="/' + imageurl + '" />', content, flags=re.DOTALL)

# Download a resource with the given guid. If it already exists do nothing.
def download_file(guid, path):
    # First, see if the file already exists.
    try:
        f = open(path, "r")
        return
    except:
        pass

    # Download and save the file.
    notestore = get_notestore()
    resource = notestore.getResource(guid, True, False, True, False)
    f = open(path, "w+")
    f.write(resource.data.body)
    f.close()

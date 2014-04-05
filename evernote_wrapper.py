from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
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
    return { "content": full.content.decode('utf-8') }

def get_notebook(notestore, name):
    for notebook in notestore.listNotebooks():
        if notebook.name == name:
            return notebook
    raise LookupError

def get_notestore():
    # TODO: Caching?
    client = EvernoteClient(token=app.config['EVERNOTE_TOKEN'])
    return client.get_note_store()

"""File picker dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_file_picker_dialog(parent, repo):
    """Show a searchable file picker dialog listing all tracked files.

    Args:
        parent: Parent dialog
        repo: Git repository object

    Returns:
        Selected file path, or None if cancelled.
    """
    dialog = Gtk.Dialog(
        title='Pick File',
        transient_for=parent,
        modal=True,
    )
    dialog.set_default_size(500, 400)
    dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)

    content = dialog.get_content_area()
    content.set_margin_start(8)
    content.set_margin_end(8)
    content.set_margin_top(8)
    content.set_margin_bottom(8)
    content.set_spacing(4)

    search_entry = Gtk.SearchEntry()
    search_entry.set_placeholder_text('Search files...')
    content.pack_start(search_entry, False, False, 0)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_vexpand(True)
    scrolled.set_hexpand(True)
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    # Populate file list
    try:
        tracked_files = repo.git.ls_files().splitlines()
    except Exception:
        tracked_files = []

    store = Gtk.ListStore(str)
    for f in sorted(tracked_files):
        store.append([f])

    filter_model = store.filter_new()

    def visible_func(model, iter_, data):
        query = search_entry.get_text().lower()
        if not query:
            return True
        return query in model.get_value(iter_, 0).lower()

    filter_model.set_visible_func(visible_func)

    tree_view = Gtk.TreeView(model=filter_model)
    tree_view.set_headers_visible(False)

    renderer = Gtk.CellRendererText()
    renderer.set_property('family', 'monospace')
    col = Gtk.TreeViewColumn('File', renderer, text=0)
    tree_view.append_column(col)

    scrolled.add(tree_view)
    content.pack_start(scrolled, True, True, 0)

    selected_file = [None]

    def on_search_changed(entry):
        filter_model.refilter()

    def on_row_activated(tv, path, column):
        iter_ = filter_model.get_iter(path)
        if iter_:
            selected_file[0] = filter_model.get_value(iter_, 0)
            dialog.response(Gtk.ResponseType.OK)

    search_entry.connect('search-changed', on_search_changed)
    tree_view.connect('row-activated', on_row_activated)

    dialog.show_all()
    response = dialog.run()

    if response == Gtk.ResponseType.OK and selected_file[0]:
        result = selected_file[0]
    else:
        # Check if a row is selected (user might have pressed Enter via search)
        selection = tree_view.get_selection()
        model, iter_ = selection.get_selected()
        if response == Gtk.ResponseType.OK and iter_:
            result = model.get_value(iter_, 0)
        else:
            result = None

    dialog.destroy()
    return result

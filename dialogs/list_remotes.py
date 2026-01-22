"""List remotes dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig


def show_list_remotes_dialog(parent, repo):
    """Show dialog listing all remotes.

    Args:
        parent: Parent window
        repo: Git repository object
    """
    remotes = gitops.get_remotes_with_urls(repo)

    dialog = Gtk.Dialog(
        title='Remotes',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, 200)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    if not remotes:
        label = Gtk.Label(label='No remotes configured.')
        content.pack_start(label, True, True, 0)
    else:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Create list store: name, url
        store = Gtk.ListStore(str, str)
        for name, url in remotes.items():
            store.append([name, url])

        tree_view = Gtk.TreeView(model=store)
        tree_view.set_headers_visible(True)

        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn('Name', name_renderer, text=0)
        name_column.set_min_width(100)
        tree_view.append_column(name_column)

        url_renderer = Gtk.CellRendererText()
        url_column = Gtk.TreeViewColumn('URL', url_renderer, text=1)
        url_column.set_expand(True)
        tree_view.append_column(url_column)

        scrolled.add(tree_view)
        content.pack_start(scrolled, True, True, 0)

    dialog.show_all()
    dialog.run()
    dialog.destroy()

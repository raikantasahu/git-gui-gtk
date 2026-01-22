"""Open repository dialog for Git GUI GTK."""

import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_open_repository_dialog(parent, current_repo_path=None):
    """Show dialog to open a repository.

    Args:
        parent: Parent window
        current_repo_path: Current repository path for initial folder (optional)

    Returns:
        Selected folder path or None if cancelled
    """
    dialog = Gtk.FileChooserDialog(
        title='Open Git Repository',
        parent=parent,
        action=Gtk.FileChooserAction.SELECT_FOLDER
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )

    # Set initial folder
    if current_repo_path:
        dialog.set_current_folder(current_repo_path)
    else:
        dialog.set_current_folder(os.path.expanduser('~'))

    response = dialog.run()
    selected_path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
    dialog.destroy()

    return selected_path

"""Open With dialog using the system app chooser."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


def show_open_file_with_dialog(parent, file_path):
    """Show the system app chooser dialog for a file and launch the chosen app.

    Args:
        parent: Parent Gtk.Window for the dialog.
        file_path: Absolute path to the file to open.
    """
    gio_file = Gio.File.new_for_path(file_path)

    dialog = Gtk.AppChooserDialog.new(
        parent,
        Gtk.DialogFlags.MODAL,
        gio_file
    )
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        app_info = dialog.get_app_info()
        if app_info:
            try:
                app_info.launch([gio_file], None)
            except Exception:
                pass
    dialog.destroy()

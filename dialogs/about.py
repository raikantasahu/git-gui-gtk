"""About dialog for Git GUI GTK."""

import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

# Get the icon path relative to this file
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICON_PATH = os.path.join(_APP_DIR, 'icons', 'git-gui-gtk.svg')


def show_about_dialog(parent):
    """Show the about dialog.

    Args:
        parent: Parent window
    """
    about = Gtk.AboutDialog(
        transient_for=parent,
        modal=True,
        program_name='Git GUI GTK',
        version='1.0.0',
        comments='A GTK3 replacement for git-gui',
        website='https://github.com/raikantasahu/git-gui-gtk',
        copyright='© 2026 Raikanta Sahu',
        license_type=Gtk.License.MIT_X11
    )

    # Set logo from icon file
    if os.path.exists(_ICON_PATH):
        try:
            logo = GdkPixbuf.Pixbuf.new_from_file_at_size(_ICON_PATH, 64, 64)
            about.set_logo(logo)
        except Exception:
            pass

    about.run()
    about.destroy()

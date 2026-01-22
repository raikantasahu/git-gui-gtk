"""About dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


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
        license_type=Gtk.License.GPL_3_0
    )
    about.run()
    about.destroy()

"""GTK Application class for Git GUI."""

import os

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib, GdkPixbuf

from window import GitGuiWindow
from actions import setup_app_actions, setup_window_actions

# Get the icon path relative to this file
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_ICON_PATH = os.path.join(_APP_DIR, 'icons', 'git-gui-gtk.svg')


class GitGuiApplication(Gtk.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id='com.github.raikanta.GitGuiGtk',
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE
        )
        self.window = None
        self.repo_path = None

    def do_startup(self):
        """Called when application starts."""
        Gtk.Application.do_startup(self)
        setup_app_actions(self)

        # Set default icon for all windows
        if os.path.exists(_ICON_PATH):
            Gtk.Window.set_default_icon_from_file(_ICON_PATH)

    def do_activate(self):
        """Called when application is activated."""
        if not self.window:
            self.window = GitGuiWindow(application=self)
            self.window.set_wmclass('gitguigtk', 'Git GUI GTK')
            setup_window_actions(self, self.window)
        self.window.present()

    def do_open(self, files, n_files, hint):
        """Called when opening files/directories."""
        if n_files > 0:
            self.repo_path = files[0].get_path()
        self.do_activate()
        if self.repo_path and self.window:
            self.window.open_repository(self.repo_path)

    def quit(self):
        """Quit the application."""
        super().quit()

    def _show_about_from_action(self):
        """Show about dialog (called from action)."""
        about = Gtk.AboutDialog(
            transient_for=self.window,
            modal=True,
            program_name='Git GUI GTK',
            version='1.0.0',
            website='https://github.com/raikantasahu/git-gui-gtk',
            copyright='© 2026 Raikanta Sahu',
            license_type=Gtk.License.MIT_X11,
            comments='A modern GTK3 replacement for git-gui'
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

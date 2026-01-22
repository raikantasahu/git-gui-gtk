"""GTK Application class for Git GUI."""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib

from window import GitGuiWindow
from actions import setup_app_actions, setup_window_actions


class GitGuiApplication(Gtk.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id='org.gnome.GitGuiGtk',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.window = None
        self.repo_path = None

    def do_startup(self):
        """Called when application starts."""
        Gtk.Application.do_startup(self)
        setup_app_actions(self)

    def do_activate(self):
        """Called when application is activated."""
        if not self.window:
            self.window = GitGuiWindow(application=self)
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
            website='https://github.com/git-gui-gtk',
            copyright='© 2024 Git GUI GTK Contributors',
            license_type=Gtk.License.GPL_3_0,
            comments='A modern GTK3 replacement for git-gui'
        )
        about.run()
        about.destroy()

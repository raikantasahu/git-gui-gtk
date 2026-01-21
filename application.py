"""GTK Application class for Git GUI."""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib

from window import GitGuiWindow


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
        self._setup_actions()

    def do_activate(self):
        """Called when application is activated."""
        if not self.window:
            self.window = GitGuiWindow(application=self)
        self.window.present()

    def do_open(self, files, n_files, hint):
        """Called when opening files/directories."""
        if n_files > 0:
            self.repo_path = files[0].get_path()
        self.do_activate()
        if self.repo_path and self.window:
            self.window.open_repository(self.repo_path)

    def _setup_actions(self):
        """Set up application actions."""
        # Quit action
        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self._on_quit)
        self.add_action(quit_action)
        self.set_accels_for_action('app.quit', ['<Ctrl>q'])

        # Open repository action
        open_action = Gio.SimpleAction.new('open', None)
        open_action.connect('activate', self._on_open)
        self.add_action(open_action)
        self.set_accels_for_action('app.open', ['<Ctrl>o'])

        # Rescan action
        rescan_action = Gio.SimpleAction.new('rescan', None)
        rescan_action.connect('activate', self._on_rescan)
        self.add_action(rescan_action)
        self.set_accels_for_action('app.rescan', ['<Ctrl>r', 'F5'])

        # Commit action
        commit_action = Gio.SimpleAction.new('commit', None)
        commit_action.connect('activate', self._on_commit)
        self.add_action(commit_action)
        self.set_accels_for_action('app.commit', ['<Ctrl>Return'])

        # Push action
        push_action = Gio.SimpleAction.new('push', None)
        push_action.connect('activate', self._on_push)
        self.add_action(push_action)
        self.set_accels_for_action('app.push', ['<Ctrl>p'])

        # Pull action
        pull_action = Gio.SimpleAction.new('pull', None)
        pull_action.connect('activate', self._on_pull)
        self.add_action(pull_action)

        # Fetch action
        fetch_action = Gio.SimpleAction.new('fetch', None)
        fetch_action.connect('activate', self._on_fetch)
        self.add_action(fetch_action)

        # Stage all action
        stage_all_action = Gio.SimpleAction.new('stage-all', None)
        stage_all_action.connect('activate', self._on_stage_all)
        self.add_action(stage_all_action)
        self.set_accels_for_action('app.stage-all', ['<Ctrl><Shift>a'])

        # Unstage all action
        unstage_all_action = Gio.SimpleAction.new('unstage-all', None)
        unstage_all_action.connect('activate', self._on_unstage_all)
        self.add_action(unstage_all_action)

        # Amend action
        amend_action = Gio.SimpleAction.new('amend', None)
        amend_action.connect('activate', self._on_amend)
        self.add_action(amend_action)

        # About action
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self._on_about)
        self.add_action(about_action)

    def _on_quit(self, action, param):
        """Handle quit action."""
        self.quit()

    def _on_open(self, action, param):
        """Handle open repository action."""
        if self.window:
            self.window.show_open_dialog()

    def _on_rescan(self, action, param):
        """Handle rescan action."""
        if self.window:
            self.window.rescan()

    def _on_commit(self, action, param):
        """Handle commit action."""
        if self.window:
            self.window.do_commit()

    def _on_push(self, action, param):
        """Handle push action."""
        if self.window:
            self.window.do_push()

    def _on_pull(self, action, param):
        """Handle pull action."""
        if self.window:
            self.window.do_pull()

    def _on_fetch(self, action, param):
        """Handle fetch action."""
        if self.window:
            self.window.do_fetch()

    def _on_stage_all(self, action, param):
        """Handle stage all action."""
        if self.window:
            self.window.stage_all()

    def _on_unstage_all(self, action, param):
        """Handle unstage all action."""
        if self.window:
            self.window.unstage_all()

    def _on_amend(self, action, param):
        """Handle amend action."""
        if self.window:
            self.window.toggle_amend()

    def _on_about(self, action, param):
        """Show about dialog."""
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

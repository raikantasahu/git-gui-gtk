"""Main application window."""

import os

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib

from git_operations import GitOperations, FileChange
from widgets import FileListWidget, DiffView, CommitArea


class GitGuiWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title('Git GUI')
        self.set_default_size(1200, 800)

        self._git = GitOperations()
        self._current_file = None

        self._setup_ui()
        self._setup_menu()

        # Try to open current directory as repo
        cwd = os.getcwd()
        self.open_repository(cwd)

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # Menu bar
        menubar = self._create_menubar()
        main_box.pack_start(menubar, False, False, 0)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(4)
        toolbar.set_margin_bottom(4)

        # Open button
        open_button = Gtk.Button()
        open_icon = Gtk.Image.new_from_icon_name('folder-open-symbolic', Gtk.IconSize.BUTTON)
        open_button.add(open_icon)
        open_button.set_tooltip_text('Open Repository (Ctrl+O)')
        open_button.connect('clicked', lambda b: self.show_open_dialog())
        toolbar.pack_start(open_button, False, False, 0)

        # Rescan button
        rescan_button = Gtk.Button()
        rescan_icon = Gtk.Image.new_from_icon_name('view-refresh-symbolic', Gtk.IconSize.BUTTON)
        rescan_button.add(rescan_icon)
        rescan_button.set_tooltip_text('Rescan (F5)')
        rescan_button.connect('clicked', lambda b: self.rescan())
        toolbar.pack_start(rescan_button, False, False, 0)

        toolbar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)

        # Branch indicator
        branch_icon = Gtk.Image.new_from_icon_name('emblem-symbolic-link', Gtk.IconSize.BUTTON)
        toolbar.pack_start(branch_icon, False, False, 0)
        self._branch_label = Gtk.Label()
        toolbar.pack_start(self._branch_label, False, False, 0)

        main_box.pack_start(toolbar, False, False, 0)
        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # Main horizontal paned: file lists on left, diff+commit on right
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_vexpand(True)

        # Left side: file lists (full vertical space)
        file_lists_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        file_lists_box.set_size_request(280, -1)

        # Unstaged changes
        self._unstaged_list = FileListWidget(title='Unstaged Changes', staged=False)
        self._unstaged_list.set_vexpand(True)
        self._unstaged_list.connect('file-selected', self._on_unstaged_file_selected)
        self._unstaged_list.connect('file-activated', self._on_unstaged_file_activated)
        file_lists_box.pack_start(self._unstaged_list, True, True, 0)

        # Separator
        file_lists_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # Staged changes
        self._staged_list = FileListWidget(title='Staged Changes', staged=True)
        self._staged_list.set_vexpand(True)
        self._staged_list.connect('file-selected', self._on_staged_file_selected)
        self._staged_list.connect('file-activated', self._on_staged_file_activated)
        file_lists_box.pack_start(self._staged_list, True, True, 0)

        main_paned.pack1(file_lists_box, resize=False, shrink=False)

        # Right side: diff view and commit area stacked vertically
        right_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        right_paned.set_hexpand(True)

        # Diff view (top)
        self._diff_view = DiffView()
        self._diff_view.set_vexpand(True)
        right_paned.pack1(self._diff_view, resize=True, shrink=False)

        # Commit area (bottom)
        self._commit_area = CommitArea()
        self._commit_area.set_size_request(-1, 180)
        self._commit_area.connect('commit-requested', self._on_commit_requested)
        self._commit_area.connect('push-requested', lambda w: self.do_push())
        self._commit_area.connect('pull-requested', lambda w: self.do_pull())
        self._commit_area.connect('rescan-requested', lambda w: self.rescan())
        right_paned.pack2(self._commit_area, resize=False, shrink=False)

        main_paned.pack2(right_paned, resize=True, shrink=False)

        main_box.pack_start(main_paned, True, True, 0)

        # Status bar
        self._status_bar = Gtk.Label()
        self._status_bar.set_xalign(0)
        self._status_bar.set_margin_start(8)
        self._status_bar.set_margin_end(8)
        self._status_bar.set_margin_top(4)
        self._status_bar.set_margin_bottom(4)
        self._status_bar.get_style_context().add_class('dim-label')
        main_box.pack_start(self._status_bar, False, False, 0)

        main_box.show_all()

    def _setup_menu(self):
        """Set up keyboard shortcuts and window actions."""
        # Stage selected file
        stage_action = Gio.SimpleAction.new('stage-selected', None)
        stage_action.connect('activate', lambda a, p: self._stage_selected())
        self.add_action(stage_action)

        # Unstage selected file
        unstage_action = Gio.SimpleAction.new('unstage-selected', None)
        unstage_action.connect('activate', lambda a, p: self._unstage_selected())
        self.add_action(unstage_action)

        # Revert selected file
        revert_action = Gio.SimpleAction.new('revert-selected', None)
        revert_action.connect('activate', lambda a, p: self._revert_selected())
        self.add_action(revert_action)

    def _create_menubar(self):
        """Create the menu bar."""
        menubar = Gtk.MenuBar()

        # Repository menu
        repo_menu = Gtk.Menu()
        repo_item = Gtk.MenuItem(label='Repository')
        repo_item.set_submenu(repo_menu)

        open_item = Gtk.MenuItem(label='Open...')
        open_item.connect('activate', lambda w: self.show_open_dialog())
        repo_menu.append(open_item)

        rescan_item = Gtk.MenuItem(label='Rescan')
        rescan_item.connect('activate', lambda w: self.rescan())
        repo_menu.append(rescan_item)

        repo_menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect('activate', lambda w: self.get_application().quit())
        repo_menu.append(quit_item)

        menubar.append(repo_item)

        # Edit menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label='Edit')
        edit_item.set_submenu(edit_menu)

        stage_item = Gtk.MenuItem(label='Stage Selected')
        stage_item.connect('activate', lambda w: self._stage_selected())
        edit_menu.append(stage_item)

        unstage_item = Gtk.MenuItem(label='Unstage Selected')
        unstage_item.connect('activate', lambda w: self._unstage_selected())
        edit_menu.append(unstage_item)

        edit_menu.append(Gtk.SeparatorMenuItem())

        revert_item = Gtk.MenuItem(label='Revert Selected')
        revert_item.connect('activate', lambda w: self._revert_selected())
        edit_menu.append(revert_item)

        menubar.append(edit_item)

        # Commit menu
        commit_menu = Gtk.Menu()
        commit_item = Gtk.MenuItem(label='Commit')
        commit_item.set_submenu(commit_menu)

        stage_all_item = Gtk.MenuItem(label='Stage All')
        stage_all_item.connect('activate', lambda w: self.stage_all())
        commit_menu.append(stage_all_item)

        unstage_all_item = Gtk.MenuItem(label='Unstage All')
        unstage_all_item.connect('activate', lambda w: self.unstage_all())
        commit_menu.append(unstage_all_item)

        commit_menu.append(Gtk.SeparatorMenuItem())

        do_commit_item = Gtk.MenuItem(label='Commit')
        do_commit_item.connect('activate', lambda w: self.do_commit())
        commit_menu.append(do_commit_item)

        amend_item = Gtk.MenuItem(label='Amend Last Commit')
        amend_item.connect('activate', lambda w: self.toggle_amend())
        commit_menu.append(amend_item)

        menubar.append(commit_item)

        # Remote menu
        remote_menu = Gtk.Menu()
        remote_item = Gtk.MenuItem(label='Remote')
        remote_item.set_submenu(remote_menu)

        fetch_item = Gtk.MenuItem(label='Fetch')
        fetch_item.connect('activate', lambda w: self.do_fetch())
        remote_menu.append(fetch_item)

        pull_item = Gtk.MenuItem(label='Pull')
        pull_item.connect('activate', lambda w: self.do_pull())
        remote_menu.append(pull_item)

        push_item = Gtk.MenuItem(label='Push')
        push_item.connect('activate', lambda w: self.do_push())
        remote_menu.append(push_item)

        menubar.append(remote_item)

        # Help menu
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label='Help')
        help_item.set_submenu(help_menu)

        about_item = Gtk.MenuItem(label='About')
        about_item.connect('activate', lambda w: self._show_about())
        help_menu.append(about_item)

        menubar.append(help_item)

        return menubar

    def _show_about(self):
        """Show the about dialog."""
        about = Gtk.AboutDialog(
            transient_for=self,
            modal=True,
            program_name='Git GUI GTK',
            version='1.0.0',
            comments='A GTK3 replacement for git-gui',
            license_type=Gtk.License.GPL_3_0
        )
        about.run()
        about.destroy()

    def open_repository(self, path):
        """Open a git repository."""
        if self._git.open_repository(path):
            self.set_title('Git GUI - ' + self._git.get_repo_name())
            self._update_branch_label()
            self.rescan()
            self._set_status('Opened repository: ' + path)
        else:
            self._set_status('Not a git repository: ' + path)
            self._clear_ui()

    def _clear_ui(self):
        """Clear all UI elements."""
        self._unstaged_list.set_files([])
        self._staged_list.set_files([])
        self._diff_view.clear()
        self._branch_label.set_text('')
        self._commit_area.set_commit_sensitive(False)

    def _update_branch_label(self):
        """Update the branch indicator."""
        branch = self._git.get_current_branch()
        self._branch_label.set_text('  ' + branch if branch else '')

    def rescan(self):
        """Rescan the repository for changes."""
        if not self._git.is_valid():
            return

        unstaged, staged = self._git.get_status()
        self._unstaged_list.set_files(unstaged)
        self._staged_list.set_files(staged)

        self._update_branch_label()
        self._set_status('{} unstaged, {} staged changes'.format(len(unstaged), len(staged)))

        # Enable commit button only if there are staged files
        self._commit_area.set_commit_sensitive(len(staged) > 0)

        # Clear diff if selected file is no longer in list
        if self._current_file:
            all_files = [f.path for f in unstaged + staged]
            if self._current_file.path not in all_files:
                self._diff_view.clear()
                self._current_file = None

    def _on_unstaged_file_selected(self, widget, file_change):
        """Handle unstaged file selection."""
        self._staged_list.clear_selection()
        self._current_file = file_change
        self._show_diff(file_change, staged=False)

    def _on_staged_file_selected(self, widget, file_change):
        """Handle staged file selection."""
        self._unstaged_list.clear_selection()
        self._current_file = file_change
        self._show_diff(file_change, staged=True)

    def _on_unstaged_file_activated(self, widget, file_change):
        """Handle unstaged file double-click (stage)."""
        if file_change is None:
            # Stage all button clicked
            self.stage_all()
        else:
            self._stage_file(file_change)

    def _on_staged_file_activated(self, widget, file_change):
        """Handle staged file double-click (unstage)."""
        if file_change is None:
            # Unstage all button clicked
            self.unstage_all()
        else:
            self._unstage_file(file_change)

    def _show_diff(self, file_change, staged):
        """Show diff for a file."""
        diff = self._git.get_diff(file_change.path, staged=staged)
        self._diff_view.set_diff(diff, file_change.path)

    def _stage_file(self, file_change):
        """Stage a single file."""
        if self._git.stage_file(file_change.path):
            self._set_status('Staged: ' + file_change.path)
            self.rescan()
        else:
            self._set_status('Failed to stage: ' + file_change.path)

    def _unstage_file(self, file_change):
        """Unstage a single file."""
        if self._git.unstage_file(file_change.path):
            self._set_status('Unstaged: ' + file_change.path)
            self.rescan()
        else:
            self._set_status('Failed to unstage: ' + file_change.path)

    def _stage_selected(self):
        """Stage the currently selected file."""
        file_change = self._unstaged_list.get_selected_file()
        if file_change:
            self._stage_file(file_change)

    def _unstage_selected(self):
        """Unstage the currently selected file."""
        file_change = self._staged_list.get_selected_file()
        if file_change:
            self._unstage_file(file_change)

    def _revert_selected(self):
        """Revert the currently selected file."""
        file_change = self._unstaged_list.get_selected_file()
        if file_change:
            # Show confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text='Revert Changes?'
            )
            dialog.format_secondary_text(
                'This will discard all changes to:\n{}\n\nThis cannot be undone.'.format(file_change.path)
            )
            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.OK:
                success, message = self._git.revert_file(file_change.path)
                self._set_status(message)
                self.rescan()

    def stage_all(self):
        """Stage all unstaged files."""
        if self._git.stage_all():
            self._set_status('Staged all changes')
            self.rescan()
        else:
            self._set_status('Failed to stage all changes')

    def unstage_all(self):
        """Unstage all staged files."""
        if self._git.unstage_all():
            self._set_status('Unstaged all changes')
            self.rescan()
        else:
            self._set_status('Failed to unstage all changes')

    def _on_commit_requested(self, widget, message, amend, sign_off):
        """Handle commit request from commit area."""
        self.do_commit(message, amend, sign_off)

    def do_commit(self, message=None, amend=None, sign_off=None):
        """Perform a commit."""
        if message is None:
            message = self._commit_area.get_message()
        if amend is None:
            amend = self._commit_area.is_amend_mode()
        if sign_off is None:
            sign_off = self._commit_area.is_signoff_enabled()

        if not message.strip() and not amend:
            self._show_error('Commit Error', 'Please enter a commit message.')
            return

        success, result_msg = self._git.commit(message, amend=amend, sign_off=sign_off)
        if success:
            self._set_status(result_msg)
            self._commit_area.clear_message()
            self._commit_area.set_amend_mode(False)
            self.rescan()
        else:
            self._show_error('Commit Error', result_msg)

    def toggle_amend(self):
        """Toggle amend mode and load last commit message."""
        current = self._commit_area.is_amend_mode()
        self._commit_area.set_amend_mode(not current)

        if not current:
            # Loading amend mode, get last commit message
            last_msg = self._git.get_last_commit_message()
            self._commit_area.set_message(last_msg)

    def do_push(self):
        """Push to remote."""
        self._set_status('Pushing...')

        def do_push_async():
            success, message = self._git.push()
            GLib.idle_add(self._on_push_complete, success, message)

        import threading
        thread = threading.Thread(target=do_push_async)
        thread.daemon = True
        thread.start()

    def _on_push_complete(self, success, message):
        """Handle push completion."""
        self._set_status(message)
        if not success:
            self._show_error('Push Error', message)

    def do_pull(self):
        """Pull from remote."""
        self._set_status('Pulling...')

        def do_pull_async():
            success, message = self._git.pull()
            GLib.idle_add(self._on_pull_complete, success, message)

        import threading
        thread = threading.Thread(target=do_pull_async)
        thread.daemon = True
        thread.start()

    def _on_pull_complete(self, success, message):
        """Handle pull completion."""
        self._set_status(message)
        if success:
            self.rescan()
        else:
            self._show_error('Pull Error', message)

    def do_fetch(self):
        """Fetch from remote."""
        self._set_status('Fetching...')

        def do_fetch_async():
            success, message = self._git.fetch()
            GLib.idle_add(self._on_fetch_complete, success, message)

        import threading
        thread = threading.Thread(target=do_fetch_async)
        thread.daemon = True
        thread.start()

    def _on_fetch_complete(self, success, message):
        """Handle fetch completion."""
        self._set_status(message)
        if not success:
            self._show_error('Fetch Error', message)

    def _set_status(self, message):
        """Set status bar message."""
        self._status_bar.set_text(message)

    def _show_error(self, title, message):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_open_dialog(self):
        """Show dialog to open a repository."""
        dialog = Gtk.FileChooserDialog(
            title='Open Git Repository',
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Set initial folder
        if self._git.repo_path:
            dialog.set_current_folder(self._git.repo_path)
        else:
            dialog.set_current_folder(os.path.expanduser('~'))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.open_repository(dialog.get_filename())
        dialog.destroy()

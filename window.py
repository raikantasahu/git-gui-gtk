"""Main application window."""

import os

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib

from git_operations import GitOperations, FileChange, FileStatus
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

        # Left side: file lists with resizable paned (full vertical space)
        file_lists_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        file_lists_paned.set_size_request(280, -1)

        # Unstaged changes
        self._unstaged_list = FileListWidget(title='Unstaged Changes', staged=False)
        self._unstaged_list.set_vexpand(True)
        self._unstaged_list.connect('file-selected', self._on_unstaged_file_selected)
        self._unstaged_list.connect('file-activated', self._on_unstaged_file_activated)
        self._unstaged_list.connect('file-revert-requested', self._on_file_revert_requested)
        file_lists_paned.pack1(self._unstaged_list, resize=True, shrink=False)

        # Staged changes
        self._staged_list = FileListWidget(title='Staged Changes', staged=True)
        self._staged_list.set_vexpand(True)
        self._staged_list.connect('file-selected', self._on_staged_file_selected)
        self._staged_list.connect('file-activated', self._on_staged_file_activated)
        file_lists_paned.pack2(self._staged_list, resize=True, shrink=False)

        main_paned.pack1(file_lists_paned, resize=False, shrink=False)

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

        # Branch menu
        branch_menu = Gtk.Menu()
        branch_item = Gtk.MenuItem(label='Branch')
        branch_item.set_submenu(branch_menu)

        create_branch_item = Gtk.MenuItem(label='Create...')
        create_branch_item.connect('activate', lambda w: self._show_create_branch_dialog())
        branch_menu.append(create_branch_item)

        checkout_branch_item = Gtk.MenuItem(label='Checkout...')
        checkout_branch_item.connect('activate', lambda w: self._show_checkout_branch_dialog())
        branch_menu.append(checkout_branch_item)

        rename_branch_item = Gtk.MenuItem(label='Rename...')
        rename_branch_item.connect('activate', lambda w: self._show_rename_branch_dialog())
        branch_menu.append(rename_branch_item)

        delete_branch_item = Gtk.MenuItem(label='Delete...')
        delete_branch_item.connect('activate', lambda w: self._show_delete_branch_dialog())
        branch_menu.append(delete_branch_item)

        branch_menu.append(Gtk.SeparatorMenuItem())

        reset_branch_item = Gtk.MenuItem(label='Reset...')
        reset_branch_item.connect('activate', lambda w: self._show_reset_branch_dialog())
        branch_menu.append(reset_branch_item)

        menubar.append(branch_item)

        # Remote menu
        remote_menu = Gtk.Menu()
        remote_item = Gtk.MenuItem(label='Remote')
        remote_item.set_submenu(remote_menu)

        list_remotes_item = Gtk.MenuItem(label='List')
        list_remotes_item.connect('activate', lambda w: self._show_list_remotes_dialog())
        remote_menu.append(list_remotes_item)

        add_remote_item = Gtk.MenuItem(label='Add...')
        add_remote_item.connect('activate', lambda w: self._show_add_remote_dialog())
        remote_menu.append(add_remote_item)

        remote_menu.append(Gtk.SeparatorMenuItem())

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

    def _on_file_revert_requested(self, widget, file_change):
        """Handle revert request from context menu."""
        if not file_change:
            return

        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text='Revert Changes?'
        )
        dialog.format_secondary_text(
            'This will discard all changes to:\n{}\n\nThis action cannot be undone.'.format(file_change.path)
        )
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Revert', Gtk.ResponseType.OK)

        # Make the Revert button look destructive
        revert_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        revert_btn.get_style_context().add_class('destructive-action')

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            success, message = self._git.revert_file(file_change.path)
            self._set_status(message)
            self.rescan()

    def _show_diff(self, file_change, staged):
        """Show diff for a file."""
        diff = self._git.get_diff(file_change.path, staged=staged)
        status = self._get_file_status_text(file_change, staged)
        self._diff_view.set_diff(diff, file_change.path, status)

    def _get_file_status_text(self, file_change, staged):
        """Get descriptive status text for a file."""
        if staged:
            return 'Staged for commit'
        else:
            status_map = {
                FileStatus.MODIFIED: 'Modified, not staged',
                FileStatus.ADDED: 'Added, not staged',
                FileStatus.DELETED: 'Missing',
                FileStatus.RENAMED: 'Renamed, not staged',
                FileStatus.COPIED: 'Copied, not staged',
                FileStatus.UNTRACKED: 'Untracked, not staged',
                FileStatus.UNMERGED: 'Unmerged',
            }
            return status_map.get(file_change.status, 'Unknown')

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

    def _show_create_branch_dialog(self):
        """Show dialog to create a new branch."""
        dialog = Gtk.Dialog(
            title='Create Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        label = Gtk.Label(label='Branch name:')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)

        checkout_check = Gtk.CheckButton(label='Checkout after creation')
        checkout_check.set_active(True)
        content.pack_start(checkout_check, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        branch_name = entry.get_text().strip()
        checkout = checkout_check.get_active()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and branch_name:
            success, message = self._git.create_branch(branch_name, checkout=checkout)
            self._set_status(message)
            if success:
                self._update_branch_label()
            else:
                self._show_error('Create Branch Error', message)

    def _show_checkout_branch_dialog(self):
        """Show dialog to checkout a branch."""
        branches = self._git.get_branches()
        if not branches:
            self._show_error('Checkout Branch', 'No branches found.')
            return

        dialog = Gtk.Dialog(
            title='Checkout Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        label = Gtk.Label(label='Select branch:')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        combo = Gtk.ComboBoxText()
        current_branch = self._git.get_current_branch()
        active_index = 0
        for i, branch in enumerate(branches):
            combo.append_text(branch)
            if branch == current_branch:
                active_index = i
        combo.set_active(active_index)
        content.pack_start(combo, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        selected_branch = combo.get_active_text()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and selected_branch:
            success, message = self._git.checkout_branch(selected_branch)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            else:
                self._show_error('Checkout Branch Error', message)

    def _show_rename_branch_dialog(self):
        """Show dialog to rename a branch."""
        branches = self._git.get_branches()
        if not branches:
            self._show_error('Rename Branch', 'No branches found.')
            return

        dialog = Gtk.Dialog(
            title='Rename Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        label1 = Gtk.Label(label='Select branch to rename:')
        label1.set_xalign(0)
        content.pack_start(label1, False, False, 0)

        combo = Gtk.ComboBoxText()
        current_branch = self._git.get_current_branch()
        active_index = 0
        for i, branch in enumerate(branches):
            combo.append_text(branch)
            if branch == current_branch:
                active_index = i
        combo.set_active(active_index)
        content.pack_start(combo, False, False, 0)

        label2 = Gtk.Label(label='New name:')
        label2.set_xalign(0)
        content.pack_start(label2, False, False, 0)

        entry = Gtk.Entry()
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        old_name = combo.get_active_text()
        new_name = entry.get_text().strip()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and old_name and new_name:
            success, message = self._git.rename_branch(old_name, new_name)
            self._set_status(message)
            if success:
                self._update_branch_label()
            else:
                self._show_error('Rename Branch Error', message)

    def _show_delete_branch_dialog(self):
        """Show dialog to delete a branch."""
        branches = self._git.get_branches()
        current_branch = self._git.get_current_branch()
        # Filter out current branch
        branches = [b for b in branches if b != current_branch]

        if not branches:
            self._show_error('Delete Branch', 'No branches available to delete (cannot delete current branch).')
            return

        dialog = Gtk.Dialog(
            title='Delete Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            'Delete', Gtk.ResponseType.OK
        )

        # Make delete button destructive
        delete_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        delete_btn.get_style_context().add_class('destructive-action')

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        label = Gtk.Label(label='Select branch to delete:')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        combo = Gtk.ComboBoxText()
        for branch in branches:
            combo.append_text(branch)
        combo.set_active(0)
        content.pack_start(combo, False, False, 0)

        force_check = Gtk.CheckButton(label='Force delete (even if not merged)')
        content.pack_start(force_check, False, False, 0)

        dialog.show_all()

        response = dialog.run()
        selected_branch = combo.get_active_text()
        force = force_check.get_active()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and selected_branch:
            success, message = self._git.delete_branch(selected_branch, force=force)
            self._set_status(message)
            if not success:
                self._show_error('Delete Branch Error', message)

    def _show_list_remotes_dialog(self):
        """Show dialog listing all remotes."""
        remotes = self._git.get_remotes_with_urls()

        dialog = Gtk.Dialog(
            title='Remotes',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        dialog.set_default_size(500, 200)

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

    def _show_add_remote_dialog(self):
        """Show dialog to add a new remote."""
        dialog = Gtk.Dialog(
            title='Add Remote',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 200)

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        name_label = Gtk.Label(label='Remote name:')
        name_label.set_xalign(0)
        content.pack_start(name_label, False, False, 0)

        name_entry = Gtk.Entry()
        name_entry.set_text('origin')
        content.pack_start(name_entry, False, False, 0)

        url_label = Gtk.Label(label='Remote URL:')
        url_label.set_xalign(0)
        content.pack_start(url_label, False, False, 0)

        url_entry = Gtk.Entry()
        url_entry.set_activates_default(True)
        url_entry.set_placeholder_text('https://github.com/user/repo.git')
        content.pack_start(url_entry, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        name = name_entry.get_text().strip()
        url = url_entry.get_text().strip()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and name and url:
            success, message = self._git.add_remote(name, url)
            self._set_status(message)
            if not success:
                self._show_error('Add Remote Error', message)

    def _show_reset_branch_dialog(self):
        """Show dialog to reset current branch."""
        dialog = Gtk.Dialog(
            title='Reset Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            'Reset', Gtk.ResponseType.OK
        )

        # Make reset button destructive
        reset_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        reset_btn.get_style_context().add_class('destructive-action')

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        current_branch = self._git.get_current_branch()
        info_label = Gtk.Label(label=f'Reset branch: {current_branch}')
        info_label.set_xalign(0)
        content.pack_start(info_label, False, False, 0)

        label = Gtk.Label(label='Reset to (commit/branch/tag):')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text('HEAD')
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)

        mode_label = Gtk.Label(label='Reset mode:')
        mode_label.set_xalign(0)
        content.pack_start(mode_label, False, False, 0)

        soft_radio = Gtk.RadioButton.new_with_label(None, 'Soft (keep changes staged)')
        content.pack_start(soft_radio, False, False, 0)

        mixed_radio = Gtk.RadioButton.new_with_label_from_widget(soft_radio, 'Mixed (keep changes unstaged)')
        mixed_radio.set_active(True)
        content.pack_start(mixed_radio, False, False, 0)

        hard_radio = Gtk.RadioButton.new_with_label_from_widget(soft_radio, 'Hard (discard all changes)')
        content.pack_start(hard_radio, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        target = entry.get_text().strip()
        if soft_radio.get_active():
            mode = 'soft'
        elif hard_radio.get_active():
            mode = 'hard'
        else:
            mode = 'mixed'
        dialog.destroy()

        if response == Gtk.ResponseType.OK and target:
            success, message = self._git.reset_branch(target, mode=mode)
            self._set_status(message)
            if success:
                self.rescan()
            else:
                self._show_error('Reset Branch Error', message)

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

"""Main application window."""

import os
import threading
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib

from cache import RecentRepositoryList
from widgets import FileListWidget, DiffView, CommitArea
from actions import get_action_shortcut
from viewmodels.repository_vm import RepositoryViewModel
from viewmodels.file_list_vm import FileListViewModel
from viewmodels.diff_vm import DiffViewModel
from viewmodels.commit_vm import CommitViewModel
from viewmodels.remote_vm import RemoteViewModel
from viewmodels.branch_vm import BranchViewModel
import dialogs
from dialogs.message import MessageType

class GitGuiWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title('Git GUI')
        self.set_default_size(1200, 800)

        # ViewModels
        self._repo_vm = RepositoryViewModel()
        self._file_list_vm = FileListViewModel(self._repo_vm)
        self._diff_vm = DiffViewModel(self._repo_vm)
        self._commit_vm = CommitViewModel(self._repo_vm)
        self._remote_vm = RemoteViewModel(self._repo_vm)
        self._branch_vm = BranchViewModel(self._repo_vm)

        # Wire VM callbacks
        self._repo_vm.on_state_changed = self._on_repo_state_changed
        self._repo_vm.set_status = self._on_vm_status

        self._setup_ui()

        # Try to open current directory as repo
        cwd = os.getcwd()
        self.open_repository(cwd)

    # --- VM callback handlers ---

    def _on_vm_status(self, message, msg_type='info'):
        """Handle status messages from VMs."""
        self._set_status(message, MessageType.get_message_type(msg_type))

    def _on_repo_state_changed(self):
        """Handle repository state changes — push VM state to widgets."""
        vm = self._repo_vm
        self._unstaged_list.set_files(vm.unstaged_files)
        self._staged_list.set_files(vm.staged_files)

        branch = vm.branch_name
        self._branch_label.set_text('  ' + branch if branch else '')
        if branch:
            self._visualize_branch_item.set_label(f"Visualize {branch}'s History")

        if not self._commit_vm.amend_mode:
            self._commit_area.set_commit_sensitive(vm.has_staged_files)

        # Clear diff if selected file is no longer in lists
        if self._diff_vm.is_stale(vm.unstaged_files, vm.staged_files):
            self._diff_vm.clear()
            self._diff_view.clear()

    # --- UI setup ---

    # Menu items that should display keyboard shortcut hints
    _MENU_SHORTCUTS = {
        'menu_open': 'open',
        'menu_rescan': 'rescan',
        'menu_explore': 'explore',
        'menu_quit': 'quit',
        'menu_add_remote': 'add-remote',
        'menu_fetch': 'fetch',
        'menu_pull': 'pull',
        'menu_push': 'push',
        'menu_about': 'about',
    }

    def _setup_ui(self):
        """Set up the user interface."""
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__), 'ui', 'window.ui'))

        main_box = builder.get_object('main_box')
        self.add(main_box)

        # --- Widget references ---
        self._branch_label = builder.get_object('branch_label')
        self._diff_view = builder.get_object('diff_view')
        self._commit_area = builder.get_object('commit_area')
        self._status_bar = builder.get_object('status_bar')
        self._visualize_branch_item = builder.get_object('menu_visualize_branch')
        self._recent_menu_item = builder.get_object('menu_open_recent')
        self._recent_submenu = builder.get_object('recent_submenu')

        # --- Shortcut labels on menu items ---
        self._add_shortcut_labels(builder)

        # --- Dynamic recent repos menu ---
        self._update_recent_menu()

        # --- FileListWidgets (need constructor params) ---
        file_lists_paned = builder.get_object('file_lists_paned')

        self._unstaged_list = FileListWidget(title='Unstaged Changes', staged=False)
        self._unstaged_list.set_vexpand(True)
        file_lists_paned.pack1(self._unstaged_list, resize=True, shrink=False)

        self._staged_list = FileListWidget(title='Staged Changes', staged=True)
        self._staged_list.set_vexpand(True)
        file_lists_paned.pack2(self._staged_list, resize=True, shrink=False)

        # --- Signal connections: toolbar ---
        builder.get_object('open_button').connect('clicked', lambda b: self.show_open_dialog())
        builder.get_object('rescan_button').connect('clicked', lambda b: self.rescan())

        # --- Signal connections: file lists ---
        self._unstaged_list.connect('file-selected', self._on_unstaged_file_selected)
        self._unstaged_list.connect('file-activated', self._on_unstaged_file_activated)
        self._unstaged_list.connect('file-revert-requested', self._on_file_revert_requested)

        self._staged_list.connect('file-selected', self._on_staged_file_selected)
        self._staged_list.connect('file-activated', self._on_staged_file_activated)

        # --- Signal connections: diff view ---
        self._diff_view.connect('stage-hunk', self._on_stage_hunk)
        self._diff_view.connect('stage-lines', self._on_stage_lines)
        self._diff_view.connect('unstage-hunk', self._on_unstage_hunk)
        self._diff_view.connect('unstage-lines', self._on_unstage_lines)
        self._diff_view.connect('revert-hunk', self._on_revert_hunk)
        self._diff_view.connect('revert-lines', self._on_revert_lines)
        self._diff_view.connect('context-changed', self._on_context_changed)

        # --- Signal connections: commit area ---
        self._commit_area.connect('commit-requested', self._on_commit_requested)
        self._commit_area.connect('push-requested', lambda w: self.show_push_dialog())
        self._commit_area.connect('rescan-requested', lambda w: self.rescan())
        self._commit_area.connect('amend-toggled', self._on_amend_toggled)

        # --- Signal connections: menu items ---
        menu_signals = {
            'menu_open': lambda w: self.show_open_dialog(),
            'menu_explore': lambda w: self.explore_repository(),
            'menu_rescan': lambda w: self.rescan(),
            'menu_visualize_branch': lambda w: self._visualize_branch_history(),
            'menu_visualize_all': lambda w: self._visualize_all_history(),
            'menu_db_stats': lambda w: self._show_database_statistics(),
            'menu_db_compress': lambda w: self._compress_database(),
            'menu_db_verify': lambda w: self._verify_database(),
            'menu_quit': lambda w: self.get_application().quit(),
            'menu_create_branch': lambda w: self._show_create_branch_dialog(),
            'menu_checkout_branch': lambda w: self._show_checkout_branch_dialog(),
            'menu_rename_branch': lambda w: self._show_rename_branch_dialog(),
            'menu_delete_branch': lambda w: self._show_delete_branch_dialog(),
            'menu_reset_branch': lambda w: self._show_reset_branch_dialog(),
            'menu_merge': lambda w: self._show_merge_dialog(),
            'menu_rebase': lambda w: self._show_rebase_dialog(),
            'menu_list_remotes': lambda w: self._show_list_remotes_dialog(),
            'menu_add_remote': lambda w: self.show_add_remote_dialog(),
            'menu_rename_remote': lambda w: self.show_rename_remote_dialog(),
            'menu_delete_remote': lambda w: self.show_delete_remote_dialog(),
            'menu_fetch': lambda w: self.show_fetch_dialog(),
            'menu_pull': lambda w: self.show_pull_dialog(),
            'menu_push': lambda w: self.show_push_dialog(),
            'menu_git_docs': lambda w: self._open_git_documentation(),
            'menu_ssh_key': lambda w: self._show_ssh_key(),
            'menu_about': lambda w: self._show_about(),
        }
        for widget_id, handler in menu_signals.items():
            builder.get_object(widget_id).connect('activate', handler)

        main_box.show_all()

    def _add_shortcut_labels(self, builder):
        """Replace plain labels on menu items with label + shortcut hint boxes."""
        for widget_id, action_name in self._MENU_SHORTCUTS.items():
            shortcut = get_action_shortcut(action_name)
            if not shortcut:
                continue
            item = builder.get_object(widget_id)
            label_text = item.get_label()
            child = item.get_child()
            item.remove(child)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            label_widget = Gtk.Label(label=label_text)
            label_widget.set_xalign(0)
            box.pack_start(label_widget, True, True, 0)
            shortcut_label = Gtk.Label(label=shortcut)
            shortcut_label.get_style_context().add_class('dim-label')
            box.pack_end(shortcut_label, False, False, 0)
            item.add(box)

    # --- Recent repositories ---

    def _update_recent_menu(self):
        """Update the Open Recent submenu with recent repositories."""
        # Clear existing items
        for child in self._recent_submenu.get_children():
            self._recent_submenu.remove(child)

        recent = RecentRepositoryList.get_recent()

        if not recent:
            empty_item = Gtk.MenuItem(label='(No recent repositories)')
            empty_item.set_sensitive(False)
            self._recent_submenu.append(empty_item)
        else:
            for path in recent:
                # Show just the directory name as label, full path as tooltip
                label = os.path.basename(path) or path
                item = Gtk.MenuItem(label=label)
                item.set_tooltip_text(path)
                item.connect('activate', self._on_recent_item_activated, path)
                self._recent_submenu.append(item)

            # Add separator and clear option
            self._recent_submenu.append(Gtk.SeparatorMenuItem())
            clear_item = Gtk.MenuItem(label='Clear Recent')
            clear_item.connect('activate', self._on_clear_recent)
            self._recent_submenu.append(clear_item)

        self._recent_submenu.show_all()

    def _on_recent_item_activated(self, widget, path):
        """Handle click on a recent repository item."""
        self.open_repository(path)

    def _on_clear_recent(self, widget):
        """Clear the recent repositories list."""
        RecentRepositoryList.clear_recent()
        self._update_recent_menu()

    # --- Pure UI actions ---

    def _open_git_documentation(self):
        """Open Git documentation in default web browser."""
        import webbrowser
        webbrowser.open('https://git-scm.com/doc')

    def _show_ssh_key(self):
        """Show the user's SSH public key."""
        dialogs.show_ssh_key_dialog(self, on_status=lambda msg, t=MessageType.INFO: self._set_status(msg, t))

    def _show_about(self):
        """Show the about dialog."""
        dialogs.show_about_dialog(self)

    # --- Repository operations ---

    def open_repository(self, path):
        """Open a git repository."""
        success = self._repo_vm.open_repository(path)
        if success:
            self.set_title('Git GUI - ' + self._repo_vm.repo_name)
            RecentRepositoryList.add_recent(self._repo_vm.repo_path)
            self._update_recent_menu()
        else:
            self._clear_ui()

    def _clear_ui(self):
        """Clear all UI elements."""
        self._unstaged_list.set_files([])
        self._staged_list.set_files([])
        self._diff_vm.clear()
        self._diff_view.clear()
        self._branch_label.set_text('')
        self._commit_area.set_commit_sensitive(False)

    def rescan(self):
        """Rescan the repository for changes."""
        self._repo_vm.rescan()

    def explore_repository(self):
        """Open repository root in default file browser."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            subprocess.Popen(['xdg-open', self._repo_vm.repo_path])
        except Exception as e:
            self._show_error('Explore Repository', f'Failed to open file browser: {e}')

    def _visualize_branch_history(self):
        """Open gitk to visualize current branch history."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            subprocess.Popen(['gitk', self._repo_vm.branch_name], cwd=self._repo_vm.repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _visualize_all_history(self):
        """Open gitk to visualize all branches history."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            subprocess.Popen(['gitk', '--all'], cwd=self._repo_vm.repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _show_database_statistics(self):
        """Show git database statistics."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        dialogs.show_database_statistics_dialog(self, self._repo_vm.repo)

    def _compress_database(self):
        """Compress git database (git gc)."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        self._set_status('Compressing database...')
        dialogs.show_compress_database_dialog(
            self, self._repo_vm.repo,
            on_complete=lambda success, msg: self._set_status(
                msg, MessageType.INFO if success else MessageType.ERROR
            )
        )

    def _verify_database(self):
        """Verify git database (git fsck)."""
        if not self._repo_vm.repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        self._set_status('Verifying database...')
        dialogs.show_verify_database_dialog(
            self, self._repo_vm.repo,
            on_complete=lambda success, msg: self._set_status(
                'Database verification completed' if success else 'Database verification found issues'
            )
        )

    # --- File selection handlers ---

    def _on_unstaged_file_selected(self, widget, file_change):
        """Handle unstaged file selection."""
        self._staged_list.clear_selection()
        self._diff_vm.show_diff(file_change, staged=False,
                                context_lines=self._diff_view.get_context_lines())
        self._update_diff_view()

    def _on_staged_file_selected(self, widget, file_change):
        """Handle staged file selection."""
        self._unstaged_list.clear_selection()
        self._diff_vm.show_diff(file_change, staged=True,
                                context_lines=self._diff_view.get_context_lines())
        self._update_diff_view()

    def _on_unstaged_file_activated(self, widget, file_change):
        """Handle unstaged file double-click (stage)."""
        if file_change is None:
            self._file_list_vm.stage_all()
        else:
            self._file_list_vm.stage_file(file_change)

    def _on_staged_file_activated(self, widget, file_change):
        """Handle staged file double-click (unstage)."""
        if file_change is None:
            self._file_list_vm.unstage_all()
        else:
            self._file_list_vm.unstage_file(file_change)

    def _on_file_revert_requested(self, widget, file_change):
        """Handle revert request from context menu."""
        if not file_change:
            return
        if self._confirm_revert('Revert Changes?',
                                'This will discard all changes to:\n{}\n\n'
                                'This action cannot be undone.'.format(file_change.path),
                                'Revert'):
            self._file_list_vm.revert_file(file_change.path)

    def _update_diff_view(self):
        """Push current DiffViewModel state to the DiffView widget."""
        vm = self._diff_vm
        self._diff_view.set_diff(vm.diff_text, vm.file_path, vm.status_text)
        self._diff_view.set_file_info(vm.file_path, vm.is_staged, vm.is_untracked)

    # --- Diff operations ---

    def _on_stage_hunk(self, widget, file_path, line):
        self._diff_vm.stage_hunk(file_path, line)

    def _on_stage_lines(self, widget, file_path, start_line, end_line):
        self._diff_vm.stage_lines(file_path, start_line, end_line)

    def _on_unstage_hunk(self, widget, file_path, line):
        self._diff_vm.unstage_hunk(file_path, line)

    def _on_unstage_lines(self, widget, file_path, start_line, end_line):
        self._diff_vm.unstage_lines(file_path, start_line, end_line)

    def _on_revert_hunk(self, widget, file_path, line):
        if self._confirm_revert('Revert Hunk?',
                                f'This will discard changes in the selected hunk from:\n{file_path}\n\n'
                                'This action cannot be undone.',
                                'Revert Hunk'):
            self._diff_vm.revert_hunk(file_path, line)

    def _on_revert_lines(self, widget, file_path, start_line, end_line):
        if self._confirm_revert('Revert Lines?',
                                f'This will discard the selected line change from:\n{file_path}\n\n'
                                'This action cannot be undone.',
                                'Revert Lines'):
            self._diff_vm.revert_lines(file_path, start_line, end_line)

    def _on_context_changed(self, widget, context_lines):
        """Handle context lines change from diff view."""
        self._diff_vm.context_lines = context_lines
        if self._diff_vm.refresh():
            self._update_diff_view()
            self._set_status(f'Context lines: {context_lines}')

    # --- Staging operations (thin delegation for actions.py) ---

    def stage_selected(self):
        """Stage the currently selected file."""
        file_change = self._unstaged_list.get_selected_file()
        if file_change:
            self._file_list_vm.stage_file(file_change)

    def unstage_selected(self):
        """Unstage the currently selected file."""
        file_change = self._staged_list.get_selected_file()
        if file_change:
            self._file_list_vm.unstage_file(file_change)

    def revert_selected(self):
        """Revert the currently selected file."""
        file_change = self._unstaged_list.get_selected_file()
        if file_change:
            if self._confirm_revert('Revert Changes?',
                                    'This will discard all changes to:\n{}\n\n'
                                    'This cannot be undone.'.format(file_change.path),
                                    'Revert'):
                self._file_list_vm.revert_file(file_change.path)

    def stage_all(self):
        """Stage all unstaged files."""
        self._file_list_vm.stage_all()

    def unstage_all(self):
        """Unstage all staged files."""
        self._file_list_vm.unstage_all()

    # --- Commit operations ---

    def _on_commit_requested(self, widget, message, amend, sign_off):
        """Handle commit request from commit area."""
        success, result_msg = self._commit_vm.commit(message, amend, sign_off)
        if success:
            self._commit_area.clear_message()
            self._commit_area.set_amend_mode(False)
        else:
            self._show_error('Commit Error', result_msg)

    def _on_amend_toggled(self, widget, amend_enabled):
        """Handle amend checkbox toggle."""
        if amend_enabled:
            last_msg, files = self._commit_vm.get_amend_data()
            self._commit_area.set_message(last_msg)
            self._staged_list.set_files(files)
            self._commit_area.set_commit_sensitive(True)
        else:
            self._commit_vm.leave_amend_mode()
            self._commit_area.clear_message()

    def commit(self, message=None, amend=None, sign_off=None):
        """Perform a commit (called from actions.py)."""
        if message is None:
            message = self._commit_area.get_message()
        if amend is None:
            amend = self._commit_area.is_amend_mode()
        if sign_off is None:
            sign_off = self._commit_area.is_signoff_enabled()
        success, result_msg = self._commit_vm.commit(message, amend, sign_off)
        if success:
            self._commit_area.clear_message()
            self._commit_area.set_amend_mode(False)
        else:
            self._show_error('Commit Error', result_msg)

    def toggle_amend(self):
        """Toggle amend mode (called from actions.py)."""
        enabled, last_msg, files = self._commit_vm.toggle_amend()
        if enabled:
            self._commit_area.set_amend_mode(True)
            self._commit_area.set_message(last_msg)
        else:
            self._commit_area.set_amend_mode(False)
            self._commit_area.clear_message()

    # --- Remote operations (async wrappers) ---

    def show_push_dialog(self):
        """Show dialog to push to a remote."""
        result = dialogs.show_push_dialog(self, self._repo_vm.repo)
        if result:
            remote, branch, force, tags = result
            branch_display = f'{remote}/{branch}' if branch else remote
            self._set_status(f'Pushing to {branch_display}...')
            self._run_async(
                lambda: self._remote_vm.push(remote, branch, force, tags),
                lambda s, m: self._show_error('Push Error', m) if not s else None
            )

    def show_pull_dialog(self):
        """Show dialog to pull from a remote."""
        result = dialogs.show_pull_dialog(self, self._repo_vm.repo)
        if result:
            remote, branch, ff_only, rebase = result
            branch_display = f'{remote}/{branch}' if branch else remote
            self._set_status(f'Pulling from {branch_display}...')
            self._run_async(
                lambda: self._remote_vm.pull(remote, branch, ff_only, rebase),
                lambda s, m: self._show_error('Pull Error', m) if not s else None
            )

    def show_fetch_dialog(self):
        """Show dialog to fetch from a remote."""
        result = dialogs.show_fetch_dialog(self, self._repo_vm.repo)
        if result:
            self._set_status(f'Fetching from {result}...')
            self._run_async(
                lambda: self._remote_vm.fetch(result),
                lambda s, m: self._show_error('Fetch Error', m) if not s else None
            )

    def _run_async(self, operation, on_complete):
        """Run an operation in a background thread, dispatch result to main thread.

        Args:
            operation: callable returning (success, message)
            on_complete: callable(success, message) run on the main thread
        """
        def worker():
            success, message = operation()
            GLib.idle_add(self._on_async_complete, success, message, on_complete)

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def _on_async_complete(self, success, message, on_complete):
        """Handle async operation completion on the main thread."""
        self._set_status(message)
        if on_complete:
            on_complete(success, message)

    # --- Remote CRUD ---

    def show_add_remote_dialog(self):
        """Show dialog to add a new remote."""
        result = dialogs.show_add_remote_dialog(self, self._repo_vm.repo)
        if result:
            name, url, fetch_after = result
            success, message = self._remote_vm.add_remote(name, url)
            self._set_status(message)
            if not success:
                self._show_error('Add Remote Error', message)
            elif fetch_after:
                self._set_status(f'Fetching from {name}...')
                self._run_async(
                    lambda: self._remote_vm.fetch(name),
                    lambda s, m: self._show_error('Fetch Error', m) if not s else None
                )

    def show_rename_remote_dialog(self):
        """Show dialog to rename a remote."""
        result = dialogs.show_rename_remote_dialog(self, self._repo_vm.repo)
        if result:
            old_name, new_name = result
            success, message = self._remote_vm.rename_remote(old_name, new_name)
            self._set_status(message)
            if not success:
                self._show_error('Rename Remote Error', message)

    def show_delete_remote_dialog(self):
        """Show dialog to delete a remote."""
        result = dialogs.show_delete_remote_dialog(self, self._repo_vm.repo)
        if result:
            success, message = self._remote_vm.delete_remote(result)
            self._set_status(message)
            if not success:
                self._show_error('Delete Remote Error', message)

    # --- Branch dialogs ---

    def _show_create_branch_dialog(self):
        result = dialogs.show_create_branch_dialog(self, self._repo_vm.repo)
        if result:
            branch_name, base, checkout = result
            success, message = self._branch_vm.create_branch(branch_name, base, checkout)
            if not success:
                self._show_error('Create Branch Error', message)

    def _show_checkout_branch_dialog(self):
        result = dialogs.show_checkout_branch_dialog(self, self._repo_vm.repo)
        if result:
            success, message = self._branch_vm.checkout_branch(result)
            if not success:
                self._show_error('Checkout Branch Error', message)

    def _show_rename_branch_dialog(self):
        result = dialogs.show_rename_branch_dialog(self, self._repo_vm.repo)
        if result:
            old_name, new_name = result
            success, message = self._branch_vm.rename_branch(old_name, new_name)
            if not success:
                self._show_error('Rename Branch Error', message)

    def _show_delete_branch_dialog(self):
        result = dialogs.show_delete_branch_dialog(self, self._repo_vm.repo)
        if result:
            branch_name, force = result
            success, message = self._branch_vm.delete_branch(branch_name, force)
            if not success:
                self._show_error('Delete Branch Error', message)

    def _show_reset_branch_dialog(self):
        result = dialogs.show_reset_branch_dialog(self, self._repo_vm.repo)
        if result:
            target, mode = result
            success, message = self._branch_vm.reset_branch(target, mode)
            if not success:
                self._show_error('Reset Branch Error', message)

    def _show_merge_dialog(self):
        result = dialogs.show_merge_dialog(self, self._repo_vm.repo)
        if result:
            branch, strategy = result
            success, message = self._branch_vm.merge_branch(branch, strategy)
            self._show_status_dialog('Merge', message, success)

    def _show_rebase_dialog(self):
        result = dialogs.show_rebase_dialog(self, self._repo_vm.repo)
        if result:
            success, message = self._branch_vm.rebase_branch(result)
            self._show_status_dialog('Rebase', message, success)

    def _show_list_remotes_dialog(self):
        dialogs.show_list_remotes_dialog(self, self._repo_vm.repo)

    def show_open_dialog(self):
        """Show dialog to open a repository."""
        result = dialogs.show_open_repository_dialog(self, self._repo_vm.repo_path)
        if result:
            self.open_repository(result)

    # --- Status and error display ---

    def _set_status(self, message, msg_type=MessageType.INFO):
        """Set status bar message or show dialog for long messages."""
        MAX_STATUS_LENGTH = 100

        if len(message) > MAX_STATUS_LENGTH:
            title = msg_type.get_message_dialog_title()
            dialogs.show_message_dialog(self, title, message, msg_type)
            truncated = message[:MAX_STATUS_LENGTH - 3] + '...'
            self._status_bar.set_text(truncated)
        else:
            self._status_bar.set_text(message)

    def _show_error(self, title, message):
        """Show an error dialog."""
        dialogs.show_message_dialog(self, title, message, MessageType.ERROR)

    def _show_status_dialog(self, title, message, success):
        """Show a status dialog for operation results."""
        msg_type = MessageType.INFO if success else MessageType.ERROR
        dialogs.show_message_dialog(self, title, message, msg_type)

    def _confirm_revert(self, title, detail, button_label):
        """Show a destructive confirmation dialog.

        Returns True if the user confirmed.
        """
        return dialogs.show_confirm_dialog(self, title, detail, button_label)

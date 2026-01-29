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

def _create_menu_item(label, action_name=None):
    """Create a menu item with optional keyboard shortcut display.

    Args:
        label: Menu item label
        action_name: Action name to look up shortcut (optional)

    Returns:
        Gtk.MenuItem with shortcut shown if available
    """
    shortcut = get_action_shortcut(action_name) if action_name else ''
    if shortcut:
        # Use a box to show label and shortcut
        item = Gtk.MenuItem()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label_widget = Gtk.Label(label=label)
        label_widget.set_xalign(0)
        box.pack_start(label_widget, True, True, 0)
        shortcut_label = Gtk.Label(label=shortcut)
        shortcut_label.get_style_context().add_class('dim-label')
        box.pack_end(shortcut_label, False, False, 0)
        item.add(box)
    else:
        item = Gtk.MenuItem(label=label)
    return item

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
        self._diff_view.connect('stage-hunk', self._on_stage_hunk)
        self._diff_view.connect('stage-line', self._on_stage_line)
        self._diff_view.connect('unstage-hunk', self._on_unstage_hunk)
        self._diff_view.connect('unstage-line', self._on_unstage_line)
        self._diff_view.connect('revert-hunk', self._on_revert_hunk)
        self._diff_view.connect('revert-line', self._on_revert_line)
        self._diff_view.connect('context-changed', self._on_context_changed)
        right_paned.pack1(self._diff_view, resize=True, shrink=False)

        # Commit area (bottom)
        self._commit_area = CommitArea()
        self._commit_area.set_size_request(-1, 180)
        self._commit_area.connect('commit-requested', self._on_commit_requested)
        self._commit_area.connect('push-requested', lambda w: self.show_push_dialog())
        self._commit_area.connect('rescan-requested', lambda w: self.rescan())
        self._commit_area.connect('amend-toggled', self._on_amend_toggled)
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

    def _create_menubar(self):
        """Create the menu bar."""
        menubar = Gtk.MenuBar()

        # Repository menu
        repo_menu = Gtk.Menu()
        repo_item = Gtk.MenuItem(label='Repository')
        repo_item.set_submenu(repo_menu)

        open_item = _create_menu_item('Open...', 'open')
        open_item.connect('activate', lambda w: self.show_open_dialog())
        repo_menu.append(open_item)

        # Open Recent submenu
        self._recent_menu_item = Gtk.MenuItem(label='Open Recent...')
        self._recent_submenu = Gtk.Menu()
        self._recent_menu_item.set_submenu(self._recent_submenu)
        repo_menu.append(self._recent_menu_item)
        self._update_recent_menu()

        repo_menu.append(Gtk.SeparatorMenuItem())

        explore_item = _create_menu_item('Explore Repository', 'explore')
        explore_item.connect('activate', lambda w: self.explore_repository())
        repo_menu.append(explore_item)

        rescan_item = _create_menu_item('Rescan', 'rescan')
        rescan_item.connect('activate', lambda w: self.rescan())
        repo_menu.append(rescan_item)

        repo_menu.append(Gtk.SeparatorMenuItem())

        # Visualize section
        branch = self._repo_vm.branch_name or 'main'
        self._visualize_branch_item = _create_menu_item(f"Visualize {branch}'s History")
        self._visualize_branch_item.connect('activate', lambda w: self._visualize_branch_history())
        repo_menu.append(self._visualize_branch_item)

        visualize_all_item = _create_menu_item('Visualize All Branches History')
        visualize_all_item.connect('activate', lambda w: self._visualize_all_history())
        repo_menu.append(visualize_all_item)

        repo_menu.append(Gtk.SeparatorMenuItem())

        # Database section
        db_stats_item = _create_menu_item('Database Statistics')
        db_stats_item.connect('activate', lambda w: self._show_database_statistics())
        repo_menu.append(db_stats_item)

        db_compress_item = _create_menu_item('Compress Database')
        db_compress_item.connect('activate', lambda w: self._compress_database())
        repo_menu.append(db_compress_item)

        db_verify_item = _create_menu_item('Verify Database')
        db_verify_item.connect('activate', lambda w: self._verify_database())
        repo_menu.append(db_verify_item)

        repo_menu.append(Gtk.SeparatorMenuItem())

        quit_item = _create_menu_item('Quit', 'quit')
        quit_item.connect('activate', lambda w: self.get_application().quit())
        repo_menu.append(quit_item)

        menubar.append(repo_item)

        # Branch menu
        branch_menu = Gtk.Menu()
        branch_item = Gtk.MenuItem(label='Branch')
        branch_item.set_submenu(branch_menu)

        create_branch_item = _create_menu_item('Create...')
        create_branch_item.connect('activate', lambda w: self._show_create_branch_dialog())
        branch_menu.append(create_branch_item)

        checkout_branch_item = _create_menu_item('Checkout...')
        checkout_branch_item.connect('activate', lambda w: self._show_checkout_branch_dialog())
        branch_menu.append(checkout_branch_item)

        rename_branch_item = _create_menu_item('Rename...')
        rename_branch_item.connect('activate', lambda w: self._show_rename_branch_dialog())
        branch_menu.append(rename_branch_item)

        delete_branch_item = _create_menu_item('Delete...')
        delete_branch_item.connect('activate', lambda w: self._show_delete_branch_dialog())
        branch_menu.append(delete_branch_item)

        branch_menu.append(Gtk.SeparatorMenuItem())

        reset_branch_item = _create_menu_item('Reset...')
        reset_branch_item.connect('activate', lambda w: self._show_reset_branch_dialog())
        branch_menu.append(reset_branch_item)

        menubar.append(branch_item)

        # Merge menu
        merge_menu = Gtk.Menu()
        merge_item = Gtk.MenuItem(label='Merge')
        merge_item.set_submenu(merge_menu)

        merge_branch_item = _create_menu_item('Merge...')
        merge_branch_item.connect('activate', lambda w: self._show_merge_dialog())
        merge_menu.append(merge_branch_item)

        rebase_item = _create_menu_item('Rebase...')
        rebase_item.connect('activate', lambda w: self._show_rebase_dialog())
        merge_menu.append(rebase_item)

        menubar.append(merge_item)

        # Remote menu
        remote_menu = Gtk.Menu()
        remote_item = Gtk.MenuItem(label='Remote')
        remote_item.set_submenu(remote_menu)

        list_remotes_item = _create_menu_item('List')
        list_remotes_item.connect('activate', lambda w: self._show_list_remotes_dialog())
        remote_menu.append(list_remotes_item)

        add_remote_item = _create_menu_item('Add...', 'add-remote')
        add_remote_item.connect('activate', lambda w: self.show_add_remote_dialog())
        remote_menu.append(add_remote_item)

        rename_remote_item = _create_menu_item('Rename...')
        rename_remote_item.connect('activate', lambda w: self.show_rename_remote_dialog())
        remote_menu.append(rename_remote_item)

        delete_remote_item = _create_menu_item('Delete...')
        delete_remote_item.connect('activate', lambda w: self.show_delete_remote_dialog())
        remote_menu.append(delete_remote_item)

        remote_menu.append(Gtk.SeparatorMenuItem())

        fetch_item = _create_menu_item('Fetch...', 'fetch')
        fetch_item.connect('activate', lambda w: self.show_fetch_dialog())
        remote_menu.append(fetch_item)

        pull_item = _create_menu_item('Pull...', 'pull')
        pull_item.connect('activate', lambda w: self.show_pull_dialog())
        remote_menu.append(pull_item)

        push_item = _create_menu_item('Push...', 'push')
        push_item.connect('activate', lambda w: self.show_push_dialog())
        remote_menu.append(push_item)

        menubar.append(remote_item)

        # Help menu
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label='Help')
        help_item.set_submenu(help_menu)

        git_docs_item = _create_menu_item('Online Git Documentation')
        git_docs_item.connect('activate', lambda w: self._open_git_documentation())
        help_menu.append(git_docs_item)

        ssh_key_item = _create_menu_item('Show SSH Key')
        ssh_key_item.connect('activate', lambda w: self._show_ssh_key())
        help_menu.append(ssh_key_item)

        help_menu.append(Gtk.SeparatorMenuItem())

        about_item = _create_menu_item('About', 'about')
        about_item.connect('activate', lambda w: self._show_about())
        help_menu.append(about_item)

        menubar.append(help_item)

        return menubar

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

    def _on_stage_line(self, widget, file_path, line):
        self._diff_vm.stage_line(file_path, line)

    def _on_unstage_hunk(self, widget, file_path, line):
        self._diff_vm.unstage_hunk(file_path, line)

    def _on_unstage_line(self, widget, file_path, line):
        self._diff_vm.unstage_line(file_path, line)

    def _on_revert_hunk(self, widget, file_path, line):
        if self._confirm_revert('Revert Hunk?',
                                f'This will discard changes in the selected hunk from:\n{file_path}\n\n'
                                'This action cannot be undone.',
                                'Revert Hunk'):
            self._diff_vm.revert_hunk(file_path, line)

    def _on_revert_line(self, widget, file_path, line):
        if self._confirm_revert('Revert Lines?',
                                f'This will discard the selected line change from:\n{file_path}\n\n'
                                'This action cannot be undone.',
                                'Revert Lines'):
            self._diff_vm.revert_line(file_path, line)

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

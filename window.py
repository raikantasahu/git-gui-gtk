"""Main application window."""

import os
from enum import Enum, auto

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib


import gitops


class MessageType(Enum):
    """Message types for status display."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
from cache import RecentRepositoryList
from gitops import FileChange, FileStatus
from widgets import FileListWidget, DiffView, CommitArea
from actions import get_action_shortcut
import dialogs


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

        self._repo = None
        self._repo_path = None
        self._current_file = None
        self._current_diff_file = None
        self._current_diff_staged = False

        self._setup_ui()

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
        self._visualize_branch_item = _create_menu_item('Visualize main\'s History')
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

    def _open_git_documentation(self):
        """Open Git documentation in default web browser."""
        import webbrowser
        webbrowser.open('https://git-scm.com/doc')

    def _show_ssh_key(self):
        """Show the user's SSH public key."""
        dialogs.show_ssh_key_dialog(self, on_status=self._set_status)

    def _show_about(self):
        """Show the about dialog."""
        dialogs.show_about_dialog(self)

    def open_repository(self, path):
        """Open a git repository."""
        self._repo, self._repo_path = gitops.open_repository(path)
        if self._repo:
            self.set_title('Git GUI - ' + gitops.get_repo_name(self._repo_path))
            self._update_branch_label()
            self.rescan()
            self._set_status('Opened repository: ' + path)
            # Add to recent repositories
            RecentRepositoryList.add_recent(self._repo_path)
            self._update_recent_menu()
        else:
            self._set_status('Not a git repository: ' + path, MessageType.WARNING)
            self._clear_ui()

    def _clear_ui(self):
        """Clear all UI elements."""
        self._unstaged_list.set_files([])
        self._staged_list.set_files([])
        self._diff_view.clear()
        self._branch_label.set_text('')
        self._commit_area.set_commit_sensitive(False)
        self._current_diff_file = None

    def explore_repository(self):
        """Open repository root in default file browser."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            subprocess.Popen(['xdg-open', self._repo_path])
        except Exception as e:
            self._show_error('Explore Repository', f'Failed to open file browser: {e}')

    def _visualize_branch_history(self):
        """Open gitk to visualize current branch history."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            branch = gitops.get_current_branch(self._repo)
            subprocess.Popen(['gitk', branch], cwd=self._repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _visualize_all_history(self):
        """Open gitk to visualize all branches history."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        try:
            import subprocess
            subprocess.Popen(['gitk', '--all'], cwd=self._repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _show_database_statistics(self):
        """Show git database statistics."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        dialogs.show_database_statistics_dialog(self, self._repo)

    def _compress_database(self):
        """Compress git database (git gc)."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        self._set_status('Compressing database...')
        dialogs.show_compress_database_dialog(
            self, self._repo,
            on_complete=lambda success, msg: self._set_status(
                msg, MessageType.INFO if success else MessageType.ERROR
            )
        )

    def _verify_database(self):
        """Verify git database (git fsck)."""
        if not self._repo_path:
            self._set_status('No repository open', MessageType.WARNING)
            return
        self._set_status('Verifying database...')
        dialogs.show_verify_database_dialog(
            self, self._repo,
            on_complete=lambda success, msg: self._set_status(
                'Database verification completed' if success else 'Database verification found issues'
            )
        )

    def _update_branch_label(self):
        """Update the branch indicator and related menu items."""
        branch = gitops.get_current_branch(self._repo)
        self._branch_label.set_text('  ' + branch if branch else '')
        # Update visualize menu item
        if branch:
            self._visualize_branch_item.set_label(f"Visualize {branch}'s History")

    def rescan(self):
        """Rescan the repository for changes."""
        if not self._repo is not None:
            return

        unstaged, staged = gitops.get_status(self._repo)
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
                self._current_diff_file = None

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
            success, message = gitops.revert_file(self._repo,file_change.path)
            self._set_status(message)
            self.rescan()

    def _on_stage_hunk(self, widget, file_path, line):
        """Handle stage hunk request from diff view."""
        success, message = gitops.stage_hunk(self._repo, file_path, line)
        self._set_status(message)
        if success:
            self.rescan()

    def _on_stage_line(self, widget, file_path, line):
        """Handle stage line request from diff view."""
        success, message = gitops.stage_line(self._repo, file_path, line)
        self._set_status(message)
        if success:
            self.rescan()

    def _on_unstage_hunk(self, widget, file_path, line):
        """Handle unstage hunk request from diff view."""
        success, message = gitops.unstage_hunk(self._repo, file_path, line)
        self._set_status(message)
        if success:
            self.rescan()

    def _on_unstage_line(self, widget, file_path, line):
        """Handle unstage line request from diff view."""
        success, message = gitops.unstage_line(self._repo, file_path, line)
        self._set_status(message)
        if success:
            self.rescan()

    def _on_revert_hunk(self, widget, file_path, line):
        """Handle revert hunk request from diff view."""
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text='Revert Hunk?'
        )
        dialog.format_secondary_text(
            f'This will discard changes in the selected hunk from:\n{file_path}\n\n'
            'This action cannot be undone.'
        )
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Revert Hunk', Gtk.ResponseType.OK)

        revert_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        revert_btn.get_style_context().add_class('destructive-action')

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            success, message = gitops.revert_hunk(self._repo, file_path, line)
            self._set_status(message)
            if success:
                self.rescan()

    def _on_revert_line(self, widget, file_path, line):
        """Handle revert line request from diff view."""
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text='Revert Line?'
        )
        dialog.format_secondary_text(
            f'This will discard the selected line change from:\n{file_path}\n\n'
            'This action cannot be undone.'
        )
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Revert Line', Gtk.ResponseType.OK)

        revert_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        revert_btn.get_style_context().add_class('destructive-action')

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            success, message = gitops.revert_line(self._repo, file_path, line)
            self._set_status(message)
            if success:
                self.rescan()

    def _on_context_changed(self, widget, context_lines):
        """Handle context lines change from diff view."""
        if hasattr(self, '_current_diff_file') and self._current_diff_file:
            self._show_diff(self._current_diff_file, self._current_diff_staged)
            self._set_status(f'Context lines: {context_lines}')

    def _show_diff(self, file_change, staged):
        """Show diff for a file."""
        context_lines = self._diff_view.get_context_lines()
        diff = gitops.get_diff(
            self._repo, self._repo_path, file_change.path,
            staged=staged, context_lines=context_lines
        )
        status = self._get_file_status_text(file_change, staged)
        self._diff_view.set_diff(diff, file_change.path, status)
        is_untracked = file_change.status == FileStatus.UNTRACKED
        self._diff_view.set_file_info(file_change.path, staged, is_untracked)
        # Store current file info for context refresh
        self._current_diff_file = file_change
        self._current_diff_staged = staged

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
        if gitops.stage_file(self._repo,file_change.path):
            self._set_status('Staged: ' + file_change.path)
            self.rescan()
        else:
            self._set_status('Failed to stage: ' + file_change.path, MessageType.ERROR)

    def _unstage_file(self, file_change):
        """Unstage a single file."""
        if gitops.unstage_file(self._repo,file_change.path):
            self._set_status('Unstaged: ' + file_change.path)
            self.rescan()
        else:
            self._set_status('Failed to unstage: ' + file_change.path, MessageType.ERROR)

    def stage_selected(self):
        """Stage the currently selected file."""
        file_change = self._unstaged_list.get_selected_file()
        if file_change:
            self._stage_file(file_change)

    def unstage_selected(self):
        """Unstage the currently selected file."""
        file_change = self._staged_list.get_selected_file()
        if file_change:
            self._unstage_file(file_change)

    def revert_selected(self):
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
                success, message = gitops.revert_file(self._repo,file_change.path)
                self._set_status(message)
                self.rescan()

    def stage_all(self):
        """Stage all unstaged files."""
        if gitops.stage_all(self._repo):
            self._set_status('Staged all changes')
            self.rescan()
        else:
            self._set_status('Failed to stage all changes', MessageType.ERROR)

    def unstage_all(self):
        """Unstage all staged files."""
        if gitops.unstage_all(self._repo):
            self._set_status('Unstaged all changes')
            self.rescan()
        else:
            self._set_status('Failed to unstage all changes', MessageType.ERROR)

    def _on_commit_requested(self, widget, message, amend, sign_off):
        """Handle commit request from commit area."""
        self.commit(message, amend, sign_off)

    def _on_amend_toggled(self, widget, amend_enabled):
        """Handle amend checkbox toggle."""
        if amend_enabled:
            # Load last commit message when entering amend mode
            last_msg = gitops.get_last_commit_message(self._repo)
            self._commit_area.set_message(last_msg)
            # Show files from last commit in staged area
            last_commit_files = gitops.get_last_commit_files(self._repo)
            # Merge with currently staged files
            _, currently_staged = gitops.get_status(self._repo)
            # Combine: last commit files + any new staged files not in last commit
            staged_paths = {f.path for f in last_commit_files}
            for f in currently_staged:
                if f.path not in staged_paths:
                    last_commit_files.append(f)
            self._staged_list.set_files(last_commit_files)
            # Enable commit button for amend even if no staged changes
            self._commit_area.set_commit_sensitive(True)
        else:
            # Clear message when leaving amend mode
            self._commit_area.clear_message()
            # Rescan to restore normal view
            self.rescan()

    def commit(self, message=None, amend=None, sign_off=None):
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

        success, result_msg = gitops.commit(self._repo,message, amend=amend, sign_off=sign_off)
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
            last_msg = gitops.get_last_commit_message(self._repo)
            self._commit_area.set_message(last_msg)

    def show_push_dialog(self):
        """Show dialog to push to a remote."""
        result = dialogs.show_push_dialog(self, self._repo)
        if result:
            remote, branch, force, tags = result
            self._do_push(remote, branch, force, tags)

    def _do_push(self, remote_name, branch_name=None, force=False, tags=False):
        """Perform push to the specified remote."""
        branch_display = f'{remote_name}/{branch_name}' if branch_name else remote_name
        self._set_status(f'Pushing to {branch_display}...')

        def push_async():
            success, message = gitops.push(self._repo,remote_name, branch_name, force, tags)
            GLib.idle_add(self._on_push_complete, success, message)

        import threading
        thread = threading.Thread(target=push_async)
        thread.daemon = True
        thread.start()

    def _on_push_complete(self, success, message):
        """Handle push completion."""
        self._set_status(message)
        if not success:
            self._show_error('Push Error', message)

    def show_pull_dialog(self):
        """Show dialog to pull from a remote."""
        result = dialogs.show_pull_dialog(self, self._repo)
        if result:
            remote, branch, ff_only, rebase = result
            self._do_pull(remote, branch, ff_only, rebase)

    def _do_pull(self, remote_name, branch_name=None, ff_only=False, rebase=False):
        """Perform pull from the specified remote."""
        branch_display = f'{remote_name}/{branch_name}' if branch_name else remote_name
        self._set_status(f'Pulling from {branch_display}...')

        def pull_async():
            success, message = gitops.pull(self._repo,remote_name, branch_name, ff_only, rebase)
            GLib.idle_add(self._on_pull_complete, success, message)

        import threading
        thread = threading.Thread(target=pull_async)
        thread.daemon = True
        thread.start()

    def _on_pull_complete(self, success, message):
        """Handle pull completion."""
        self._set_status(message)
        if success:
            self.rescan()
        else:
            self._show_error('Pull Error', message)

    def show_fetch_dialog(self):
        """Show dialog to fetch from a remote."""
        result = dialogs.show_fetch_dialog(self, self._repo)
        if result:
            self._do_fetch(result)

    def _do_fetch(self, remote_name):
        """Perform fetch from the specified remote."""
        self._set_status(f'Fetching from {remote_name}...')

        def fetch_async():
            success, message = gitops.fetch(self._repo,remote_name)
            GLib.idle_add(self._on_fetch_complete, success, message)

        import threading
        thread = threading.Thread(target=fetch_async)
        thread.daemon = True
        thread.start()

    def _on_fetch_complete(self, success, message):
        """Handle fetch completion."""
        self._set_status(message)
        if not success:
            self._show_error('Fetch Error', message)

    def _set_status(self, message, msg_type=MessageType.INFO):
        """Set status bar message or show dialog for long messages.

        Args:
            message: The status message to display
            msg_type: MessageType (INFO, WARNING, or ERROR)
        """
        # Maximum characters that fit reasonably in the status bar
        MAX_STATUS_LENGTH = 100

        if len(message) > MAX_STATUS_LENGTH:
            # Show dialog for long messages
            title_map = {
                MessageType.INFO: 'Information',
                MessageType.WARNING: 'Warning',
                MessageType.ERROR: 'Error',
            }
            title = title_map.get(msg_type, 'Information')
            self._show_message_dialog(title, message, msg_type)
            # Show truncated message in status bar
            truncated = message[:MAX_STATUS_LENGTH - 3] + '...'
            self._status_bar.set_text(truncated)
        else:
            self._status_bar.set_text(message)

    def _show_message_dialog(self, title, message, msg_type=MessageType.INFO):
        """Show a message dialog based on message type.

        Args:
            title: Dialog title
            message: The full message to display
            msg_type: MessageType (INFO, WARNING, or ERROR)
        """
        type_map = {
            MessageType.INFO: Gtk.MessageType.INFO,
            MessageType.WARNING: Gtk.MessageType.WARNING,
            MessageType.ERROR: Gtk.MessageType.ERROR,
        }
        gtk_type = type_map.get(msg_type, Gtk.MessageType.INFO)

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=gtk_type,
            buttons=Gtk.ButtonsType.NONE,
            text=title
        )
        dialog.format_secondary_text(message)
        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        dialog.run()
        dialog.destroy()

    def _show_error(self, title, message):
        """Show an error dialog."""
        self._show_message_dialog(title, message, MessageType.ERROR)

    def _show_status_dialog(self, title, message, success):
        """Show a status dialog for operation results."""
        msg_type = MessageType.INFO if success else MessageType.ERROR
        self._show_message_dialog(title, message, msg_type)

    def _show_create_branch_dialog(self):
        """Show dialog to create a new branch."""
        result = dialogs.show_create_branch_dialog(self, self._repo)
        if result:
            branch_name, base, checkout = result
            success, message = gitops.create_branch(
                self._repo, branch_name, start_point=base, checkout=checkout
            )
            self._set_status(message)
            if success:
                self._update_branch_label()
            else:
                self._show_error('Create Branch Error', message)

    def _show_checkout_branch_dialog(self):
        """Show dialog to checkout a branch."""
        result = dialogs.show_checkout_branch_dialog(self, self._repo)
        if result:
            success, message = gitops.checkout_branch(self._repo,result)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            else:
                self._show_error('Checkout Branch Error', message)

    def _show_rename_branch_dialog(self):
        """Show dialog to rename a branch."""
        result = dialogs.show_rename_branch_dialog(self, self._repo)
        if result:
            old_name, new_name = result
            success, message = gitops.rename_branch(self._repo,old_name, new_name)
            self._set_status(message)
            if success:
                self._update_branch_label()
            else:
                self._show_error('Rename Branch Error', message)

    def _show_delete_branch_dialog(self):
        """Show dialog to delete a branch."""
        result = dialogs.show_delete_branch_dialog(self, self._repo)
        if result:
            branch_name, force = result
            success, message = gitops.delete_branch(self._repo,branch_name, force=force)
            self._set_status(message)
            if not success:
                self._show_error('Delete Branch Error', message)

    def _show_list_remotes_dialog(self):
        """Show dialog listing all remotes."""
        dialogs.show_list_remotes_dialog(self, self._repo)

    def show_add_remote_dialog(self):
        """Show dialog to add a new remote."""
        result = dialogs.show_add_remote_dialog(self, self._repo)
        if result:
            name, url, fetch_after = result
            success, message = gitops.add_remote(self._repo,name, url)
            self._set_status(message)
            if not success:
                self._show_error('Add Remote Error', message)
            elif fetch_after:
                self._do_fetch(name)

    def show_rename_remote_dialog(self):
        """Show dialog to rename a remote."""
        result = dialogs.show_rename_remote_dialog(self, self._repo)
        if result:
            old_name, new_name = result
            success, message = gitops.rename_remote(self._repo,old_name, new_name)
            self._set_status(message)
            if not success:
                self._show_error('Rename Remote Error', message)

    def show_delete_remote_dialog(self):
        """Show dialog to delete a remote."""
        result = dialogs.show_delete_remote_dialog(self, self._repo)
        if result:
            success, message = gitops.delete_remote(self._repo,result)
            self._set_status(message)
            if not success:
                self._show_error('Delete Remote Error', message)

    def _show_reset_branch_dialog(self):
        """Show dialog to reset current branch."""
        result = dialogs.show_reset_branch_dialog(self, self._repo)
        if result:
            target, mode = result
            success, message = gitops.reset_branch(self._repo,target, mode=mode)
            self._set_status(message)
            if success:
                self.rescan()
            else:
                self._show_error('Reset Branch Error', message)

    def _show_merge_dialog(self):
        """Show dialog to merge a branch."""
        result = dialogs.show_merge_dialog(self, self._repo)
        if result:
            branch, strategy = result
            success, message = gitops.merge_branch(self._repo, branch, strategy=strategy)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            self._show_status_dialog('Merge', message, success)

    def _show_rebase_dialog(self):
        """Show dialog to rebase current branch."""
        result = dialogs.show_rebase_dialog(self, self._repo)
        if result:
            success, message = gitops.rebase_branch(self._repo,result)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            self._show_status_dialog('Rebase', message, success)

    def show_open_dialog(self):
        """Show dialog to open a repository."""
        result = dialogs.show_open_repository_dialog(self, self._repo_path)
        if result:
            self.open_repository(result)

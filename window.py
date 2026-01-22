"""Main application window."""

import os

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib

from git_operations import GitOperations, FileChange, FileStatus
from widgets import FileListWidget, DiffView, CommitArea
from actions import get_action_shortcut


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

        self._git = GitOperations()
        self._current_file = None

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
        right_paned.pack1(self._diff_view, resize=True, shrink=False)

        # Commit area (bottom)
        self._commit_area = CommitArea()
        self._commit_area.set_size_request(-1, 180)
        self._commit_area.connect('commit-requested', self._on_commit_requested)
        self._commit_area.connect('push-requested', lambda w: self.push())
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

        remote_menu.append(Gtk.SeparatorMenuItem())

        fetch_item = _create_menu_item('Fetch', 'fetch')
        fetch_item.connect('activate', lambda w: self.fetch())
        remote_menu.append(fetch_item)

        pull_item = _create_menu_item('Pull', 'pull')
        pull_item.connect('activate', lambda w: self.pull())
        remote_menu.append(pull_item)

        push_item = _create_menu_item('Push', 'push')
        push_item.connect('activate', lambda w: self.push())
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

    def _open_git_documentation(self):
        """Open Git documentation in default web browser."""
        import webbrowser
        webbrowser.open('https://git-scm.com/doc')

    def _show_ssh_key(self):
        """Show the user's SSH public key."""
        ssh_key = None
        ssh_key_path = None

        # Check common SSH key locations
        ssh_dir = os.path.expanduser('~/.ssh')
        key_files = ['id_ed25519.pub', 'id_rsa.pub', 'id_ecdsa.pub', 'id_dsa.pub']

        for key_file in key_files:
            path = os.path.join(ssh_dir, key_file)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        ssh_key = f.read().strip()
                    ssh_key_path = path
                    break
                except Exception:
                    continue

        dialog = Gtk.Dialog(
            title='Your OpenSSH Public Key',
            transient_for=self,
            modal=True
        )
        dialog.set_default_size(600, 200)

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        if ssh_key:
            path_label = Gtk.Label(label=f'Public key from: {ssh_key_path}')
            path_label.set_xalign(0)
            content.pack_start(path_label, False, False, 0)

            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_vexpand(True)

            text_view = Gtk.TextView()
            text_view.set_editable(False)
            text_view.set_wrap_mode(Gtk.WrapMode.CHAR)
            text_view.set_monospace(True)
            text_view.get_buffer().set_text(ssh_key)
            scrolled.add(text_view)
            content.pack_start(scrolled, True, True, 0)
        else:
            no_key_label = Gtk.Label(label='No SSH public key found.')
            no_key_label.set_xalign(0)
            content.pack_start(no_key_label, False, False, 0)

        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)

        if ssh_key:
            dialog.add_button('Copy to Clipboard', Gtk.ResponseType.APPLY)
        else:
            dialog.add_button('Generate Key', Gtk.ResponseType.YES)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)

        dialog.show_all()

        # Handle responses in a loop so Copy doesn't close the dialog
        while True:
            response = dialog.run()
            if response == Gtk.ResponseType.APPLY and ssh_key:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(ssh_key, -1)
                clipboard.store()
                self._set_status('SSH key copied to clipboard')
            elif response == Gtk.ResponseType.YES:
                dialog.destroy()
                self._generate_ssh_key()
                return
            else:
                break

        dialog.destroy()

    def _generate_ssh_key(self):
        """Show dialog to generate a new SSH key."""
        dialog = Gtk.Dialog(
            title='Generate SSH Key',
            transient_for=self,
            modal=True
        )
        dialog.set_default_size(450, 250)

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(8)

        # Key type
        type_label = Gtk.Label(label='Key type:')
        type_label.set_xalign(0)
        content.pack_start(type_label, False, False, 0)

        type_combo = Gtk.ComboBoxText()
        type_combo.append('ed25519', 'Ed25519 (recommended)')
        type_combo.append('rsa', 'RSA (4096 bits)')
        type_combo.append('ecdsa', 'ECDSA')
        type_combo.set_active(0)
        content.pack_start(type_combo, False, False, 0)

        # Comment/Email
        comment_label = Gtk.Label(label='Comment (usually your email):')
        comment_label.set_xalign(0)
        content.pack_start(comment_label, False, False, 0)

        comment_entry = Gtk.Entry()
        comment_entry.set_placeholder_text('your_email@example.com')
        content.pack_start(comment_entry, False, False, 0)

        # Passphrase
        pass_label = Gtk.Label(label='Passphrase (optional, leave empty for no passphrase):')
        pass_label.set_xalign(0)
        content.pack_start(pass_label, False, False, 0)

        pass_entry = Gtk.Entry()
        pass_entry.set_visibility(False)
        pass_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        content.pack_start(pass_entry, False, False, 0)

        # Confirm passphrase
        confirm_label = Gtk.Label(label='Confirm passphrase:')
        confirm_label.set_xalign(0)
        content.pack_start(confirm_label, False, False, 0)

        confirm_entry = Gtk.Entry()
        confirm_entry.set_visibility(False)
        confirm_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        content.pack_start(confirm_entry, False, False, 0)

        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Generate', Gtk.ResponseType.OK)

        dialog.show_all()

        while True:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                key_type = type_combo.get_active_id()
                comment = comment_entry.get_text().strip()
                passphrase = pass_entry.get_text()
                confirm = confirm_entry.get_text()

                if passphrase != confirm:
                    self._show_error('Generate SSH Key', 'Passphrases do not match.')
                    continue

                dialog.destroy()

                # Generate the key
                ssh_dir = os.path.expanduser('~/.ssh')
                if not os.path.exists(ssh_dir):
                    os.makedirs(ssh_dir, mode=0o700)

                key_file = os.path.join(ssh_dir, f'id_{key_type}')

                if os.path.exists(key_file):
                    self._show_error('Generate SSH Key', f'Key file already exists: {key_file}')
                    return

                try:
                    import subprocess
                    cmd = ['ssh-keygen', '-t', key_type, '-f', key_file, '-N', passphrase]
                    if key_type == 'rsa':
                        cmd.extend(['-b', '4096'])
                    if comment:
                        cmd.extend(['-C', comment])

                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        self._set_status('SSH key generated successfully')
                        # Show the new key
                        self._show_ssh_key()
                    else:
                        self._show_error('Generate SSH Key', f'Failed to generate key:\n{result.stderr}')
                except Exception as e:
                    self._show_error('Generate SSH Key', f'Failed to generate key: {e}')
                return
            else:
                break

        dialog.destroy()

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

    def explore_repository(self):
        """Open repository root in default file browser."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return
        try:
            import subprocess
            subprocess.Popen(['xdg-open', self._git.repo_path])
        except Exception as e:
            self._show_error('Explore Repository', f'Failed to open file browser: {e}')

    def _visualize_branch_history(self):
        """Open gitk to visualize current branch history."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return
        try:
            import subprocess
            branch = self._git.get_current_branch()
            subprocess.Popen(['gitk', branch], cwd=self._git.repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _visualize_all_history(self):
        """Open gitk to visualize all branches history."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return
        try:
            import subprocess
            subprocess.Popen(['gitk', '--all'], cwd=self._git.repo_path)
        except FileNotFoundError:
            self._show_error('Visualize History', 'gitk is not installed. Please install gitk to visualize history.')
        except Exception as e:
            self._show_error('Visualize History', f'Failed to open gitk: {e}')

    def _show_database_statistics(self):
        """Show git database statistics."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return
        success, output = self._git.get_database_statistics()
        if success:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text='Database Statistics'
            )
            dialog.format_secondary_text(output)
            # Add Close button with padding, not full width
            button_box = dialog.get_action_area()
            button_box.set_layout(Gtk.ButtonBoxStyle.END)
            button_box.set_margin_end(12)
            button_box.set_margin_bottom(12)
            dialog.add_button('Close', Gtk.ResponseType.CLOSE)
            dialog.run()
            dialog.destroy()
        else:
            self._show_error('Database Statistics', output)

    def _compress_database(self):
        """Compress git database (git gc)."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return

        # Create progress dialog
        self._compress_dialog = Gtk.Dialog(
            title='Compress Database',
            transient_for=self,
            modal=True
        )
        self._compress_dialog.set_default_size(350, 120)
        self._compress_dialog.set_deletable(False)

        content = self._compress_dialog.get_content_area()
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(12)
        content.set_spacing(12)

        self._compress_label = Gtk.Label(label='Compressing database...')
        self._compress_label.set_xalign(0)
        content.pack_start(self._compress_label, False, False, 0)

        self._compress_spinner = Gtk.Spinner()
        self._compress_spinner.start()
        content.pack_start(self._compress_spinner, False, False, 0)

        self._compress_dialog.show_all()

        self._set_status('Compressing database...')

        def do_compress():
            success, message = self._git.compress_database()
            GLib.idle_add(self._on_compress_complete, success, message)

        import threading
        thread = threading.Thread(target=do_compress)
        thread.daemon = True
        thread.start()

    def _on_compress_complete(self, success, message):
        """Handle compress completion."""
        self._set_status(message)

        # Update dialog
        self._compress_spinner.stop()
        self._compress_spinner.hide()

        if success:
            self._compress_label.set_text('Database compressed successfully.')
        else:
            self._compress_label.set_text(f'Compression failed: {message}')

        # Add Close button
        button_box = self._compress_dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        self._compress_dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        self._compress_dialog.set_deletable(True)
        button_box.show_all()

        self._compress_dialog.run()
        self._compress_dialog.destroy()

    def _verify_database(self):
        """Verify git database (git fsck)."""
        if not self._git.repo_path:
            self._set_status('No repository open')
            return
        self._set_status('Verifying database...')

        def do_verify():
            success, message = self._git.verify_database()
            GLib.idle_add(self._on_verify_complete, success, message)

        import threading
        thread = threading.Thread(target=do_verify)
        thread.daemon = True
        thread.start()

    def _on_verify_complete(self, success, message):
        """Handle verify completion."""
        if success:
            self._set_status('Database verification completed')
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text='Verify Database'
            )
            dialog.format_secondary_text(message if message else 'No errors found.')
            # Add Close button with padding, not full width
            button_box = dialog.get_action_area()
            button_box.set_layout(Gtk.ButtonBoxStyle.END)
            button_box.set_margin_end(12)
            button_box.set_margin_bottom(12)
            dialog.add_button('Close', Gtk.ResponseType.CLOSE)
            dialog.run()
            dialog.destroy()
        else:
            self._set_status('Database verification found issues')
            self._show_error('Verify Database', message)

    def _update_branch_label(self):
        """Update the branch indicator and related menu items."""
        branch = self._git.get_current_branch()
        self._branch_label.set_text('  ' + branch if branch else '')
        # Update visualize menu item
        if branch:
            self._visualize_branch_item.set_label(f"Visualize {branch}'s History")

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
        self.commit(message, amend, sign_off)

    def _on_amend_toggled(self, widget, amend_enabled):
        """Handle amend checkbox toggle."""
        if amend_enabled:
            # Load last commit message when entering amend mode
            last_msg = self._git.get_last_commit_message()
            self._commit_area.set_message(last_msg)
            # Show files from last commit in staged area
            last_commit_files = self._git.get_last_commit_files()
            # Merge with currently staged files
            _, currently_staged = self._git.get_status()
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

    def push(self):
        """Push to remote."""
        self._set_status('Pushing...')

        def push_async():
            success, message = self._git.push()
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

    def pull(self):
        """Pull from remote."""
        self._set_status('Pulling...')

        def pull_async():
            success, message = self._git.pull()
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

    def fetch(self):
        """Fetch from remote."""
        self._set_status('Fetching...')

        def fetch_async():
            success, message = self._git.fetch()
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

    def _set_status(self, message):
        """Set status bar message."""
        self._status_bar.set_text(message)

    def _show_error(self, title, message):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
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

    def _show_status_dialog(self, title, message, success):
        """Show a status dialog for operation results."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
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

    def show_add_remote_dialog(self):
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

    def _show_merge_dialog(self):
        """Show dialog to merge a branch."""
        branches = self._git.get_branches()
        current_branch = self._git.get_current_branch()
        # Filter out current branch
        branches = [b for b in branches if b != current_branch]

        if not branches:
            self._show_error('Merge', 'No other branches available to merge.')
            return

        dialog = Gtk.Dialog(
            title='Merge Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            'Merge', Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        info_label = Gtk.Label(label=f'Merge into: {current_branch}')
        info_label.set_xalign(0)
        content.pack_start(info_label, False, False, 0)

        label = Gtk.Label(label='Select branch to merge:')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        combo = Gtk.ComboBoxText()
        for branch in branches:
            combo.append_text(branch)
        combo.set_active(0)
        content.pack_start(combo, False, False, 0)

        # Options
        no_ff_check = Gtk.CheckButton(label='No fast-forward (always create merge commit)')
        content.pack_start(no_ff_check, False, False, 0)

        squash_check = Gtk.CheckButton(label='Squash commits')
        content.pack_start(squash_check, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        selected_branch = combo.get_active_text()
        no_ff = no_ff_check.get_active()
        squash = squash_check.get_active()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and selected_branch:
            success, message = self._git.merge_branch(selected_branch, no_ff=no_ff, squash=squash)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            self._show_status_dialog('Merge', message, success)

    def _show_rebase_dialog(self):
        """Show dialog to rebase current branch."""
        branches = self._git.get_branches()
        current_branch = self._git.get_current_branch()
        # Filter out current branch
        branches = [b for b in branches if b != current_branch]

        if not branches:
            self._show_error('Rebase', 'No other branches available to rebase onto.')
            return

        dialog = Gtk.Dialog(
            title='Rebase Branch',
            transient_for=self,
            modal=True
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            'Rebase', Gtk.ResponseType.OK
        )

        # Make rebase button look cautionary
        rebase_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        rebase_btn.get_style_context().add_class('suggested-action')

        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_spacing(6)

        info_label = Gtk.Label(label=f'Rebase branch: {current_branch}')
        info_label.set_xalign(0)
        content.pack_start(info_label, False, False, 0)

        label = Gtk.Label(label='Rebase onto:')
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        combo = Gtk.ComboBoxText()
        for branch in branches:
            combo.append_text(branch)
        combo.set_active(0)
        content.pack_start(combo, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        response = dialog.run()
        selected_branch = combo.get_active_text()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and selected_branch:
            success, message = self._git.rebase_branch(selected_branch)
            self._set_status(message)
            if success:
                self._update_branch_label()
                self.rescan()
            self._show_status_dialog('Rebase', message, success)

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

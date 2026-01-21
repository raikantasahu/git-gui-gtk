"""File list widget for displaying staged/unstaged files."""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject

from git_operations import FileChange, FileStatus


class FileListWidget(Gtk.Box):
    """Widget displaying a list of files with their status."""

    __gtype_name__ = 'FileListWidget'

    __gsignals__ = {
        'file-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'file-revert-requested': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, title, staged=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.staged = staged
        self._files = []

        # Header with title and action buttons
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_margin_start(6)
        header.set_margin_end(6)
        header.set_margin_top(6)
        header.set_margin_bottom(6)

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        header.pack_start(title_label, True, True, 0)

        # Count label
        self._count_label = Gtk.Label(label='0')
        self._count_label.get_style_context().add_class('dim-label')
        header.pack_start(self._count_label, False, False, 0)

        # Stage/Unstage all button
        if staged:
            btn = Gtk.Button()
            btn_icon = Gtk.Image.new_from_icon_name('list-remove-symbolic', Gtk.IconSize.BUTTON)
            btn.add(btn_icon)
            btn.set_tooltip_text('Unstage All')
            btn.connect('clicked', lambda b: self.emit('file-activated', None))
        else:
            btn = Gtk.Button()
            btn_icon = Gtk.Image.new_from_icon_name('list-add-symbolic', Gtk.IconSize.BUTTON)
            btn.add(btn_icon)
            btn.set_tooltip_text('Stage All')
            btn.connect('clicked', lambda b: self.emit('file-activated', None))
        header.pack_start(btn, False, False, 0)

        self.pack_start(header, False, False, 0)

        # Scrolled window for the list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create list store: status_label, path, index
        self._store = Gtk.ListStore(str, str, int)

        # Create tree view
        self._tree_view = Gtk.TreeView(model=self._store)
        self._tree_view.set_headers_visible(False)
        self._tree_view.set_enable_search(True)
        self._tree_view.set_search_column(1)

        # Status column
        status_renderer = Gtk.CellRendererText()
        status_renderer.set_property('family', 'monospace')
        status_renderer.set_property('width-chars', 2)
        status_column = Gtk.TreeViewColumn('Status', status_renderer, text=0)
        status_column.set_cell_data_func(status_renderer, self._status_cell_data_func)
        self._tree_view.append_column(status_column)

        # Path column
        path_renderer = Gtk.CellRendererText()
        path_renderer.set_property('ellipsize', 2)  # PANGO_ELLIPSIZE_MIDDLE
        path_column = Gtk.TreeViewColumn('Path', path_renderer, text=1)
        path_column.set_expand(True)
        self._tree_view.append_column(path_column)

        # Selection handling
        selection = self._tree_view.get_selection()
        selection.connect('changed', self._on_selection_changed)

        # Double-click handling
        self._tree_view.connect('row-activated', self._on_row_activated)

        # Context menu for unstaged files
        if not staged:
            self._context_menu = self._create_context_menu()
            self._tree_view.connect('button-press-event', self._on_button_press)

        scrolled.add(self._tree_view)
        self.pack_start(scrolled, True, True, 0)

        self.show_all()

    def _status_cell_data_func(self, column, cell, model, iter, data=None):
        """Set cell color based on status."""
        status_label = model.get_value(iter, 0)
        idx = model.get_value(iter, 2)

        if idx < len(self._files):
            status = self._files[idx].status
            if status == FileStatus.ADDED or status == FileStatus.UNTRACKED:
                cell.set_property('foreground', '#26a269')  # Green
            elif status == FileStatus.DELETED:
                cell.set_property('foreground', '#c01c28')  # Red
            elif status == FileStatus.MODIFIED:
                cell.set_property('foreground', '#1c71d8')  # Blue
            elif status == FileStatus.UNMERGED:
                cell.set_property('foreground', '#e5a50a')  # Yellow
            else:
                cell.set_property('foreground', None)
        else:
            cell.set_property('foreground', None)

    def _on_selection_changed(self, selection):
        """Handle selection change."""
        model, iter = selection.get_selected()
        if iter:
            idx = model.get_value(iter, 2)
            if idx < len(self._files):
                self.emit('file-selected', self._files[idx])

    def _on_row_activated(self, tree_view, path, column):
        """Handle row double-click activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        idx = model.get_value(iter, 2)
        if idx < len(self._files):
            self.emit('file-activated', self._files[idx])

    def _create_context_menu(self):
        """Create context menu for unstaged files."""
        menu = Gtk.Menu()

        # Stage to Commit
        stage_item = Gtk.MenuItem(label='Stage to Commit')
        stage_item.connect('activate', self._on_context_stage)
        menu.append(stage_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # Revert Changes
        revert_item = Gtk.MenuItem(label='Revert Changes')
        revert_item.connect('activate', self._on_context_revert)
        menu.append(revert_item)

        menu.show_all()
        return menu

    def _on_button_press(self, tree_view, event):
        """Handle button press for context menu."""
        if event.button == 3:  # Right click
            # Select the row under the cursor
            path_info = tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, column, x, y = path_info
                tree_view.get_selection().select_path(path)
                self._context_menu.popup_at_pointer(event)
                return True
        return False

    def _on_context_stage(self, menu_item):
        """Handle Stage to Commit context menu action."""
        file_change = self.get_selected_file()
        if file_change:
            self.emit('file-activated', file_change)

    def _on_context_revert(self, menu_item):
        """Handle Revert Changes context menu action."""
        file_change = self.get_selected_file()
        if file_change:
            self.emit('file-revert-requested', file_change)

    def _get_status_label(self, status):
        """Get status label for a FileStatus."""
        labels = {
            FileStatus.MODIFIED: 'M',
            FileStatus.ADDED: 'A',
            FileStatus.DELETED: 'D',
            FileStatus.RENAMED: 'R',
            FileStatus.COPIED: 'C',
            FileStatus.UNTRACKED: '?',
            FileStatus.UNMERGED: 'U',
        }
        return labels.get(status, '?')

    def set_files(self, files):
        """Update the file list."""
        self._files = list(files)
        self._store.clear()

        for i, file_change in enumerate(self._files):
            status_label = self._get_status_label(file_change.status)
            self._store.append([status_label, file_change.path, i])

        self._count_label.set_text(str(len(self._files)))

    def get_selected_file(self):
        """Get the currently selected file."""
        selection = self._tree_view.get_selection()
        model, iter = selection.get_selected()
        if iter:
            idx = model.get_value(iter, 2)
            if idx < len(self._files):
                return self._files[idx]
        return None

    def clear_selection(self):
        """Clear the current selection."""
        selection = self._tree_view.get_selection()
        selection.unselect_all()

    def get_files(self):
        """Get all files in the list."""
        return list(self._files)

"""Diff view widget with syntax highlighting."""

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')

from gi.repository import Gtk, Gdk, GtkSource, GObject

from config import UIConfig


# CSS for header styling (matching git gui colors)
CSS = b'''
.diff-header {
    background-color: #FFD700;
    padding: 2px 6px;
    font-weight: bold;
}
'''


class DiffView(Gtk.Box):
    """Widget for displaying file diffs with syntax highlighting."""

    __gtype_name__ = 'DiffView'

    __gsignals__ = {
        'stage-hunk': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'stage-line': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'unstage-hunk': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'unstage-line': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'revert-hunk': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'revert-line': (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        'context-changed': (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self):
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)

        # Track current file and state
        self._current_file = None
        self._is_staged = False
        self._is_untracked = False
        self._context_lines = 3
        self._clicked_line = 0

        # Apply CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_size_request(-1, UIConfig.HEADER_HEIGHT)
        header.get_style_context().add_class('diff-header')

        # Status label (e.g., "Modified, not staged")
        self._status_label = Gtk.Label(label='')
        self._status_label.set_xalign(0)
        header.pack_start(self._status_label, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.pack_start(spacer, True, True, 0)

        # Current file label
        self._file_label = Gtk.Label()
        header.pack_start(self._file_label, False, False, 0)

        self.pack_start(header, False, False, 0)

        # Scrolled window for source view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create source buffer with diff language
        self._buffer = GtkSource.Buffer()
        self._setup_buffer()

        # Create source view
        self._source_view = GtkSource.View(buffer=self._buffer)
        self._source_view.set_editable(False)
        self._source_view.set_cursor_visible(False)
        self._source_view.set_show_line_numbers(True)
        self._source_view.set_monospace(True)
        self._source_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self._source_view.set_tab_width(4)

        # Connect right-click for context menu
        self._source_view.connect('button-press-event', self._on_button_press)

        # Create context menu
        self._create_context_menu()

        scrolled.add(self._source_view)
        self.pack_start(scrolled, True, True, 0)

        self.show_all()

    def _setup_buffer(self):
        """Set up the source buffer with diff language."""
        lang_manager = GtkSource.LanguageManager.get_default()
        diff_lang = lang_manager.get_language('diff')
        if diff_lang:
            self._buffer.set_language(diff_lang)

        # Set up style scheme
        style_manager = GtkSource.StyleSchemeManager.get_default()
        # Try various schemes
        for scheme_id in ['Adwaita-dark', 'oblivion', 'cobalt', 'classic']:
            scheme = style_manager.get_scheme(scheme_id)
            if scheme:
                self._buffer.set_style_scheme(scheme)
                break

    def set_diff(self, diff_text, file_path='', status=''):
        """Set the diff content to display.

        Args:
            diff_text: The diff text to display
            file_path: The file path to show in header
            status: The status text (e.g., "Modified, not staged")
        """
        self._buffer.set_text(diff_text)
        self._file_label.set_text(file_path)
        self._status_label.set_text(status)

        # Scroll to top
        self._source_view.scroll_to_iter(
            self._buffer.get_start_iter(),
            0.0, False, 0.0, 0.0
        )

    def clear(self):
        """Clear the diff view."""
        self._buffer.set_text('')
        self._file_label.set_text('')
        self._status_label.set_text('')
        self._current_file = None
        self._is_staged = False
        self._is_untracked = False

    def get_diff_text(self):
        """Get the current diff text."""
        start = self._buffer.get_start_iter()
        end = self._buffer.get_end_iter()
        return self._buffer.get_text(start, end, True)

    def set_style_scheme(self, scheme_id):
        """Set the color scheme for syntax highlighting."""
        style_manager = GtkSource.StyleSchemeManager.get_default()
        scheme = style_manager.get_scheme(scheme_id)
        if scheme:
            self._buffer.set_style_scheme(scheme)

    def _create_context_menu(self):
        """Create the right-click context menu."""
        self._context_menu = Gtk.Menu()

        # Stage Hunk for Commit
        self._stage_hunk_item = Gtk.MenuItem(label='Stage Hunk for Commit')
        self._stage_hunk_item.connect('activate', self._on_stage_hunk)
        self._context_menu.append(self._stage_hunk_item)

        # Stage Lines for Commit
        self._stage_lines_item = Gtk.MenuItem(label='Stage Lines for Commit')
        self._stage_lines_item.connect('activate', self._on_stage_line)
        self._context_menu.append(self._stage_lines_item)

        # Separator
        self._context_menu.append(Gtk.SeparatorMenuItem())

        # Revert Hunk
        self._revert_hunk_item = Gtk.MenuItem(label='Revert Hunk')
        self._revert_hunk_item.connect('activate', self._on_revert_hunk)
        self._context_menu.append(self._revert_hunk_item)

        # Revert Lines
        self._revert_lines_item = Gtk.MenuItem(label='Revert Lines')
        self._revert_lines_item.connect('activate', self._on_revert_line)
        self._context_menu.append(self._revert_lines_item)

        # Separator
        self._context_menu.append(Gtk.SeparatorMenuItem())

        # Show More Context
        self._more_context_item = Gtk.MenuItem(label='Show More Context')
        self._more_context_item.connect('activate', self._on_more_context)
        self._context_menu.append(self._more_context_item)

        # Show Less Context
        self._less_context_item = Gtk.MenuItem(label='Show Less Context')
        self._less_context_item.connect('activate', self._on_less_context)
        self._context_menu.append(self._less_context_item)

        self._context_menu.show_all()

    def _on_button_press(self, widget, event):
        """Handle button press events."""
        if event.button == 3:  # Right click
            # Get line number at click position
            _, y = self._source_view.window_to_buffer_coords(
                Gtk.TextWindowType.TEXT, int(event.x), int(event.y)
            )
            line_iter, _ = self._source_view.get_line_at_y(y)
            self._clicked_line = line_iter.get_line()

            self._update_context_menu_sensitivity()
            self._context_menu.popup_at_pointer(event)
            return True
        return False

    def _update_context_menu_sensitivity(self):
        """Update menu item sensitivity based on current state."""
        has_file = self._current_file is not None
        has_diff = len(self.get_diff_text().strip()) > 0

        # Stage/unstage items available for tracked files
        can_stage_unstage = has_file and has_diff and not self._is_untracked
        self._stage_hunk_item.set_sensitive(can_stage_unstage)
        self._stage_lines_item.set_sensitive(can_stage_unstage)

        # Update labels based on staged state
        if self._is_staged:
            self._stage_hunk_item.set_label('Unstage Hunk from Commit')
            self._stage_lines_item.set_label('Unstage Lines from Commit')
        else:
            self._stage_hunk_item.set_label('Stage Hunk for Commit')
            self._stage_lines_item.set_label('Stage Lines for Commit')

        # Revert items only available for unstaged, tracked files
        can_revert = has_file and has_diff and not self._is_staged and not self._is_untracked
        self._revert_hunk_item.set_sensitive(can_revert)
        self._revert_lines_item.set_sensitive(can_revert)

        # Context items only available for tracked files with diffs
        can_change_context = has_file and has_diff and not self._is_untracked
        self._more_context_item.set_sensitive(can_change_context)
        self._less_context_item.set_sensitive(can_change_context and self._context_lines > 0)

    def _on_stage_hunk(self, widget):
        """Handle Stage/Unstage Hunk action."""
        if self._current_file:
            if self._is_staged:
                self.emit('unstage-hunk', self._current_file, self._clicked_line)
            else:
                self.emit('stage-hunk', self._current_file, self._clicked_line)

    def _on_stage_line(self, widget):
        """Handle Stage/Unstage Lines action."""
        if self._current_file:
            if self._is_staged:
                self.emit('unstage-line', self._current_file, self._clicked_line)
            else:
                self.emit('stage-line', self._current_file, self._clicked_line)

    def _on_revert_hunk(self, widget):
        """Handle Revert Hunk action."""
        if self._current_file:
            self.emit('revert-hunk', self._current_file, self._clicked_line)

    def _on_revert_line(self, widget):
        """Handle Revert Lines action."""
        if self._current_file:
            self.emit('revert-line', self._current_file, self._clicked_line)

    def _on_more_context(self, widget):
        """Show more context lines in diff."""
        old_context = self._context_lines
        self._context_lines = min(self._context_lines + 3, 99)
        if self._context_lines != old_context:
            self.emit('context-changed', self._context_lines)

    def _on_less_context(self, widget):
        """Show less context lines in diff."""
        old_context = self._context_lines
        self._context_lines = max(self._context_lines - 3, 0)
        if self._context_lines != old_context:
            self.emit('context-changed', self._context_lines)

    def get_context_lines(self):
        """Get the current number of context lines."""
        return self._context_lines

    def set_file_info(self, file_path, is_staged, is_untracked=False):
        """Set the current file information.

        Args:
            file_path: Path to the current file
            is_staged: Whether the file is staged
            is_untracked: Whether the file is untracked
        """
        self._current_file = file_path
        self._is_staged = is_staged
        self._is_untracked = is_untracked

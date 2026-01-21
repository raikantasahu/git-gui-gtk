"""Diff view widget with syntax highlighting."""

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')

from gi.repository import Gtk, GtkSource


class DiffView(Gtk.Box):
    """Widget for displaying file diffs with syntax highlighting."""

    __gtype_name__ = 'DiffView'

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_margin_start(6)
        header.set_margin_end(6)
        header.set_margin_top(6)
        header.set_margin_bottom(6)

        title_label = Gtk.Label(label='Diff View')
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        header.pack_start(title_label, True, True, 0)

        # Current file label
        self._file_label = Gtk.Label()
        self._file_label.get_style_context().add_class('dim-label')
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

    def set_diff(self, diff_text, file_path=''):
        """Set the diff content to display.

        Args:
            diff_text: The diff text to display
            file_path: The file path to show in header
        """
        self._buffer.set_text(diff_text)
        self._file_label.set_text(file_path)

        # Scroll to top
        self._source_view.scroll_to_iter(
            self._buffer.get_start_iter(),
            0.0, False, 0.0, 0.0
        )

    def clear(self):
        """Clear the diff view."""
        self._buffer.set_text('')
        self._file_label.set_text('')

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

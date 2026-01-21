"""Commit area widget with message input and action buttons."""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject


class CommitArea(Gtk.Box):
    """Widget for commit message input and commit actions."""

    __gtype_name__ = 'CommitArea'

    __gsignals__ = {
        'commit-requested': (GObject.SignalFlags.RUN_FIRST, None, (str, bool, bool)),
        'push-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'pull-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'rescan-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_margin_start(6)
        self.set_margin_end(6)
        self.set_margin_top(6)
        self.set_margin_bottom(6)

        self._amend_mode = False

        # Header with title
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        title_label = Gtk.Label(label='Commit Message')
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        header.pack_start(title_label, True, True, 0)

        # Sign-off checkbox
        self._signoff_check = Gtk.CheckButton(label='Sign Off')
        self._signoff_check.set_tooltip_text('Add Signed-off-by line')
        header.pack_start(self._signoff_check, False, False, 0)

        # Amend checkbox
        self._amend_check = Gtk.CheckButton(label='Amend')
        self._amend_check.set_tooltip_text('Amend the last commit')
        self._amend_check.connect('toggled', self._on_amend_toggled)
        header.pack_start(self._amend_check, False, False, 0)

        self.pack_start(header, False, False, 0)

        # Text view for commit message
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(100)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._text_view = Gtk.TextView()
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_accepts_tab(False)
        self._text_view.set_top_margin(8)
        self._text_view.set_bottom_margin(8)
        self._text_view.set_left_margin(8)
        self._text_view.set_right_margin(8)

        self._buffer = self._text_view.get_buffer()

        scrolled.add(self._text_view)
        self.pack_start(scrolled, True, True, 0)

        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)

        # Rescan button
        rescan_btn = Gtk.Button(label='Rescan')
        rescan_icon = Gtk.Image.new_from_icon_name('view-refresh-symbolic', Gtk.IconSize.BUTTON)
        rescan_btn.set_image(rescan_icon)
        rescan_btn.set_always_show_image(True)
        rescan_btn.set_tooltip_text('Rescan repository (F5)')
        rescan_btn.connect('clicked', lambda b: self.emit('rescan-requested'))
        button_box.pack_start(rescan_btn, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        button_box.pack_start(spacer, True, True, 0)

        # Pull button
        pull_btn = Gtk.Button(label='Pull')
        pull_icon = Gtk.Image.new_from_icon_name('go-down-symbolic', Gtk.IconSize.BUTTON)
        pull_btn.set_image(pull_icon)
        pull_btn.set_always_show_image(True)
        pull_btn.set_tooltip_text('Pull from remote')
        pull_btn.connect('clicked', lambda b: self.emit('pull-requested'))
        button_box.pack_start(pull_btn, False, False, 0)

        # Push button
        push_btn = Gtk.Button(label='Push')
        push_icon = Gtk.Image.new_from_icon_name('go-up-symbolic', Gtk.IconSize.BUTTON)
        push_btn.set_image(push_icon)
        push_btn.set_always_show_image(True)
        push_btn.set_tooltip_text('Push to remote')
        push_btn.connect('clicked', lambda b: self.emit('push-requested'))
        button_box.pack_start(push_btn, False, False, 0)

        # Commit button
        self._commit_btn = Gtk.Button(label='Commit')
        commit_icon = Gtk.Image.new_from_icon_name('emblem-ok-symbolic', Gtk.IconSize.BUTTON)
        self._commit_btn.set_image(commit_icon)
        self._commit_btn.set_always_show_image(True)
        self._commit_btn.get_style_context().add_class('suggested-action')
        self._commit_btn.set_tooltip_text('Create commit (Ctrl+Enter)')
        self._commit_btn.connect('clicked', self._on_commit_clicked)
        button_box.pack_start(self._commit_btn, False, False, 0)

        self.pack_start(button_box, False, False, 0)

        self.show_all()

    def _on_commit_clicked(self, button):
        """Handle commit button click."""
        message = self.get_message()
        sign_off = self._signoff_check.get_active()
        amend = self._amend_check.get_active()
        self.emit('commit-requested', message, amend, sign_off)

    def _on_amend_toggled(self, check_button):
        """Handle amend checkbox toggle."""
        self._amend_mode = check_button.get_active()
        if self._amend_mode:
            self._commit_btn.set_label('Amend')
        else:
            self._commit_btn.set_label('Commit')

    def get_message(self):
        """Get the commit message."""
        start = self._buffer.get_start_iter()
        end = self._buffer.get_end_iter()
        return self._buffer.get_text(start, end, True)

    def set_message(self, message):
        """Set the commit message."""
        self._buffer.set_text(message)

    def clear_message(self):
        """Clear the commit message."""
        self._buffer.set_text('')

    def is_amend_mode(self):
        """Check if amend mode is enabled."""
        return self._amend_check.get_active()

    def set_amend_mode(self, enabled):
        """Set amend mode."""
        self._amend_check.set_active(enabled)

    def is_signoff_enabled(self):
        """Check if sign-off is enabled."""
        return self._signoff_check.get_active()

    def set_signoff_enabled(self, enabled):
        """Set sign-off mode."""
        self._signoff_check.set_active(enabled)

    def focus_message(self):
        """Focus the commit message text view."""
        self._text_view.grab_focus()

    def set_commit_sensitive(self, sensitive):
        """Enable or disable the commit button."""
        self._commit_btn.set_sensitive(sensitive)

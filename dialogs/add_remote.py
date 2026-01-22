"""Add remote dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config import UIConfig


def show_add_remote_dialog(parent, git_ops):
    """Show dialog to add a new remote.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Tuple of (name, url, fetch_immediately) or None if cancelled
    """
    dialog = Gtk.Dialog(
        title='Add Remote',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Add', Gtk.ResponseType.OK
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)

    add_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    add_button.set_sensitive(False)

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

    def on_url_changed(entry):
        """Enable Add button only if URL is not empty."""
        add_button.set_sensitive(bool(entry.get_text().strip()))

    url_entry.connect('changed', on_url_changed)

    content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6)

    fetch_check = Gtk.CheckButton(label='Fetch Immediately')
    fetch_check.set_active(False)
    content.pack_start(fetch_check, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    name = name_entry.get_text().strip()
    url = url_entry.get_text().strip()
    fetch_after = fetch_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and name and url:
        return (name, url, fetch_after)
    return None

"""Rename remote dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig


def _get_default_remote_index(repo, remotes):
    """Get the index of the default remote (tracking remote or first)."""
    tracking_remote = gitops.get_tracking_remote(repo)
    if tracking_remote and tracking_remote in remotes:
        return remotes.index(tracking_remote)
    return 0


def show_rename_remote_dialog(parent, repo):
    """Show dialog to rename a remote.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (old_name, new_name) or None if cancelled
    """
    remotes = gitops.get_remotes(repo)
    if not remotes:
        return None

    dialog = Gtk.Dialog(
        title='Rename Remote',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Rename', Gtk.ResponseType.OK
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)

    rename_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    rename_button.set_sensitive(False)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    # Remote selection
    remote_label = Gtk.Label(label='Remote to rename:')
    remote_label.set_xalign(0)
    content.pack_start(remote_label, False, False, 0)

    remote_combo = Gtk.ComboBoxText()
    for remote in remotes:
        remote_combo.append_text(remote)
    remote_combo.set_active(_get_default_remote_index(repo, remotes))
    content.pack_start(remote_combo, False, False, 0)

    # New name entry
    new_name_label = Gtk.Label(label='New name:')
    new_name_label.set_xalign(0)
    content.pack_start(new_name_label, False, False, 0)

    new_name_entry = Gtk.Entry()
    new_name_entry.set_activates_default(True)
    content.pack_start(new_name_entry, False, False, 0)

    def on_name_changed(entry):
        """Enable Rename button only if new name is not empty and different."""
        new_name = entry.get_text().strip()
        old_name = remote_combo.get_active_text()
        rename_button.set_sensitive(bool(new_name) and new_name != old_name)

    def on_remote_changed(combo):
        """Update validation when remote selection changes."""
        on_name_changed(new_name_entry)

    new_name_entry.connect('changed', on_name_changed)
    remote_combo.connect('changed', on_remote_changed)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    old_name = remote_combo.get_active_text()
    new_name = new_name_entry.get_text().strip()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and old_name and new_name:
        return (old_name, new_name)
    return None

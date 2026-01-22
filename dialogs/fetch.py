"""Fetch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config import UIConfig


def _get_default_remote_index(git_ops, remotes):
    """Get the index of the default remote (tracking remote or first)."""
    tracking_remote = git_ops.get_tracking_remote()
    if tracking_remote and tracking_remote in remotes:
        return remotes.index(tracking_remote)
    return 0


def show_fetch_dialog(parent, git_ops):
    """Show dialog to fetch from a remote.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Remote name or None if cancelled
    """
    remotes = git_ops.get_remotes()
    if not remotes:
        return None

    dialog = Gtk.Dialog(
        title='Fetch',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Fetch', Gtk.ResponseType.OK
    )

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    label = Gtk.Label(label='Fetch from remote:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    for remote in remotes:
        combo.append_text(remote)
    combo.set_active(_get_default_remote_index(git_ops, remotes))
    content.pack_start(combo, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_remote = combo.get_active_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_remote:
        return selected_remote
    return None

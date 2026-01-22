"""Delete remote dialog for Git GUI GTK."""

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


def show_delete_remote_dialog(parent, git_ops):
    """Show dialog to delete a remote.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Remote name to delete or None if cancelled
    """
    remotes = git_ops.get_remotes()
    if not remotes:
        return None

    dialog = Gtk.Dialog(
        title='Delete Remote',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Delete', Gtk.ResponseType.OK
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)

    delete_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    delete_button.get_style_context().add_class('destructive-action')

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    # Remote selection
    remote_label = Gtk.Label(label='Remote to delete:')
    remote_label.set_xalign(0)
    content.pack_start(remote_label, False, False, 0)

    remote_combo = Gtk.ComboBoxText()
    for remote in remotes:
        remote_combo.append_text(remote)
    remote_combo.set_active(_get_default_remote_index(git_ops, remotes))
    content.pack_start(remote_combo, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.CANCEL)
    dialog.show_all()

    response = dialog.run()
    selected_remote = remote_combo.get_active_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_remote:
        # Show confirmation dialog
        confirm = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f'Delete remote "{selected_remote}"?'
        )
        confirm.format_secondary_text(
            'This will remove the remote and all its tracking branches. '
            'This action cannot be undone.'
        )
        confirm.add_button('Cancel', Gtk.ResponseType.CANCEL)
        confirm.add_button('Delete', Gtk.ResponseType.OK)

        delete_btn = confirm.get_widget_for_response(Gtk.ResponseType.OK)
        delete_btn.get_style_context().add_class('destructive-action')

        confirm_response = confirm.run()
        confirm.destroy()

        if confirm_response == Gtk.ResponseType.OK:
            return selected_remote

    return None

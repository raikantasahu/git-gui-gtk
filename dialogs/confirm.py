"""Confirmation dialog for destructive actions."""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk


def show_confirm_dialog(parent, title, detail, confirm_label):
    """Show a modal confirmation dialog with a destructive action button.

    Args:
        parent: Parent Gtk.Window.
        title: Primary text shown as bold heading.
        detail: Secondary text with details.
        confirm_label: Label for the confirm button (e.g. 'Revert').

    Returns:
        True if the user confirmed, False otherwise.
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text=title,
    )
    dialog.format_secondary_text(detail)
    dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
    dialog.add_button(confirm_label, Gtk.ResponseType.OK)

    confirm_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    confirm_btn.get_style_context().add_class('destructive-action')

    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK

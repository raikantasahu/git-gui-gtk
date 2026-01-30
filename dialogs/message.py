"""Generic message dialog for displaying info, warning, and error messages."""

from enum import Enum
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class MessageType(Enum):
    """Message types for status display."""
    INFO = Gtk.MessageType.INFO
    WARNING = Gtk.MessageType.WARNING
    ERROR = Gtk.MessageType.ERROR

    @staticmethod
    def get_message_type(name):
        """Return a MessageType from a string name ('info', 'warning', 'error')."""
        return _NAME_TO_MSG_TYPE.get(name, MessageType.INFO)

    def get_message_dialog_title(self):
        """Return a dialog title for this message type."""
        return _MSG_TYPE_TITLE.get(self, 'Information')

_NAME_TO_MSG_TYPE = {
    'info': MessageType.INFO,
    'warning': MessageType.WARNING,
    'error': MessageType.ERROR,
}

_MSG_TYPE_TITLE = {
    MessageType.INFO: 'Information',
    MessageType.WARNING: 'Warning',
    MessageType.ERROR: 'Error',
}

def show_message_dialog(parent, title, message, msg_type=MessageType.INFO):
    """Show a modal message dialog.

    Args:
        parent: Parent Gtk.Window.
        title: Primary text shown as bold heading.
        message: Secondary text with details.
        msg_type: A MessageType enum value.
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=msg_type.value,
        buttons=Gtk.ButtonsType.NONE,
        text=title,
    )
    dialog.format_secondary_text(message)

    for label in dialog.get_message_area().get_children():
        if isinstance(label, Gtk.Label):
            label.set_selectable(True)

    button_box = dialog.get_action_area()
    button_box.set_layout(Gtk.ButtonBoxStyle.END)
    button_box.set_margin_end(12)
    button_box.set_margin_bottom(12)

    dialog.add_button('Close', Gtk.ResponseType.CLOSE)
    dialog.run()
    dialog.destroy()

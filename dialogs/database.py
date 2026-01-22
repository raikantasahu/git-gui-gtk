"""Database dialogs for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import threading


def show_database_statistics_dialog(parent, git_ops):
    """Show git database statistics dialog.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        True if successful, False otherwise
    """
    success, output = git_ops.get_database_statistics()
    if success:
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text='Database Statistics'
        )
        dialog.format_secondary_text(output)
        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        dialog.run()
        dialog.destroy()
        return True
    return False


def show_compress_database_dialog(parent, git_ops, on_complete=None):
    """Show compress database dialog with progress.

    Args:
        parent: Parent window
        git_ops: GitOperations instance
        on_complete: Optional callback(success, message) when complete
    """
    dialog = Gtk.Dialog(
        title='Compress Database',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(350, 120)
    dialog.set_deletable(False)

    content = dialog.get_content_area()
    content.set_margin_start(20)
    content.set_margin_end(20)
    content.set_margin_top(20)
    content.set_margin_bottom(12)
    content.set_spacing(12)

    label = Gtk.Label(label='Compressing database...')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    spinner = Gtk.Spinner()
    spinner.start()
    content.pack_start(spinner, False, False, 0)

    dialog.show_all()

    def on_compress_complete(success, message):
        spinner.stop()
        spinner.hide()

        if success:
            label.set_text('Database compressed successfully.')
        else:
            label.set_text(f'Compression failed: {message}')

        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        dialog.set_deletable(True)
        button_box.show_all()

        dialog.run()
        dialog.destroy()

        if on_complete:
            on_complete(success, message)

    def do_compress():
        success, message = git_ops.compress_database()
        GLib.idle_add(on_compress_complete, success, message)

    thread = threading.Thread(target=do_compress)
    thread.daemon = True
    thread.start()


def show_verify_database_dialog(parent, git_ops, on_complete=None):
    """Show verify database dialog with progress and result.

    Args:
        parent: Parent window
        git_ops: GitOperations instance
        on_complete: Optional callback(success, message) when complete
    """
    dialog = Gtk.Dialog(
        title='Verify Database',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(350, 120)
    dialog.set_deletable(False)

    content = dialog.get_content_area()
    content.set_margin_start(20)
    content.set_margin_end(20)
    content.set_margin_top(20)
    content.set_margin_bottom(12)
    content.set_spacing(12)

    label = Gtk.Label(label='Verifying database...')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    spinner = Gtk.Spinner()
    spinner.start()
    content.pack_start(spinner, False, False, 0)

    dialog.show_all()

    def on_verify_complete(success, message):
        spinner.stop()
        spinner.hide()

        if success:
            label.set_text(message if message else 'No errors found.')
        else:
            label.set_text(f'Verification failed: {message}')

        button_box = dialog.get_action_area()
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_end(12)
        button_box.set_margin_bottom(12)
        dialog.add_button('Close', Gtk.ResponseType.CLOSE)
        dialog.set_deletable(True)
        button_box.show_all()

        dialog.run()
        dialog.destroy()

        if on_complete:
            on_complete(success, message)

    def do_verify():
        success, message = git_ops.verify_database()
        GLib.idle_add(on_verify_complete, success, message)

    thread = threading.Thread(target=do_verify)
    thread.daemon = True
    thread.start()

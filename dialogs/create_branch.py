"""Create branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_create_branch_dialog(parent, repo):
    """Show dialog to create a new branch.

    Args:
        parent: Parent window
        repo: Git repository object (unused, kept for consistency)

    Returns:
        Tuple of (branch_name, checkout) or None if cancelled
    """
    dialog = Gtk.Dialog(
        title='Create Branch',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Create', Gtk.ResponseType.OK
    )

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    label = Gtk.Label(label='Branch name:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_activates_default(True)
    content.pack_start(entry, False, False, 0)

    checkout_check = Gtk.CheckButton(label='Checkout after creation')
    checkout_check.set_active(True)
    content.pack_start(checkout_check, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    branch_name = entry.get_text().strip()
    checkout = checkout_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and branch_name:
        return (branch_name, checkout)
    return None

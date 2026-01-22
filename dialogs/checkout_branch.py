"""Checkout branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_checkout_branch_dialog(parent, git_ops):
    """Show dialog to checkout a branch.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Branch name to checkout or None if cancelled
    """
    branches = git_ops.get_branches()
    if not branches:
        return None

    dialog = Gtk.Dialog(
        title='Checkout Branch',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Checkout', Gtk.ResponseType.OK
    )

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    label = Gtk.Label(label='Select branch:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    current_branch = git_ops.get_current_branch()
    active_index = 0
    for i, branch in enumerate(branches):
        combo.append_text(branch)
        if branch == current_branch:
            active_index = i
    combo.set_active(active_index)
    content.pack_start(combo, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_branch = combo.get_active_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_branch:
        return selected_branch
    return None

"""Delete branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig


def show_delete_branch_dialog(parent, repo):
    """Show dialog to delete a branch.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (branch_name, force) or None if cancelled
    """
    branches = gitops.get_branches(repo)
    current_branch = gitops.get_current_branch(repo)
    # Filter out current branch
    branches = [b for b in branches if b != current_branch]

    if not branches:
        return None

    dialog = Gtk.Dialog(
        title='Delete Branch',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.DIALOG_WIDTH, -1)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Delete', Gtk.ResponseType.OK
    )

    # Make delete button destructive
    delete_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    delete_btn.get_style_context().add_class('destructive-action')

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    label = Gtk.Label(label='Select branch to delete:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    for branch in branches:
        combo.append_text(branch)
    combo.set_active(0)
    content.pack_start(combo, False, False, 0)

    force_check = Gtk.CheckButton(label='Force delete (even if not merged)')
    content.pack_start(force_check, False, False, 0)

    dialog.show_all()

    response = dialog.run()
    selected_branch = combo.get_active_text()
    force = force_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_branch:
        return (selected_branch, force)
    return None

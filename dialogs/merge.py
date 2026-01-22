"""Merge dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_merge_dialog(parent, git_ops):
    """Show dialog to merge a branch.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Tuple of (branch, no_ff, squash) or None if cancelled
    """
    branches = git_ops.get_branches()
    current_branch = git_ops.get_current_branch()
    # Filter out current branch
    branches = [b for b in branches if b != current_branch]

    if not branches:
        return None

    dialog = Gtk.Dialog(
        title='Merge Branch',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Merge', Gtk.ResponseType.OK
    )

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    info_label = Gtk.Label(label=f'Merge into: {current_branch}')
    info_label.set_xalign(0)
    content.pack_start(info_label, False, False, 0)

    label = Gtk.Label(label='Select branch to merge:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    for branch in branches:
        combo.append_text(branch)
    combo.set_active(0)
    content.pack_start(combo, False, False, 0)

    # Options
    no_ff_check = Gtk.CheckButton(label='No fast-forward (always create merge commit)')
    content.pack_start(no_ff_check, False, False, 0)

    squash_check = Gtk.CheckButton(label='Squash commits')
    content.pack_start(squash_check, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_branch = combo.get_active_text()
    no_ff = no_ff_check.get_active()
    squash = squash_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_branch:
        return (selected_branch, no_ff, squash)
    return None

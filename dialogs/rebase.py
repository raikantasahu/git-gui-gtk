"""Rebase dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops


def show_rebase_dialog(parent, repo):
    """Show dialog to rebase current branch.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Branch name to rebase onto or None if cancelled
    """
    branches = gitops.get_branches(repo)
    current_branch = gitops.get_current_branch(repo)
    # Filter out current branch
    branches = [b for b in branches if b != current_branch]

    if not branches:
        return None

    dialog = Gtk.Dialog(
        title='Rebase Branch',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Rebase', Gtk.ResponseType.OK
    )

    # Make rebase button look cautionary
    rebase_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    rebase_btn.get_style_context().add_class('suggested-action')

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    info_label = Gtk.Label(label=f'Rebase branch: {current_branch}')
    info_label.set_xalign(0)
    content.pack_start(info_label, False, False, 0)

    label = Gtk.Label(label='Rebase onto:')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    for branch in branches:
        combo.append_text(branch)
    combo.set_active(0)
    content.pack_start(combo, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_branch = combo.get_active_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_branch:
        return selected_branch
    return None

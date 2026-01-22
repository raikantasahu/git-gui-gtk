"""Push dialog for Git GUI GTK."""

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


def show_push_dialog(parent, git_ops):
    """Show dialog to push to a remote.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Tuple of (remote, branch, force, tags) or None if cancelled
    """
    remotes = git_ops.get_remotes()
    if not remotes:
        return None

    current_branch = git_ops.get_current_branch()

    dialog = Gtk.Dialog(
        title='Push',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Push', Gtk.ResponseType.OK
    )

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    # Remote selection
    remote_label = Gtk.Label(label='Remote:')
    remote_label.set_xalign(0)
    content.pack_start(remote_label, False, False, 0)

    remote_combo = Gtk.ComboBoxText()
    for remote in remotes:
        remote_combo.append_text(remote)
    remote_combo.set_active(_get_default_remote_index(git_ops, remotes))
    content.pack_start(remote_combo, False, False, 0)

    # Branch selection
    branch_label = Gtk.Label(label='Remote branch:')
    branch_label.set_xalign(0)
    content.pack_start(branch_label, False, False, 0)

    branch_combo = Gtk.ComboBoxText()
    content.pack_start(branch_combo, False, False, 0)

    def update_branches(combo):
        """Update branch dropdown when remote changes."""
        branch_combo.remove_all()
        selected_remote = combo.get_active_text()
        if selected_remote:
            branches = git_ops.get_remote_branches(selected_remote)
            default_index = 0
            for i, branch in enumerate(branches):
                branch_combo.append_text(branch)
                if branch == current_branch:
                    default_index = i
            if branches:
                branch_combo.set_active(default_index)

    remote_combo.connect('changed', update_branches)
    update_branches(remote_combo)

    # Push options
    content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6)

    options_label = Gtk.Label(label='Push options:')
    options_label.set_xalign(0)
    content.pack_start(options_label, False, False, 0)

    force_check = Gtk.CheckButton(label='Force push (--force)')
    force_check.set_tooltip_text('Overwrites remote branch. Use with caution!')
    content.pack_start(force_check, False, False, 0)

    tags_check = Gtk.CheckButton(label='Push tags (--tags)')
    tags_check.set_tooltip_text('Push all local tags to the remote')
    content.pack_start(tags_check, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_remote = remote_combo.get_active_text()
    selected_branch = branch_combo.get_active_text()
    force = force_check.get_active()
    tags = tags_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_remote:
        return (selected_remote, selected_branch, force, tags)
    return None

"""Pull dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig


def _get_default_remote_index(repo, remotes):
    """Get the index of the default remote (tracking remote or first)."""
    tracking_remote = gitops.get_tracking_remote(repo)
    if tracking_remote and tracking_remote in remotes:
        return remotes.index(tracking_remote)
    return 0


def show_pull_dialog(parent, repo):
    """Show dialog to pull from a remote.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (remote, branch, ff_only, rebase) or None if cancelled
    """
    remotes = gitops.get_remotes(repo)
    if not remotes:
        return None

    current_branch = gitops.get_current_branch(repo)

    dialog = Gtk.Dialog(
        title='Pull',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.REMOTE_DIALOG_WIDTH, -1)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Pull', Gtk.ResponseType.OK
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
    remote_combo.set_active(_get_default_remote_index(repo, remotes))
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
            branches = gitops.get_remote_branches(repo, selected_remote)
            default_index = 0
            for i, branch in enumerate(branches):
                branch_combo.append_text(branch)
                if branch == current_branch:
                    default_index = i
            if branches:
                branch_combo.set_active(default_index)

    remote_combo.connect('changed', update_branches)
    update_branches(remote_combo)

    # Pull options
    content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6)

    options_label = Gtk.Label(label='Pull options:')
    options_label.set_xalign(0)
    content.pack_start(options_label, False, False, 0)

    default_radio = Gtk.RadioButton.new_with_label(None, 'Default (merge)')
    default_radio.set_active(True)
    content.pack_start(default_radio, False, False, 0)

    ff_only_radio = Gtk.RadioButton.new_with_label_from_widget(default_radio, 'Fast-forward only (--ff-only)')
    content.pack_start(ff_only_radio, False, False, 0)

    rebase_radio = Gtk.RadioButton.new_with_label_from_widget(default_radio, 'Rebase (--rebase)')
    content.pack_start(rebase_radio, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_remote = remote_combo.get_active_text()
    selected_branch = branch_combo.get_active_text()
    ff_only = ff_only_radio.get_active()
    rebase = rebase_radio.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected_remote:
        return (selected_remote, selected_branch, ff_only, rebase)
    return None

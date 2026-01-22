"""Rename branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig
from utils import is_valid_branch_name


def show_rename_branch_dialog(parent, repo):
    """Show dialog to rename a branch.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (old_name, new_name) or None if cancelled
    """
    branches = gitops.get_branches(repo)
    if not branches:
        return None

    current_branch = gitops.get_current_branch(repo)

    dialog = Gtk.Dialog(
        title='Rename Branch',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.DIALOG_WIDTH, -1)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Rename', Gtk.ResponseType.OK
    )

    rename_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    rename_button.set_sensitive(False)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    label1 = Gtk.Label(label='Select branch to rename:')
    label1.set_xalign(0)
    content.pack_start(label1, False, False, 0)

    combo = Gtk.ComboBoxText()
    active_index = 0
    for i, branch in enumerate(branches):
        combo.append_text(branch)
        if branch == current_branch:
            active_index = i
    combo.set_active(active_index)
    content.pack_start(combo, False, False, 0)

    label2 = Gtk.Label(label='New name:')
    label2.set_xalign(0)
    content.pack_start(label2, False, False, 0)

    entry = Gtk.Entry()
    entry.set_activates_default(True)
    content.pack_start(entry, False, False, 0)

    # Validation message label
    validation_label = Gtk.Label()
    validation_label.set_xalign(0)
    validation_label.set_markup('<span size="small" foreground="red"></span>')
    content.pack_start(validation_label, False, False, 0)

    def validate_name(widget):
        """Validate new branch name and update UI accordingly."""
        new_name = entry.get_text().strip()
        old_name = combo.get_active_text()

        if not new_name:
            rename_button.set_sensitive(False)
            validation_label.set_markup('<span size="small" foreground="red"></span>')
        elif new_name == old_name:
            rename_button.set_sensitive(False)
            validation_label.set_markup(
                '<span size="small" foreground="red">New name is same as current name</span>'
            )
        elif not is_valid_branch_name(new_name):
            rename_button.set_sensitive(False)
            validation_label.set_markup(
                '<span size="small" foreground="red">Invalid branch name</span>'
            )
        elif new_name in branches:
            rename_button.set_sensitive(False)
            validation_label.set_markup(
                '<span size="small" foreground="red">Branch already exists</span>'
            )
        else:
            rename_button.set_sensitive(True)
            validation_label.set_markup('<span size="small" foreground="red"></span>')

    entry.connect('changed', validate_name)
    combo.connect('changed', validate_name)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    old_name = combo.get_active_text()
    new_name = entry.get_text().strip()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and old_name and new_name and is_valid_branch_name(new_name):
        return (old_name, new_name)
    return None

"""Create branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig
from utils import is_valid_branch_name


def show_create_branch_dialog(parent, repo):
    """Show dialog to create a new branch.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (branch_name, base, checkout) or None if cancelled
    """
    dialog = Gtk.Dialog(
        title='Create Branch',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.DIALOG_WIDTH, 400)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Create', Gtk.ResponseType.OK
    )

    create_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    create_button.set_sensitive(False)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    # Branch name
    name_label = Gtk.Label(label='Branch name:')
    name_label.set_xalign(0)
    content.pack_start(name_label, False, False, 0)

    name_entry = Gtk.Entry()
    name_entry.set_activates_default(True)
    content.pack_start(name_entry, False, False, 0)

    # Validation message label
    validation_label = Gtk.Label()
    validation_label.set_xalign(0)
    validation_label.set_markup('<span size="small" foreground="red"></span>')
    content.pack_start(validation_label, False, False, 0)

    # Starting point type selection
    base_type_label = Gtk.Label(label='Starting point:')
    base_type_label.set_xalign(0)
    content.pack_start(base_type_label, False, False, 0)

    # Radio buttons for type selection
    radio_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    local_radio = Gtk.RadioButton.new_with_label(None, 'Local Branch')
    tracking_radio = Gtk.RadioButton.new_with_label_from_widget(local_radio, 'Tracking Branch')
    tag_radio = Gtk.RadioButton.new_with_label_from_widget(local_radio, 'Tag')
    radio_box.pack_start(local_radio, False, False, 0)
    radio_box.pack_start(tracking_radio, False, False, 0)
    radio_box.pack_start(tag_radio, False, False, 0)
    content.pack_start(radio_box, False, False, 0)

    # Fetch data
    local_branches = gitops.get_branches(repo)
    tracking_branches = gitops.get_tracking_branches(repo)
    tags = gitops.get_tags(repo)
    current_branch = gitops.get_current_branch(repo)

    # ListBox for base selection in a scrolled window
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_vexpand(True)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scrolled.add(listbox)
    content.pack_start(scrolled, True, True, 0)

    def populate_listbox(items, default_item=None):
        """Populate the listbox with items."""
        # Remove all existing rows
        for child in listbox.get_children():
            listbox.remove(child)

        default_row = None
        for item in items:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=item)
            label.set_xalign(0)
            label.set_margin_start(6)
            label.set_margin_end(6)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            row.add(label)
            row.item_name = item
            listbox.add(row)
            if item == default_item:
                default_row = row

        listbox.show_all()

        # Select default row
        if default_row:
            listbox.select_row(default_row)
        elif items:
            listbox.select_row(listbox.get_row_at_index(0))

    def on_type_changed(radio):
        """Update listbox when type selection changes."""
        if not radio.get_active():
            return

        if local_radio.get_active():
            populate_listbox(local_branches, current_branch)
        elif tracking_radio.get_active():
            populate_listbox(tracking_branches)
        elif tag_radio.get_active():
            populate_listbox(tags)

    local_radio.connect('toggled', on_type_changed)
    tracking_radio.connect('toggled', on_type_changed)
    tag_radio.connect('toggled', on_type_changed)

    # Initialize with local branches
    populate_listbox(local_branches, current_branch)

    # Checkout option
    checkout_check = Gtk.CheckButton(label='Checkout after creation')
    checkout_check.set_active(True)
    content.pack_start(checkout_check, False, False, 0)

    def validate_name(entry):
        """Validate branch name and update UI accordingly."""
        name = entry.get_text().strip()
        if not name:
            create_button.set_sensitive(False)
            validation_label.set_markup('<span size="small" foreground="red"></span>')
        elif not is_valid_branch_name(name):
            create_button.set_sensitive(False)
            validation_label.set_markup(
                '<span size="small" foreground="red">Invalid branch name</span>'
            )
        elif name in local_branches:
            create_button.set_sensitive(False)
            validation_label.set_markup(
                '<span size="small" foreground="red">Branch already exists</span>'
            )
        else:
            create_button.set_sensitive(True)
            validation_label.set_markup('<span size="small" foreground="red"></span>')

    name_entry.connect('changed', validate_name)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    branch_name = name_entry.get_text().strip()
    selected_row = listbox.get_selected_row()
    base = selected_row.item_name if selected_row else None
    checkout = checkout_check.get_active()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and branch_name and is_valid_branch_name(branch_name):
        return (branch_name, base, checkout)
    return None

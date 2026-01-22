"""Merge dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from config import UIConfig


def show_merge_dialog(parent, repo):
    """Show dialog to merge a branch.

    Args:
        parent: Parent window
        repo: Git repository object

    Returns:
        Tuple of (branch, strategy) or None if cancelled.
        Strategy is one of: 'default', 'no-ff', 'ff-only', 'squash'
    """
    # Fetch data
    current_branch = gitops.get_current_branch(repo)
    local_branches = gitops.get_branches(repo)
    # Filter out current branch from local branches
    local_branches = [b for b in local_branches if b != current_branch]
    tracking_branches = gitops.get_tracking_branches(repo)
    tags = gitops.get_tags(repo)

    # Check if there's anything to merge
    if not local_branches and not tracking_branches and not tags:
        return None

    dialog = Gtk.Dialog(
        title='Merge',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(UIConfig.DIALOG_WIDTH, 400)
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

    # Info label
    info_label = Gtk.Label(label=f'Merge into: {current_branch}')
    info_label.set_xalign(0)
    content.pack_start(info_label, False, False, 0)

    # Type selection label
    type_label = Gtk.Label(label='Merge from:')
    type_label.set_xalign(0)
    content.pack_start(type_label, False, False, 0)

    # Radio buttons for type selection
    radio_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    local_radio = Gtk.RadioButton.new_with_label(None, 'Local Branch')
    tracking_radio = Gtk.RadioButton.new_with_label_from_widget(local_radio, 'Tracking Branch')
    tag_radio = Gtk.RadioButton.new_with_label_from_widget(local_radio, 'Tag')
    radio_box.pack_start(local_radio, False, False, 0)
    radio_box.pack_start(tracking_radio, False, False, 0)
    radio_box.pack_start(tag_radio, False, False, 0)
    content.pack_start(radio_box, False, False, 0)

    # ListBox for selection in a scrolled window
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_vexpand(True)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scrolled.add(listbox)
    content.pack_start(scrolled, True, True, 0)

    def populate_listbox(items):
        """Populate the listbox with items."""
        # Remove all existing rows
        for child in listbox.get_children():
            listbox.remove(child)

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

        listbox.show_all()

        # Select first row if available
        if items:
            listbox.select_row(listbox.get_row_at_index(0))

    def on_type_changed(radio):
        """Update listbox when type selection changes."""
        if not radio.get_active():
            return

        if local_radio.get_active():
            populate_listbox(local_branches)
        elif tracking_radio.get_active():
            populate_listbox(tracking_branches)
        elif tag_radio.get_active():
            populate_listbox(tags)

    local_radio.connect('toggled', on_type_changed)
    tracking_radio.connect('toggled', on_type_changed)
    tag_radio.connect('toggled', on_type_changed)

    # Initialize with local branches
    populate_listbox(local_branches)

    # Separator
    content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6)

    # Merge strategy options (mutually exclusive)
    strategy_label = Gtk.Label(label='Merge strategy:')
    strategy_label.set_xalign(0)
    content.pack_start(strategy_label, False, False, 0)

    default_radio = Gtk.RadioButton.new_with_label(None, 'Default')
    content.pack_start(default_radio, False, False, 0)

    no_ff_radio = Gtk.RadioButton.new_with_label_from_widget(
        default_radio, 'No fast-forward (always create merge commit)'
    )
    content.pack_start(no_ff_radio, False, False, 0)

    ff_only_radio = Gtk.RadioButton.new_with_label_from_widget(
        default_radio, 'Fast-forward only (fails if merge commit is needed)'
    )
    content.pack_start(ff_only_radio, False, False, 0)

    squash_radio = Gtk.RadioButton.new_with_label_from_widget(
        default_radio, 'Squash commits (needs to be committed after merge)'
    )
    content.pack_start(squash_radio, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    selected_row = listbox.get_selected_row()
    selected = selected_row.item_name if selected_row else None

    # Determine selected strategy
    if no_ff_radio.get_active():
        strategy = 'no-ff'
    elif ff_only_radio.get_active():
        strategy = 'ff-only'
    elif squash_radio.get_active():
        strategy = 'squash'
    else:
        strategy = 'default'

    dialog.destroy()

    if response == Gtk.ResponseType.OK and selected:
        return (selected, strategy)
    return None

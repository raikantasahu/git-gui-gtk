"""Reset branch dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def show_reset_branch_dialog(parent, git_ops):
    """Show dialog to reset current branch.

    Args:
        parent: Parent window
        git_ops: GitOperations instance

    Returns:
        Tuple of (target, mode) or None if cancelled
        mode is one of: 'soft', 'mixed', 'hard'
    """
    dialog = Gtk.Dialog(
        title='Reset Branch',
        transient_for=parent,
        modal=True
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        'Reset', Gtk.ResponseType.OK
    )

    # Make reset button destructive
    reset_btn = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    reset_btn.get_style_context().add_class('destructive-action')

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    current_branch = git_ops.get_current_branch()
    info_label = Gtk.Label(label=f'Reset branch: {current_branch}')
    info_label.set_xalign(0)
    content.pack_start(info_label, False, False, 0)

    label = Gtk.Label(label='Reset to (commit/branch/tag):')
    label.set_xalign(0)
    content.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_text('HEAD')
    entry.set_activates_default(True)
    content.pack_start(entry, False, False, 0)

    mode_label = Gtk.Label(label='Reset mode:')
    mode_label.set_xalign(0)
    content.pack_start(mode_label, False, False, 0)

    soft_radio = Gtk.RadioButton.new_with_label(None, 'Soft (keep changes staged)')
    content.pack_start(soft_radio, False, False, 0)

    mixed_radio = Gtk.RadioButton.new_with_label_from_widget(soft_radio, 'Mixed (keep changes unstaged)')
    mixed_radio.set_active(True)
    content.pack_start(mixed_radio, False, False, 0)

    hard_radio = Gtk.RadioButton.new_with_label_from_widget(soft_radio, 'Hard (discard all changes)')
    content.pack_start(hard_radio, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    target = entry.get_text().strip()
    if soft_radio.get_active():
        mode = 'soft'
    elif hard_radio.get_active():
        mode = 'hard'
    else:
        mode = 'mixed'
    dialog.destroy()

    if response == Gtk.ResponseType.OK and target:
        return (target, mode)
    return None

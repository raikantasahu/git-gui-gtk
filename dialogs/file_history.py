"""File history dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

import gitops
from .commit_list import create_commit_list_pane
from .file_picker import show_file_picker_dialog


def show_file_history_dialog(parent, repo, file_path):
    """Show commit history for a specific file.

    Args:
        parent: Parent window
        repo: Git repository object
        file_path: Path to the file (relative to repo root), or None to
            start with the file picker
    """
    # If no file given, prompt immediately
    if file_path is None:
        file_path = show_file_picker_dialog(parent, repo)
        if file_path is None:
            return

    dialog = Gtk.Dialog(
        title=f'History: {file_path}',
        transient_for=parent,
        modal=True,
    )
    dialog.set_default_size(700, 500)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)

    content = dialog.get_content_area()
    content.set_margin_start(8)
    content.set_margin_end(8)
    content.set_margin_top(8)
    content.set_margin_bottom(8)
    content.set_spacing(4)

    # Top controls row: file label + pick button
    controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    file_prefix = Gtk.Label(label='File:')
    controls_box.pack_start(file_prefix, False, False, 0)

    file_label = Gtk.Label(label=file_path)
    file_label.set_selectable(True)
    file_label.modify_font(Pango.FontDescription('monospace'))
    file_label.set_halign(Gtk.Align.START)
    file_label.set_ellipsize(Pango.EllipsizeMode.START)
    controls_box.pack_start(file_label, True, True, 0)

    pick_button = Gtk.Button(label='Pick File...')
    controls_box.pack_end(pick_button, False, False, 0)

    content.pack_start(controls_box, False, False, 0)

    # Container for history content (below controls)
    history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    history_box.set_vexpand(True)
    content.pack_start(history_box, True, True, 0)

    def _load_history(fp):
        # Clear previous history content
        for child in history_box.get_children():
            history_box.remove(child)
            child.destroy()

        commits = gitops.get_file_log(repo, fp)

        if not commits:
            label = Gtk.Label(label='No history found')
            label.set_vexpand(True)
            history_box.pack_start(label, True, True, 0)
        else:
            paned = create_commit_list_pane(commits)
            history_box.pack_start(paned, True, True, 0)

        history_box.show_all()

    def on_pick_file_clicked(button):
        new_path = show_file_picker_dialog(dialog, repo)
        if new_path:
            file_label.set_text(new_path)
            dialog.set_title(f'History: {new_path}')
            _load_history(new_path)

    pick_button.connect('clicked', on_pick_file_clicked)

    _load_history(file_path)

    dialog.show_all()
    dialog.run()
    dialog.destroy()

"""Git log dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gitops
from .commit_list import create_commit_list_pane


def show_logs_dialog(parent, repo):
    """Show commit log for the current branch.

    Args:
        parent: Parent window
        repo: Git repository object
    """
    dialog = Gtk.Dialog(
        title='Git Log',
        transient_for=parent,
        modal=True,
    )
    dialog.set_default_size(800, 500)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)

    content = dialog.get_content_area()
    content.set_margin_start(8)
    content.set_margin_end(8)
    content.set_margin_top(8)
    content.set_margin_bottom(8)
    content.set_spacing(4)

    # --- Top controls row ---
    controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

    count_label = Gtk.Label(label='Commits:')
    controls.pack_start(count_label, False, False, 0)

    count_adj = Gtk.Adjustment(value=50, lower=1, upper=500, step_increment=1, page_increment=10)
    count_spin = Gtk.SpinButton(adjustment=count_adj, climb_rate=1, digits=0)
    count_spin.set_width_chars(5)
    controls.pack_start(count_spin, False, False, 0)

    refresh_btn = Gtk.Button(label='Refresh')
    controls.pack_start(refresh_btn, False, False, 0)

    content.pack_start(controls, False, False, 0)

    # --- Container for log content ---
    log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    log_box.set_vexpand(True)
    content.pack_start(log_box, True, True, 0)

    def _load_log():
        for child in log_box.get_children():
            log_box.remove(child)
            child.destroy()

        max_count = count_spin.get_value_as_int()
        commits = gitops.get_log(repo, max_count=max_count)

        if not commits:
            label = Gtk.Label(label='No commits found')
            label.set_vexpand(True)
            log_box.pack_start(label, True, True, 0)
        else:
            paned = create_commit_list_pane(commits, paned_position=250)
            log_box.pack_start(paned, True, True, 0)

        log_box.show_all()

    refresh_btn.connect('clicked', lambda w: _load_log())

    _load_log()

    dialog.show_all()
    dialog.run()
    dialog.destroy()

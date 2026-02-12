"""Git log dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango


_FORMAT_HELP_TEXT = """\
Commit Hash:
  %H   Full hash
  %h   Abbreviated hash

Author:
  %an  Author name
  %ae  Author email
  %ad  Author date (uses --date= format)

Committer:
  %cn  Committer name
  %ce  Committer email
  %cd  Committer date (uses --date= format)

Subject / Body:
  %s   Subject (first line)
  %b   Body
  %B   Raw body (subject + body)

References:
  %d   Ref names (like "HEAD -> main, origin/main")
  %D   Ref names without wrapping

Tree:
  %t   Abbreviated tree hash
  %T   Full tree hash

Parent:
  %p   Abbreviated parent hashes
  %P   Full parent hashes

Formatting:
  %n   Newline
  %%   Literal %
"""


def _run_log(repo, pretty_fmt, date_fmt, max_count):
    """Run git log and return the output string."""
    try:
        return repo.git.log(
            f'--pretty=format:{pretty_fmt}',
            f'--date=format:{date_fmt}',
            f'-n{max_count}',
        )
    except Exception as e:
        return f'Error: {e}'


def _show_format_help(parent):
    """Show a dialog with format specifier help."""
    dialog = Gtk.Dialog(
        title='Format Specifiers',
        transient_for=parent,
        modal=True,
    )
    dialog.set_default_size(420, 480)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)

    content = dialog.get_content_area()
    content.set_margin_start(8)
    content.set_margin_end(8)
    content.set_margin_top(8)
    content.set_margin_bottom(8)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_vexpand(True)
    scrolled.set_hexpand(True)
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)
    text_view.set_monospace(True)
    text_view.get_buffer().set_text(_FORMAT_HELP_TEXT)

    scrolled.add(text_view)
    content.pack_start(scrolled, True, True, 0)

    dialog.show_all()
    dialog.run()
    dialog.destroy()


def show_logs_dialog(parent, repo):
    """Show formatted git log output.

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
    content.set_spacing(6)

    # --- Top controls row ---
    controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

    # Commit count
    count_label = Gtk.Label(label='Commits:')
    controls.pack_start(count_label, False, False, 0)

    count_adj = Gtk.Adjustment(value=20, lower=1, upper=500, step_increment=1, page_increment=10)
    count_spin = Gtk.SpinButton(adjustment=count_adj, climb_rate=1, digits=0)
    count_spin.set_width_chars(5)
    controls.pack_start(count_spin, False, False, 0)

    # Format string
    fmt_label = Gtk.Label(label='Format:')
    controls.pack_start(fmt_label, False, False, 0)

    fmt_entry = Gtk.Entry()
    fmt_entry.set_text('%h  %cd  %s')
    fmt_entry.set_hexpand(True)
    controls.pack_start(fmt_entry, True, True, 0)

    # Date format
    date_label = Gtk.Label(label='Date:')
    controls.pack_start(date_label, False, False, 0)

    date_entry = Gtk.Entry()
    date_entry.set_text('%Y-%m-%d %H:%M:%S')
    date_entry.set_width_chars(20)
    controls.pack_start(date_entry, False, False, 0)

    # Refresh button
    refresh_btn = Gtk.Button(label='Refresh')
    controls.pack_start(refresh_btn, False, False, 0)

    # Format Help button
    help_btn = Gtk.Button(label='Format Help')
    controls.pack_start(help_btn, False, False, 0)

    content.pack_start(controls, False, False, 0)

    # --- Main text area ---
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_vexpand(True)
    scrolled.set_hexpand(True)
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)
    text_view.set_monospace(True)

    scrolled.add(text_view)
    content.pack_start(scrolled, True, True, 0)

    # --- Callbacks ---
    def refresh(_widget=None):
        pretty_fmt = fmt_entry.get_text()
        date_fmt = date_entry.get_text()
        max_count = count_spin.get_value_as_int()
        output = _run_log(repo, pretty_fmt, date_fmt, max_count)
        text_view.get_buffer().set_text(output)

    refresh_btn.connect('clicked', refresh)
    help_btn.connect('clicked', lambda w: _show_format_help(dialog))

    # Allow Enter in entries to trigger refresh
    fmt_entry.connect('activate', refresh)
    date_entry.connect('activate', refresh)

    # Initial load
    refresh()

    dialog.show_all()
    dialog.run()
    dialog.destroy()

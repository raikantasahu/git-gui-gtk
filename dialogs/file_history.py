"""File history dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

import gitops
from .file_picker import show_file_picker_dialog


def _on_button_press(tree_view, event, context_menu):
    """Handle right-click to show context menu."""
    if event.button == 3:
        path_info = tree_view.get_path_at_pos(int(event.x), int(event.y))
        if path_info:
            path, column, x, y = path_info
            tree_view.get_selection().select_path(path)
            context_menu.popup_at_pointer(event)
            return True
    return False


def _on_copy_hash(menu_item, tree_view):
    """Copy the full hash of the selected commit to clipboard."""
    selection = tree_view.get_selection()
    model, iter_ = selection.get_selected()
    if iter_:
        full_hash = model.get_value(iter_, 4)
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(full_hash, -1)
        clipboard.store()


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
            paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
            paned.set_vexpand(True)

            # Top: commit list
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_hexpand(True)
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

            # Columns: short_hash, date, author, message_line, full_hash (hidden), full_message (hidden)
            store = Gtk.ListStore(str, str, str, str, str, str)
            for c in commits:
                date_str = c['date'][:10] if len(c['date']) >= 10 else c['date']
                first_line = c['message'].split('\n', 1)[0]
                store.append([c['short_hash'], date_str, c['author'], first_line, c['hash'], c['message']])

            tree_view = Gtk.TreeView(model=store)
            tree_view.set_headers_visible(True)

            # Context menu
            context_menu = Gtk.Menu()
            copy_hash_item = Gtk.MenuItem(label='Copy Hash')
            copy_hash_item.connect('activate', _on_copy_hash, tree_view)
            context_menu.append(copy_hash_item)
            context_menu.show_all()

            tree_view.connect('button-press-event',
                              lambda w, e: _on_button_press(w, e, context_menu))

            # Hash column (monospace)
            hash_renderer = Gtk.CellRendererText()
            hash_renderer.set_property('family', 'monospace')
            hash_col = Gtk.TreeViewColumn('Hash', hash_renderer, text=0)
            hash_col.set_resizable(True)
            tree_view.append_column(hash_col)

            # Date column
            date_renderer = Gtk.CellRendererText()
            date_col = Gtk.TreeViewColumn('Date', date_renderer, text=1)
            date_col.set_resizable(True)
            tree_view.append_column(date_col)

            # Author column
            author_renderer = Gtk.CellRendererText()
            author_col = Gtk.TreeViewColumn('Author', author_renderer, text=2)
            author_col.set_resizable(True)
            tree_view.append_column(author_col)

            # Message column
            msg_renderer = Gtk.CellRendererText()
            msg_renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
            msg_col = Gtk.TreeViewColumn('Message', msg_renderer, text=3)
            msg_col.set_expand(True)
            tree_view.append_column(msg_col)

            scrolled.add(tree_view)
            paned.pack1(scrolled, resize=True, shrink=False)

            # Bottom: commit details
            detail_scrolled = Gtk.ScrolledWindow()
            detail_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

            detail_view = Gtk.TextView()
            detail_view.set_editable(False)
            detail_view.set_cursor_visible(False)
            detail_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            detail_view.set_left_margin(6)
            detail_view.set_right_margin(6)
            detail_view.set_top_margin(6)
            detail_view.set_bottom_margin(6)
            detail_view.modify_font(Pango.FontDescription('monospace'))

            detail_scrolled.add(detail_view)
            paned.pack2(detail_scrolled, resize=True, shrink=False)

            paned.set_position(200)

            def on_selection_changed(selection):
                model, iter_ = selection.get_selected()
                buf = detail_view.get_buffer()
                if iter_:
                    short_hash = model.get_value(iter_, 0)
                    date = model.get_value(iter_, 1)
                    author = model.get_value(iter_, 2)
                    full_hash = model.get_value(iter_, 4)
                    message = model.get_value(iter_, 5)
                    text = (
                        f'Commit: {full_hash}\n'
                        f'Author: {author}\n'
                        f'Date:   {date}\n'
                        f'\n{message}\n'
                    )
                    buf.set_text(text)
                else:
                    buf.set_text('')

            tree_view.get_selection().connect('changed', on_selection_changed)

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

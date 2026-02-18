"""Git log dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

import gitops


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

            paned.set_position(250)

            def on_selection_changed(selection):
                model, iter_ = selection.get_selected()
                buf = detail_view.get_buffer()
                if iter_:
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

            log_box.pack_start(paned, True, True, 0)

        log_box.show_all()

    refresh_btn.connect('clicked', lambda w: _load_log())

    _load_log()

    dialog.show_all()
    dialog.run()
    dialog.destroy()

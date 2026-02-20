"""Shared commit list TreeView + details pane widget."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, GtkSource, Pango

import gitops


_STATUS_LABELS = {
    'A': 'Added',
    'M': 'Modified',
    'D': 'Deleted',
    'R': 'Renamed',
    'C': 'Copied',
}


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


def create_commit_list_pane(commits, repo=None, paned_position=200):
    """Build a Gtk.Paned with a commit list TreeView and a details pane.

    Args:
        commits: List of commit dicts with keys: hash, short_hash, author,
            date, message
        repo: Git repository object (needed for diff and file list)
        paned_position: Initial divider position in pixels

    Returns:
        A Gtk.Paned widget ready to pack into a container.
    """
    css = Gtk.CssProvider()
    css.load_from_data(b'.bordered { border: 1px solid @borders; }')
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    outer_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    outer_paned.set_vexpand(True)

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
    scrolled.get_style_context().add_class('bordered')
    outer_paned.pack1(scrolled, resize=True, shrink=False)

    # Bottom section: details + diff/files
    bottom_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)

    # -- Commit details --
    detail_scrolled = Gtk.ScrolledWindow()
    detail_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    detail_scrolled.get_style_context().add_class('bordered')

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
    bottom_paned.pack1(detail_scrolled, resize=False, shrink=False)

    # -- Diff + file list (horizontal paned) --
    diff_files_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

    # Left: diff view
    diff_scrolled = Gtk.ScrolledWindow()
    diff_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    diff_scrolled.get_style_context().add_class('bordered')

    diff_buffer = GtkSource.Buffer()
    lang_manager = GtkSource.LanguageManager.get_default()
    diff_lang = lang_manager.get_language('diff')
    if diff_lang:
        diff_buffer.set_language(diff_lang)
    style_manager = GtkSource.StyleSchemeManager.get_default()
    for scheme_id in ['Adwaita-dark', 'oblivion', 'cobalt', 'classic']:
        scheme = style_manager.get_scheme(scheme_id)
        if scheme:
            diff_buffer.set_style_scheme(scheme)
            break

    diff_view = GtkSource.View(buffer=diff_buffer)
    diff_view.set_editable(False)
    diff_view.set_cursor_visible(False)
    diff_view.set_show_line_numbers(True)
    diff_view.set_monospace(True)
    diff_view.set_wrap_mode(Gtk.WrapMode.NONE)
    diff_view.set_tab_width(4)

    diff_scrolled.add(diff_view)
    diff_files_paned.pack1(diff_scrolled, resize=True, shrink=False)

    # Right: file list
    files_scrolled = Gtk.ScrolledWindow()
    files_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    files_scrolled.get_style_context().add_class('bordered')

    # Columns: status letter, file path
    files_store = Gtk.ListStore(str, str)
    files_tree = Gtk.TreeView(model=files_store)
    files_tree.set_headers_visible(True)

    status_renderer = Gtk.CellRendererText()
    status_renderer.set_property('family', 'monospace')
    status_col = Gtk.TreeViewColumn('Status', status_renderer, text=0)
    status_col.set_resizable(True)
    files_tree.append_column(status_col)

    path_renderer = Gtk.CellRendererText()
    path_renderer.set_property('ellipsize', Pango.EllipsizeMode.MIDDLE)
    path_col = Gtk.TreeViewColumn('File', path_renderer, text=1)
    path_col.set_expand(True)
    files_tree.append_column(path_col)

    files_scrolled.add(files_tree)
    diff_files_paned.pack2(files_scrolled, resize=False, shrink=False)

    bottom_paned.pack2(diff_files_paned, resize=True, shrink=False)
    bottom_paned.set_position(100)

    outer_paned.pack2(bottom_paned, resize=True, shrink=False)
    outer_paned.set_position(paned_position)

    # Map from file path to line offset in the diff text, populated on
    # each commit selection.
    file_line_map = {}

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

            # Load diff and file list for this commit
            _load_commit_diff(full_hash)
            _load_commit_files(full_hash)
        else:
            buf.set_text('')
            diff_buffer.set_text('')
            files_store.clear()
            file_line_map.clear()

    def _load_commit_diff(commit_hash):
        diff_text = gitops.get_commit_diff(repo, commit_hash)
        diff_buffer.set_text(diff_text)
        diff_view.scroll_to_iter(diff_buffer.get_start_iter(), 0.0, False, 0.0, 0.0)

        # Build file -> line number map for jumping
        file_line_map.clear()
        for i, line in enumerate(diff_text.splitlines()):
            if line.startswith('diff --git '):
                # Extract the b/ path from "diff --git a/... b/..."
                parts = line.split(' b/', 1)
                if len(parts) == 2:
                    file_line_map[parts[1]] = i

    def _load_commit_files(commit_hash):
        files_store.clear()
        changed_files = gitops.get_commit_files(repo, commit_hash)
        for status, path in changed_files:
            label = _STATUS_LABELS.get(status, status)
            files_store.append([label, path])

    def on_file_selected(selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        path = model.get_value(iter_, 1)

        # For renames ("old -> new"), use the new path for lookup
        lookup = path
        if ' -> ' in path:
            lookup = path.split(' -> ', 1)[1]

        line_num = file_line_map.get(lookup)
        if line_num is not None:
            it = diff_buffer.get_iter_at_line(line_num)
            diff_view.scroll_to_iter(it, 0.0, True, 0.0, 0.0)
            diff_buffer.place_cursor(it)

    tree_view.get_selection().connect('changed', on_selection_changed)
    files_tree.get_selection().connect('changed', on_file_selected)

    # Set a reasonable default position for the file list pane
    diff_files_paned.set_position(500)

    return outer_paned

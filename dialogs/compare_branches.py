"""Compare branches dialog for Git GUI GTK."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, GtkSource, Pango

import gitops
from dialogs.commit_list import _on_diff_populate_popup


_STATUS_LABELS = {
    'A': 'Added',
    'M': 'Modified',
    'D': 'Deleted',
    'R': 'Renamed',
    'C': 'Copied',
    'T': 'Type Changed',
}


def show_compare_branches_dialog(parent, repo):
    """Show a dialog to compare two branches.

    Args:
        parent: Parent window
        repo: Git repository object
    """
    dialog = Gtk.Dialog(
        title='Compare Branches',
        transient_for=parent,
        modal=True,
    )
    dialog.set_default_size(1100, 750)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)

    content = dialog.get_content_area()
    content.set_margin_start(8)
    content.set_margin_end(8)
    content.set_margin_top(8)
    content.set_margin_bottom(8)
    content.set_spacing(6)

    # --- Gather branches ---
    current_branch = gitops.get_current_branch(repo)
    all_branches = list(gitops.get_branches(repo))
    for remote_name in gitops.get_remotes(repo):
        for rb in gitops.get_remote_branches(repo, remote_name):
            all_branches.append(f'{remote_name}/{rb}')

    # === Top section: branch selectors + Compare button ===
    top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

    branch1_label = Gtk.Label(label='Branch 1:')
    top_box.pack_start(branch1_label, False, False, 0)

    branch1_combo = Gtk.ComboBoxText()
    branch1_combo.append_text('')
    for name in all_branches:
        branch1_combo.append_text(name)
    # Default to current branch
    for i, name in enumerate(all_branches):
        if name == current_branch:
            branch1_combo.set_active(i + 1)  # +1 for empty entry
            break
    top_box.pack_start(branch1_combo, False, False, 0)

    branch2_label = Gtk.Label(label='Branch 2:')
    top_box.pack_start(branch2_label, False, False, 0)

    branch2_combo = Gtk.ComboBoxText()
    branch2_combo.append_text('')
    for name in all_branches:
        branch2_combo.append_text(name)
    top_box.pack_start(branch2_combo, False, False, 0)

    compare_btn = Gtk.Button(label='Compare')
    compare_btn.set_sensitive(False)
    top_box.pack_start(compare_btn, False, False, 0)

    full_diff_check = Gtk.CheckButton(label='Show complete diff')
    top_box.pack_start(full_diff_check, False, False, 0)

    content.pack_start(top_box, False, False, 0)

    # === Middle + Bottom: file list (middle) and diff view (bottom) ===
    paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    paned.set_vexpand(True)

    # --- Middle section: file list ---
    files_scrolled = Gtk.ScrolledWindow()
    files_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    css = Gtk.CssProvider()
    css.load_from_data(b'.bordered { border: 1px solid @borders; }')
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    files_scrolled.get_style_context().add_class('bordered')

    # Columns: status label, file path, raw status letter (hidden)
    files_store = Gtk.ListStore(str, str, str)
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
    paned.pack1(files_scrolled, resize=True, shrink=False)

    # --- Bottom section: diff view ---
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
    diff_view.connect_after('populate-popup', _on_diff_populate_popup)

    diff_scrolled.add(diff_view)
    paned.pack2(diff_scrolled, resize=True, shrink=False)
    paned.set_position(200)

    content.pack_start(paned, True, True, 0)

    # --- State ---
    compare_state = {'branch1': '', 'branch2': '', 'full_diff': ''}
    file_line_map = {}

    def _update_compare_sensitivity(*args):
        b1 = branch1_combo.get_active_text()
        b2 = branch2_combo.get_active_text()
        compare_btn.set_sensitive(bool(b1) and bool(b2) and b1 != b2)

    branch1_combo.connect('changed', _update_compare_sensitivity)
    branch2_combo.connect('changed', _update_compare_sensitivity)

    def _load_full_diff():
        """Load full diff and build file->line map."""
        b1 = compare_state['branch1']
        b2 = compare_state['branch2']
        try:
            full_diff = repo.git.diff(b1, b2)
        except Exception as e:
            full_diff = f'Error: {e}'
        compare_state['full_diff'] = full_diff
        diff_buffer.set_text(full_diff)

        file_line_map.clear()
        for i, dline in enumerate(full_diff.splitlines()):
            if dline.startswith('diff --git '):
                parts = dline.split(' b/', 1)
                if len(parts) == 2:
                    file_line_map[parts[1]] = i

    def _on_compare(btn):
        b1 = branch1_combo.get_active_text()
        b2 = branch2_combo.get_active_text()
        if not b1 or not b2:
            return

        compare_state['branch1'] = b1
        compare_state['branch2'] = b2
        compare_state['full_diff'] = ''
        file_line_map.clear()
        files_store.clear()
        diff_buffer.set_text('')

        # Get changed files via git diff --name-status
        try:
            output = repo.git.diff('--name-status', b1, b2)
        except Exception as e:
            diff_buffer.set_text(f'Error: {e}')
            return

        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status_letter = parts[0].strip()
                file_path = parts[1]
                # Handle renames: R100\told\tnew
                if '\t' in file_path:
                    old, new = file_path.split('\t', 1)
                    file_path = f'{old} -> {new}'
                label = _STATUS_LABELS.get(status_letter[0], status_letter)
                files_store.append([label, file_path, status_letter])

        if full_diff_check.get_active():
            _load_full_diff()

    compare_btn.connect('clicked', _on_compare)

    def _on_full_diff_toggled(check):
        b1 = compare_state['branch1']
        b2 = compare_state['branch2']
        if not b1 or not b2:
            return

        if check.get_active():
            _load_full_diff()
        else:
            file_line_map.clear()
            # Show diff for the currently selected file
            selection = files_tree.get_selection()
            model, iter_ = selection.get_selected()
            if iter_:
                file_path = model.get_value(iter_, 1)
                lookup = file_path
                if ' -> ' in file_path:
                    lookup = file_path.split(' -> ', 1)[1]
                try:
                    file_diff = repo.git.diff(b1, b2, '--', lookup)
                except Exception as e:
                    file_diff = f'Error: {e}'
                diff_buffer.set_text(file_diff)
                diff_view.scroll_to_iter(diff_buffer.get_start_iter(), 0.0, False, 0.0, 0.0)
            else:
                diff_buffer.set_text('')

    full_diff_check.connect('toggled', _on_full_diff_toggled)

    def _on_file_selected(selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        file_path = model.get_value(iter_, 1)
        b1 = compare_state['branch1']
        b2 = compare_state['branch2']
        if not b1 or not b2:
            return

        # For renames, use the new path for lookup
        lookup = file_path
        if ' -> ' in file_path:
            lookup = file_path.split(' -> ', 1)[1]

        if full_diff_check.get_active():
            # Scroll to file in the full diff
            line_num = file_line_map.get(lookup)
            if line_num is not None:
                it = diff_buffer.get_iter_at_line(line_num)
                diff_view.scroll_to_iter(it, 0.0, True, 0.0, 0.0)
                diff_buffer.place_cursor(it)
        else:
            # Show diff for this single file
            try:
                file_diff = repo.git.diff(b1, b2, '--', lookup)
            except Exception as e:
                file_diff = f'Error: {e}'
            diff_buffer.set_text(file_diff)
            diff_view.scroll_to_iter(diff_buffer.get_start_iter(), 0.0, False, 0.0, 0.0)

    files_tree.get_selection().connect('changed', _on_file_selected)

    dialog.show_all()
    dialog.run()
    dialog.destroy()

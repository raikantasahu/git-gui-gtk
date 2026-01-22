"""Action definitions for Git GUI GTK."""

from gi.repository import Gio, Gtk, Gdk


def get_shortcut_label(accel):
    """Convert an accelerator string to a human-readable label.

    Args:
        accel: Accelerator string like '<Ctrl>q'

    Returns:
        Human-readable string like 'Ctrl+Q'
    """
    if not accel:
        return ''
    key, mods = Gtk.accelerator_parse(accel)
    return Gtk.accelerator_get_label(key, mods)


def get_action_shortcut(action_name):
    """Get the shortcut label for an action by name.

    Args:
        action_name: Action name without prefix (e.g., 'open', 'quit')

    Returns:
        Human-readable shortcut string or empty string
    """
    # Check app actions
    for name, shortcuts, _ in APP_ACTIONS:
        if name == action_name and shortcuts:
            return get_shortcut_label(shortcuts[0])

    # Check window actions
    for name, shortcuts, _ in WINDOW_ACTIONS:
        if name == action_name and shortcuts:
            return get_shortcut_label(shortcuts[0])

    return ''


# Action definitions: (name, shortcuts, handler_method_name)
# Shortcuts is a list of accelerators, or None for no shortcut

# Application-level actions (work without a window)
APP_ACTIONS = [
    ('quit', ['<Ctrl>q'], 'quit'),
    ('about', None, '_show_about_from_action'),
]

# Window-level actions (require window to be present)
WINDOW_ACTIONS = [
    # Repository
    ('open', ['<Ctrl>o'], 'show_open_dialog'),
    ('rescan', ['F5', '<Ctrl>r'], 'rescan'),
    ('explore', None, 'explore_repository'),

    # Staging
    ('stage-selected', ['<Ctrl>s'], 'stage_selected'),
    ('unstage-selected', ['<Ctrl>u'], 'unstage_selected'),
    ('stage-all', ['<Ctrl><Shift>a'], 'stage_all'),
    ('unstage-all', ['<Ctrl><Shift>u'], 'unstage_all'),
    ('revert-selected', None, 'revert_selected'),

    # Commit
    ('commit', ['<Ctrl>Return'], 'commit'),
    ('amend', None, 'toggle_amend'),

    # Remote
    ('push', ['<Ctrl>p'], 'show_push_dialog'),
    ('pull', ['<Ctrl><Shift>p'], 'show_pull_dialog'),
    ('fetch', None, 'show_fetch_dialog'),
    ('add-remote', ['<Ctrl>a'], 'show_add_remote_dialog'),
]


def setup_app_actions(app):
    """Register application-level actions.

    Args:
        app: The Gtk.Application instance
    """
    for name, shortcuts, handler_name in APP_ACTIONS:
        action = Gio.SimpleAction.new(name, None)
        handler = getattr(app, handler_name, None)
        if handler:
            action.connect('activate', lambda a, p, h=handler: h())
        app.add_action(action)
        if shortcuts:
            app.set_accels_for_action(f'app.{name}', shortcuts)


def setup_window_actions(app, window):
    """Register window-level actions.

    Args:
        app: The Gtk.Application instance (for setting accelerators)
        window: The Gtk.ApplicationWindow instance
    """
    for name, shortcuts, handler_name in WINDOW_ACTIONS:
        action = Gio.SimpleAction.new(name, None)
        handler = getattr(window, handler_name, None)
        if handler:
            action.connect('activate', lambda a, p, h=handler: h())
        window.add_action(action)
        if shortcuts:
            app.set_accels_for_action(f'win.{name}', shortcuts)

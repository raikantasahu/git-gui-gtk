"""Action definitions for Git GUI GTK."""

from gi.repository import Gio


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
    ('rescan', ['<Ctrl>r', 'F5'], 'rescan'),
    ('explore', None, '_explore_repository'),

    # Staging
    ('stage-selected', ['<Ctrl>s'], '_stage_selected'),
    ('unstage-selected', ['<Ctrl>u'], '_unstage_selected'),
    ('stage-all', ['<Ctrl><Shift>a'], 'stage_all'),
    ('unstage-all', ['<Ctrl><Shift>u'], 'unstage_all'),
    ('revert-selected', None, '_revert_selected'),

    # Commit
    ('commit', ['<Ctrl>Return'], 'do_commit'),
    ('amend', None, 'toggle_amend'),

    # Remote
    ('push', ['<Ctrl>p'], 'do_push'),
    ('pull', ['<Ctrl><Shift>p'], 'do_pull'),
    ('fetch', None, 'do_fetch'),
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

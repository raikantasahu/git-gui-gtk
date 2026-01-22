#!/usr/bin/python3
"""Git GUI GTK - A modern GTK3 replacement for git-gui."""

import sys
import gi

gi.require_version('Gtk', '3.0')

from application import GitGuiApplication


def main():
    """Application entry point."""
    app = GitGuiApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())

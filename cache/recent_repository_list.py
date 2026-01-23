"""Recent repository list management."""

import json
import os


class RecentRepositoryList:
    """Manage recent repositories list."""

    MAX_RECENT = 10
    CONFIG_DIR = os.path.expanduser('~/.config/git-gui-gtk')
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'recent.json')

    @classmethod
    def _ensure_config_dir(cls):
        """Ensure config directory exists."""
        if not os.path.exists(cls.CONFIG_DIR):
            os.makedirs(cls.CONFIG_DIR)

    @classmethod
    def get_recent(cls):
        """Get list of recent repository paths."""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('recent', [])
        except (json.JSONDecodeError, IOError):
            pass
        return []

    @classmethod
    def add_recent(cls, path):
        """Add a repository path to recent list."""
        cls._ensure_config_dir()
        recent = cls.get_recent()

        # Normalize path
        path = os.path.abspath(path)

        # Remove if already exists (will be re-added at front)
        if path in recent:
            recent.remove(path)

        # Add at front
        recent.insert(0, path)

        # Trim to max
        recent = recent[:cls.MAX_RECENT]

        # Save
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump({'recent': recent}, f, indent=2)
        except IOError:
            pass

    @classmethod
    def clear_recent(cls):
        """Clear the recent repositories list."""
        cls._ensure_config_dir()
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump({'recent': []}, f, indent=2)
        except IOError:
            pass

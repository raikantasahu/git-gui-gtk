# Git GUI GTK

A modern GTK3 replacement for the classic `git-gui` tool. Provides a graphical interface for common Git operations with a clean, native look on Linux desktops.

## Features

- **Repository Status View**: See unstaged and staged changes at a glance
- **Diff Viewer**: View file diffs with syntax highlighting
- **Staging**: Stage/unstage individual files or all changes
- **Commits**: Create commits with messages, amend previous commits
- **Branches**: Create, checkout, rename, delete, merge, and rebase branches
- **Remotes**: Add, rename, delete remotes; push, pull, and fetch operations
- **Database Tools**: View statistics, compress, and verify the Git database

## Requirements

### System Dependencies

- Python 3.10+
- GTK 3.0
- GtkSourceView 4

On Debian/Ubuntu:

```bash
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtksource-4
```

On Fedora:

```bash
sudo dnf install python3 python3-gobject gtk3 gtksourceview4
```

On Arch Linux:

```bash
sudo pacman -S python python-gobject gtk3 gtksourceview4
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/raikantasahu/git-gui-gtk.git
   cd git-gui-gtk
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python main.py
   ```

## Usage

### Opening a Repository

Run from within a Git repository:

```bash
cd /path/to/your/repo
python /path/to/git-gui-gtk/main.py
```

Or open a repository via the menu: **Repository > Open...**

### Basic Workflow

1. **View Changes**: Unstaged and staged files appear in the left panel
2. **View Diff**: Click a file to see its diff in the right panel
3. **Stage Files**: Double-click a file or use the context menu to stage/unstage
4. **Commit**: Enter a commit message and click Commit

### Keyboard Shortcuts

- `Ctrl+O` - Open repository
- `F5 or Ctrl+R` - Rescan/refresh
- `Ctrl+Q` - Quit

## Project Structure

```
git-gui-gtk/
├── main.py              # Application entry point
├── application.py       # GtkApplication class
├── window.py            # Main window
├── actions.py           # Menu and keyboard actions
├── config.py            # UI configuration
├── utils.py             # Utility functions
├── gitops/              # Git operations (one function per file)
├── dialogs/             # Dialog windows
└── widgets/             # Custom GTK widgets
    ├── file_list.py     # Staged/unstaged file lists
    ├── diff_view.py     # Diff viewer with syntax highlighting
    └── commit_area.py   # Commit message and buttons
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

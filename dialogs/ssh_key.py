"""SSH key dialog for Git GUI GTK."""

import os
import subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


def _find_ssh_key():
    """Find the user's SSH public key.

    Returns:
        Tuple of (key_content, key_path) or (None, None) if not found
    """
    ssh_dir = os.path.expanduser('~/.ssh')
    key_files = ['id_ed25519.pub', 'id_rsa.pub', 'id_ecdsa.pub', 'id_dsa.pub']

    for key_file in key_files:
        path = os.path.join(ssh_dir, key_file)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return f.read().strip(), path
            except Exception:
                continue
    return None, None


def _show_error(parent, title, message):
    """Show an error dialog."""
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.NONE,
        text=title
    )
    dialog.format_secondary_text(message)
    button_box = dialog.get_action_area()
    button_box.set_layout(Gtk.ButtonBoxStyle.END)
    button_box.set_margin_end(12)
    button_box.set_margin_bottom(12)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)
    dialog.run()
    dialog.destroy()


def _generate_ssh_key_dialog(parent):
    """Show dialog to generate a new SSH key.

    Args:
        parent: Parent window

    Returns:
        True if key was generated, False otherwise
    """
    dialog = Gtk.Dialog(
        title='Generate SSH Key',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(450, 250)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(8)

    # Key type
    type_label = Gtk.Label(label='Key type:')
    type_label.set_xalign(0)
    content.pack_start(type_label, False, False, 0)

    type_combo = Gtk.ComboBoxText()
    type_combo.append('ed25519', 'Ed25519 (recommended)')
    type_combo.append('rsa', 'RSA (4096 bits)')
    type_combo.append('ecdsa', 'ECDSA')
    type_combo.set_active(0)
    content.pack_start(type_combo, False, False, 0)

    # Comment/Email
    comment_label = Gtk.Label(label='Comment (usually your email):')
    comment_label.set_xalign(0)
    content.pack_start(comment_label, False, False, 0)

    comment_entry = Gtk.Entry()
    comment_entry.set_placeholder_text('your_email@example.com')
    content.pack_start(comment_entry, False, False, 0)

    # Passphrase
    pass_label = Gtk.Label(label='Passphrase (optional, leave empty for no passphrase):')
    pass_label.set_xalign(0)
    content.pack_start(pass_label, False, False, 0)

    pass_entry = Gtk.Entry()
    pass_entry.set_visibility(False)
    pass_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
    content.pack_start(pass_entry, False, False, 0)

    # Confirm passphrase
    confirm_label = Gtk.Label(label='Confirm passphrase:')
    confirm_label.set_xalign(0)
    content.pack_start(confirm_label, False, False, 0)

    confirm_entry = Gtk.Entry()
    confirm_entry.set_visibility(False)
    confirm_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
    content.pack_start(confirm_entry, False, False, 0)

    button_box = dialog.get_action_area()
    button_box.set_layout(Gtk.ButtonBoxStyle.END)
    button_box.set_margin_end(12)
    button_box.set_margin_bottom(12)
    dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
    dialog.add_button('Generate', Gtk.ResponseType.OK)

    dialog.show_all()

    while True:
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            key_type = type_combo.get_active_id()
            comment = comment_entry.get_text().strip()
            passphrase = pass_entry.get_text()
            confirm = confirm_entry.get_text()

            if passphrase != confirm:
                _show_error(parent, 'Generate SSH Key', 'Passphrases do not match.')
                continue

            dialog.destroy()

            # Generate the key
            ssh_dir = os.path.expanduser('~/.ssh')
            if not os.path.exists(ssh_dir):
                os.makedirs(ssh_dir, mode=0o700)

            key_file = os.path.join(ssh_dir, f'id_{key_type}')

            if os.path.exists(key_file):
                _show_error(parent, 'Generate SSH Key', f'Key file already exists: {key_file}')
                return False

            try:
                cmd = ['ssh-keygen', '-t', key_type, '-f', key_file, '-N', passphrase]
                if key_type == 'rsa':
                    cmd.extend(['-b', '4096'])
                if comment:
                    cmd.extend(['-C', comment])

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    return True
                else:
                    _show_error(parent, 'Generate SSH Key', f'Failed to generate key:\n{result.stderr}')
                    return False
            except Exception as e:
                _show_error(parent, 'Generate SSH Key', f'Failed to generate key: {e}')
                return False
        else:
            break

    dialog.destroy()
    return False


def show_ssh_key_dialog(parent, on_status=None):
    """Show the user's SSH public key dialog.

    Args:
        parent: Parent window
        on_status: Optional callback(message) to report status

    Returns:
        True if key was copied or generated, False otherwise
    """
    ssh_key, ssh_key_path = _find_ssh_key()

    dialog = Gtk.Dialog(
        title='Your OpenSSH Public Key',
        transient_for=parent,
        modal=True
    )
    dialog.set_default_size(600, 200)

    content = dialog.get_content_area()
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    content.set_spacing(6)

    if ssh_key:
        path_label = Gtk.Label(label=f'Public key from: {ssh_key_path}')
        path_label.set_xalign(0)
        content.pack_start(path_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        text_view.set_monospace(True)
        text_view.get_buffer().set_text(ssh_key)
        scrolled.add(text_view)
        content.pack_start(scrolled, True, True, 0)
    else:
        no_key_label = Gtk.Label(label='No SSH public key found.')
        no_key_label.set_xalign(0)
        content.pack_start(no_key_label, False, False, 0)

    button_box = dialog.get_action_area()
    button_box.set_layout(Gtk.ButtonBoxStyle.END)
    button_box.set_margin_end(12)
    button_box.set_margin_bottom(12)

    if ssh_key:
        dialog.add_button('Copy to Clipboard', Gtk.ResponseType.APPLY)
    else:
        dialog.add_button('Generate Key', Gtk.ResponseType.YES)
    dialog.add_button('Close', Gtk.ResponseType.CLOSE)

    dialog.show_all()

    result = False
    while True:
        response = dialog.run()
        if response == Gtk.ResponseType.APPLY and ssh_key:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(ssh_key, -1)
            clipboard.store()
            if on_status:
                on_status('SSH key copied to clipboard')
            result = True
        elif response == Gtk.ResponseType.YES:
            dialog.destroy()
            if _generate_ssh_key_dialog(parent):
                if on_status:
                    on_status('SSH key generated successfully')
                # Show the new key
                show_ssh_key_dialog(parent, on_status)
                return True
            return False
        else:
            break

    dialog.destroy()
    return result

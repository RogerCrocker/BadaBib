# dialogs.py
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from gi.repository import Adw, Gtk


def add_filters(dialog):
    """
    Add ".bib" and "all files" categories to file chooser dialog.

    Parameters
    ----------
    dialog: Gtk.FileChooserDialog
    """
    filter_bibtex = Gtk.FileFilter()
    filter_bibtex.set_name("BibTeX files")
    filter_bibtex.add_pattern("*.bib")
    dialog.add_filter(filter_bibtex)

    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    dialog.add_filter(filter_all)


class WarningDialog(Adw.AlertDialog):
    """
    A dialog that displays a warning message. The user can only acknowledge
    the message.
    """
    def __init__(self, text, window, title="Bada Bib! - Warning"):
        """
        text: str
            Message text
        window: Gtk.Window
            Parent window of the dialog
        title: str, optional
            Dialog title. The default is "Bada Bib! - Warning".
        """
        super().__init__()
        self.set_heading(title)
        self.set_body(text)
        self.set_body_use_markup(True)
        self.add_response("ok", "OK")
        self.set_close_response("ok")

        self.choose(window, None, self.close)

    @staticmethod
    def close(dialog, response):
        """Close dialog, irrespective of response."""
        dialog.choose_finish(response)
        return None


class SaveChangesDialog(Gtk.MessageDialog):
    """
    Alert user that file contains unsaved changes.
    """
    def __init__(self, window, filename):
        """
        window: Gtk.Window
            Parent window of the dialog
        filename: str
            Name of file with unsaved changes
        """
        super().__init__(
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Save changes to file '{filename}' before closing?",
            title="Bada Bib! - Unsaved Changes",
        )
        self.add_buttons(
            "Close without saving", Gtk.ResponseType.CLOSE,
            "Cancel", Gtk.ResponseType.CANCEL,
            "Save", Gtk.ResponseType.OK,
        )
        self.set_default_response(Gtk.ResponseType.CANCEL)
        self.set_modal(True)


class ConfirmSaveDialog(Gtk.MessageDialog):
    """
    Confirm that user wants to save file, although it contains empty and/or
    duplicate keys.
    """
    def __init__(self, window, filename, has_empty_keys, duplicate_keys):
        """
        window: Gtk.Window
            Parent window of the dialog
        filename: str
            Name of file with empty/duplicate keys
        has_empty_keys: bool
            True if file contains empty keys, False otherwise
        duplicate_keys: list of str
            List of duplicate keys, can be empty
        """
        # Compose case-by-case warning
        if duplicate_keys:
            warning = (
                f"contains {'<b>empty keys</b> and ' if has_empty_keys else ''}"
                + "the following <b>duplicate keys</b>:"
                + "\n\n"
                + "\n".join(duplicate_keys)
            )
        else:
            warning = "contains <b>empty keys</b>."

        text = (
            f"'{filename}'"
            + "\n\n"
            + f"{warning}"
            + "\n\n"
            + "Save anyhow?"
        )

        super().__init__(
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            text=text,
            title="Bada Bib! - Warning",
        )

        self.add_buttons(
            "No", Gtk.ResponseType.NO,
            "Yes", Gtk.ResponseType.YES,
        )

        self.props.use_markup = True
        self.set_modal(True)


class FileChooser(Gtk.FileChooserDialog):
    """
    Customized file chooser.
    """
    def __init__(self, window):
        """
        window: Gtk.Window
            Parent window of the dialog
        """
        super().__init__(
            title="Bada Bib! - Please choose a file",
            transient_for=window,
            action=Gtk.FileChooserAction.OPEN
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        accept_button = self.add_button("Open", Gtk.ResponseType.ACCEPT)
        accept_button.get_style_context().add_class("suggested-action")

        self.set_select_multiple(True)  # Allow selecting multiple files
        add_filters(self)


class SaveDialog(Gtk.FileChooserDialog):
    """
    Customized save dialog.
    """
    def __init__(self, window, filename):
        """
        window: Gtk.Window
            Parent window of the dialog
        filename: str
            File to be saved
        """
        super().__init__(
            title="Bada Bib! - Please choose a file name",
            transient_for=window,
            action=Gtk.FileChooserAction.SAVE,
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        accept_button = self.add_button("Save", Gtk.ResponseType.ACCEPT)
        accept_button.get_style_context().add_class("suggested-action")

        self.set_current_name(filename)  # Suggest name
        add_filters(self)

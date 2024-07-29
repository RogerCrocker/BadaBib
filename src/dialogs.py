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


from gi.repository import Adw, Gio, Gtk


def add_filters(dialog):
    """
    Add ".bib" and "all files" categories to file chooser dialog.

    Parameters
    ----------
    dialog: Gtk.FileDialog
    """
    filter_bibtex = Gtk.FileFilter()
    filter_bibtex.set_name("BibTeX files")
    filter_bibtex.add_pattern("*.bib")

    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")

    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filter_bibtex)
    filters.append(filter_all)
    dialog.set_filters(filters)


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


class SaveChangesDialog(Adw.AlertDialog):
    """
    Alert user that file contains unsaved changes.
    """
    def __init__(self, filename):
        """
        filename: str
            Name of file with unsaved changes
        """
        super().__init__()
        self.set_heading("Bada Bib! - Unsaved Changes")
        self.set_body(f"Save changes to file '{filename}' before closing?")
        self.add_response("close", "Close without saving")
        self.add_response("cancel", "Cancel")
        self.add_response("save", "Save")
        self.set_close_response("cancel")


class ConfirmSaveDialog(Adw.AlertDialog):
    """
    Confirm that user wants to save file, although it contains empty and/or
    duplicate keys.
    """
    def __init__(self, filename, has_empty_keys, duplicate_keys):
        """
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

        super().__init__()
        self.set_heading("Bada Bib! - Warning")
        self.set_body(text)
        self.set_body_use_markup(True)
        self.add_response("no", "No")
        self.add_response("yes", "Yes")
        self.set_close_response("no")


class FileChooser(Gtk.FileDialog):
    """
    Customized file dialog.
    """
    def __init__(self):
        super().__init__(title="Bada Bib! - Please choose a file")
        add_filters(self)


class SaveDialog(Gtk.FileDialog):
    """
    Customized save dialog.
    """
    def __init__(self, filename):
        """
        filename: str
            File to be saved
        """
        super().__init__(title="Bada Bib! - Please choose a file name")
        self.set_initial_name(filename)  # Suggest name
        add_filters(self)

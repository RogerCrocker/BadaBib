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


from platform import python_version

from gi.repository import Gtk, Gio, GLib


def add_filters(dialog):
    filter_bibtex = Gtk.FileFilter()
    filter_bibtex.set_name("BibTeX files")
    filter_bibtex.add_pattern("*.bib")
    dialog.add_filter(filter_bibtex)

    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    dialog.add_filter(filter_all)


class WarningDialog(Gtk.MessageDialog):
    def __init__(self, texts, window, title="Bada Bib! - Warning"):
        if not isinstance(texts, list):
            texts = [texts]
        if len(texts) > 0:
            WarningDialogChain(None, None, texts, window, title)


class WarningDialogChain(Gtk.MessageDialog):
    def __init__(self, dialog, response, texts, window, title="Bada Bib! - Warning", n=0):
        super().__init__(
            transient_for=window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=texts[n],
            title=title,
        )

        if dialog:
            dialog.destroy()

        self.set_modal(True)
        self.props.use_markup = True

        if n < len(texts) - 1:
            self.connect("response", WarningDialogChain, texts, window, title, n+1)
        else:
            self.connect("response", self.end)

        self.show()

    @staticmethod
    def end(dialog, response):
        dialog.destroy()


class SaveChangesDialog(Gtk.MessageDialog):
    def __init__(self, window, filename):
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
    def __init__(self, window, filename, has_empty_keys, duplicate_keys):
        if has_empty_keys:
            if duplicate_keys:
                empty_warning = " <b>empty keys</b> and"
            else:
                empty_warning = " <b>empty keys</b>."
        else:
            empty_warning = ""

        if duplicate_keys:
            duplicate_warning = " the following <b>duplicate keys</b>:\n\n" + "\n".join(duplicate_keys)
        else:
            duplicate_warning = ""

        text = (
            f"File '{filename}' contains{empty_warning}{duplicate_warning}"
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
    def __init__(self, window):
        super().__init__(
            title="Bada Bib! - Please choose a file",
            transient_for=window,
            action=Gtk.FileChooserAction.OPEN
        )
        # cancel button
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)

        # accept button (suggested action -> blue)
        accept_button = self.add_button("Open", Gtk.ResponseType.ACCEPT)
        accept_button.get_style_context().add_class("suggested-action")

        self.set_select_multiple(True)
        add_filters(self)


class SaveDialog(Gtk.FileChooserDialog):
    def __init__(self, window, filename):
        super().__init__(
            title="Bada Bib! - Please choose a file name",
            transient_for=window,
            action=Gtk.FileChooserAction.SAVE,
        )
        # cancel button
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)

        # accept button (suggested action -> blue)
        accept_button = self.add_button("Save", Gtk.ResponseType.ACCEPT)
        accept_button.get_style_context().add_class("suggested-action")

        self.set_current_name(filename)

        add_filters(self)


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, window):
        super().__init__(modal=True, transient_for=window)
        self.set_program_name(self.get_program_name() + " " + window.app.version)

        gtk_version = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        self.set_version(f"Python {python_version()}, GTK {gtk_version}")

        self.set_comments("View, search and edit your BibTeX files")
        self.set_logo_icon_name("com.github.rogercrocker.badabib")
        self.set_website("https://github.com/RogerCrocker/BadaBib")
        self.set_website_label("GitHub Repository")
        self.set_license_type(Gtk.License.GPL_3_0)

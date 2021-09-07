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


import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gio, GLib

from .config_manager import entrytype_dict
from .config_manager import field_dict
from .config_manager import sort_fields

from .store import get_shortest_unique_names


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
    def __init__(self, text, title="Bada Bib! - Warning", window=None):
        Gtk.MessageDialog.__init__(
            self,
            transient_for=window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=text,
            title=title,
        )
        self.props.use_markup = True
        self.run()
        self.destroy()


class SaveChanges(Gtk.MessageDialog):
    def __init__(self, window, filename, quit=False):
        Gtk.MessageDialog.__init__(
            self,
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Save changes to file '" + filename + "' before closing?",
            title="Bada Bib! - Unsaved Changes",
        )
        self.add_buttons(
            "Close without saving", Gtk.ResponseType.CLOSE,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        self.set_default_response(Gtk.ResponseType.CANCEL)


class FileChanged(Gtk.MessageDialog):
    def __init__(self, window, filename):
        Gtk.MessageDialog.__init__(
            self,
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            text="File '" + filename + "' changed on disk.",
            title="Bada Bib! - File Changed on Disk",
        )
        self.add_buttons(
            "Continue Editing", Gtk.ResponseType.YES,
            "Reload", Gtk.ResponseType.NO,
        )


class EmptyKeys(Gtk.MessageDialog):
    def __init__(self, window, filename):
        text = "Entries with empty keys in file '" + filename + "'.\n\n"
        text += "<b>Save anyhow?</b>"

        Gtk.MessageDialog.__init__(
            self,
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            text=text,
            title="Bada Bib! - Empty Keys",
        )
        self.props.use_markup = True
        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO,
            Gtk.STOCK_YES, Gtk.ResponseType.YES,
        )


class DuplicateKeys(Gtk.MessageDialog):
    def __init__(self, window, filename, duplicate_keys):
        text = "Duplicate keys\n\n"
        text += "\n".join(duplicate_keys) + "\n\n"
        text += "in file '" + filename + "'.\n\n"
        text += "<b>Save anyhow?</b>"

        Gtk.MessageDialog.__init__(
            self,
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            text=text,
            title="Bada Bib! - Duplicate Keys",
        )
        self.props.use_markup = True
        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO,
            Gtk.STOCK_YES, Gtk.ResponseType.YES,
        )


class FileChooser(Gtk.FileChooserDialog):
    def __init__(self):
        Gtk.FileChooserDialog.__init__(
            self,
            title="Bada Bib! - Please choose a file",
            action=Gtk.FileChooserAction.OPEN,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        add_filters(self)


class SaveDialog(Gtk.FileChooserDialog):
    def __init__(self):
        Gtk.FileChooserDialog.__init__(
            self,
            title="Bada Bib! - Please choose a file name",
            action=Gtk.FileChooserAction.SAVE,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        self.set_do_overwrite_confirmation(True)
        add_filters(self)


class FilterPopover(Gtk.Popover):
    def __init__(self, button, itemlist):
        Gtk.Popover.__init__(self)
        self.switches = []
        self.itemlist = itemlist
        self.assemble()
        self.set_relative_to(button)
        self.show_all()
        self.popup()

    def assemble(self):
        switch_grid = Gtk.Grid()
        switch_grid.set_row_spacing(3)
        switch_grid.set_column_spacing(3)

        for n, entrytype in enumerate(entrytype_dict):
            switch = Gtk.Switch()
            switch.set_active(self.itemlist.fltr[entrytype])
            switch.connect("state-set", self.on_switch_clicked, entrytype)
            self.switches.append(switch)

            label = Gtk.Label(label=entrytype_dict[entrytype])

            switch_grid.attach(label, 0, n, 1, 1)
            switch_grid.attach(switch, 1, n, 1, 1)

        invert = Gtk.Button.new_with_label("Invert")
        invert.connect("clicked", self.on_invert_clicked)
        invert_box = Gtk.Box()
        invert_box.set_center_widget(invert)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(switch_grid, False, False, 0)
        vbox.pack_start(invert_box, False, False, 5)

        self.add(vbox)

    def on_switch_clicked(self, _switch, state, entrytype):
        self.itemlist.fltr[entrytype] = state
        GLib.idle_add(self.itemlist.invalidate_filter)

    def on_invert_clicked(self, _button):
        for switch in self.switches:
            switch.set_state(not switch.get_state())


class SortPopover(Gtk.Popover):
    def __init__(self, sort_button, itemlist):
        Gtk.Popover.__init__(self)
        self.itemlist = itemlist
        self.assemble()
        self.set_relative_to(sort_button)
        self.show_all()
        self.popup()

    def assemble(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        sort_key_buttons = {sort_fields[0]: None}
        for field in sort_fields:
            radio_button = Gtk.RadioButton.new_from_widget(sort_key_buttons[sort_fields[0]])
            radio_button.set_label(field_dict[field])
            radio_button.connect("toggled", self.on_entrytype_clicked, field)
            sort_key_buttons[field] = radio_button
            vbox.pack_start(radio_button, False, False, 0)

        vbox.pack_start(Gtk.Separator(), False, False, 0)

        reverse_buttons = {False: None}
        for value, label in {False: "Ascending", True: "Descending"}.items():
            radio_button = Gtk.RadioButton.new_from_widget(reverse_buttons[False])
            radio_button.set_label(label)
            radio_button.connect("toggled", self.on_order_clicked, value)
            reverse_buttons[value] = radio_button
            vbox.pack_start(radio_button, False, False, 0)

        sort_key_buttons[self.itemlist.sort_key].set_active(True)
        reverse_buttons[self.itemlist.sort_reverse].set_active(True)

        self.add(vbox)

    def on_entrytype_clicked(self, radio_button, field):
        is_active = radio_button.get_active()
        if is_active and field != self.itemlist.sort_key:
            self.itemlist.sort_key = field
            GLib.idle_add(self.itemlist.invalidate_sort)

    def on_order_clicked(self, radio_button, reverse):
        is_active = radio_button.get_active()
        if is_active and self.itemlist.sort_reverse != reverse:
            self.itemlist.sort_reverse = reverse
            GLib.idle_add(self.itemlist.invalidate_sort)


class RecentModel(Gio.Menu):
    def __init__(self, recent_files):
        Gio.Menu.__init__(self)
        menu_section = Gio.Menu()

        if not recent_files:
            menu_item = Gio.MenuItem()
            menu_item.set_label("No recently opened Files")
            menu_item.set_action_and_target_value("app.dummy", None)
            menu_section.prepend_item(menu_item)
        else:
            short_names = get_shortest_unique_names(recent_files)
            for file, label in short_names.items():
                filename = GLib.Variant.new_string(file)
                menu_item = Gio.MenuItem()
                menu_item.set_label(label.replace("_", "__"))  # gio.menu swallows underscores
                menu_item.set_action_and_target_value("app.open_file", filename)
                menu_section.prepend_item(menu_item)

        self.append_section(None, menu_section)


class MenuPopover(Gtk.Popover):
    def __init__(self):
        Gtk.Popover.__init__(self)

        save_section = Gio.Menu()
        save_section.append("Save All", "save_all")

        settings_section = Gio.Menu()
        settings_section.append("Manage Strings", "manage_strings")
        settings_section.append("Customize Editor", "custom_editor")

        preferences_section = Gio.Menu()
        preferences_section.append("Preferences", "preferences")

        about_section = Gio.Menu()
        about_section.append("Keyboard Shortcuts", "shortcuts")
        about_section.append("About Bada Bib!", "about")

        menu = Gio.Menu()
        menu.append_section(None, save_section)
        menu.append_section(None, settings_section)
        menu.append_section(None, preferences_section)
        menu.append_section(None, about_section)

        self.bind_model(menu, "app")


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, window):
        Gtk.AboutDialog.__init__(self, modal=True, transient_for=window)
        self.set_program_name(self.get_program_name() + " " + window.application.version)

        about_comment = "GTK " + " %d.%d.%d" % (
            Gtk.get_major_version(),
            Gtk.get_minor_version(),
            Gtk.get_micro_version(),
        )
        self.set_comments(about_comment)

        self.set_logo_icon_name("com.github.rogercrocker.badabib")
        self.set_website("https://github.com/RogerCrocker/BadaBib")
        self.set_website_label("GitHub Repository")
        self.set_license_type(Gtk.License.GPL_3_0)

        self.show()

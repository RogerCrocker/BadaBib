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
    def __init__(self, window, filename):
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
            title="Bada Bib! - Empty keys",
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
            title="Bada Bib! - Duplicate keys",
        )
        self.props.use_markup = True
        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO,
            Gtk.STOCK_YES, Gtk.ResponseType.YES,
        )


class FileChooser(Gtk.FileChooserNative):
    def __init__(self, window):
        Gtk.FileChooserNative.__init__(
            self,
            title="Bada Bib! - Please choose a file",
            transient_for=window,
            action=Gtk.FileChooserAction.OPEN,
        )
        add_filters(self)


class SaveDialog(Gtk.FileChooserNative):
    def __init__(self, window):
        Gtk.FileChooserNative.__init__(
            self,
            title="Bada Bib! - Please choose a file name",
            transient_for=window,
            action=Gtk.FileChooserAction.SAVE,
        )
        self.set_do_overwrite_confirmation(True)
        add_filters(self)


class FilterPopover(Gtk.Popover):
    def __init__(self, button, itemlist):
        Gtk.Popover.__init__(self)
        self.set_border_width(5)
        self.switches = []
        self.track_changes = True
        self.itemlist = itemlist
        self.assemble()
        self.set_relative_to(button)
        self.show_all()
        self.popup()

    def assemble(self):
        switch_grid = Gtk.Grid()
        switch_grid.set_row_spacing(3)
        switch_grid.set_column_spacing(5)

        all_active = True
        all_count = 0

        for n, entrytype in enumerate(entrytype_dict, start=1):
            active = self.itemlist.fltr[entrytype]
            if not active and all_active:
                all_active = False
            count = self.itemlist.bibfile.count(entrytype)

            if count > 0:
                all_count += count

                switch = Gtk.Switch()
                switch.set_active(active)
                switch.connect("state-set", self.on_switch_clicked, entrytype)
                self.switches.append(switch)

                label_text = entrytype_dict[entrytype] + " (" + str(count) + ")"
                label = Gtk.Label(label=label_text)

                switch_grid.attach(label, 0, n, 1, 1)
                switch_grid.attach(switch, 1, n, 1, 1)

        # All switch
        if all_count > 0:
            switch = Gtk.Switch()
            switch.set_active(all_active)
            switch.connect("state-set", self.on_switch_clicked, None)
            self.switches.append(switch)

            label_text = "All (" + str(all_count) + ")"
            label = Gtk.Label(label=label_text)

            switch_grid.attach(label, 0, 0, 1, 1)
            switch_grid.attach(switch, 1, 0, 1, 1)
        else:
            label = Gtk.Label(label="Empty File")
            label.set_sensitive(False)
            switch_grid.attach(label, 0, 0, 1, 1)

        self.add(switch_grid)

    def on_switch_clicked(self, switch, state, entrytype):
        if self.track_changes:
            if switch == self.switches[-1]:
                for s in self.switches:
                    s.set_state(state)
            else:
                self.itemlist.fltr[entrytype] = state
                self.track_changes = False
                if not state and self.switches[-1].get_state():
                    self.switches[-1].set_state(False)
                elif all(self.itemlist.fltr.values()):
                    self.switches[-1].set_state(True)
                self.track_changes = True

            GLib.idle_add(self.itemlist.invalidate_filter)


class SortPopover(Gtk.Popover):
    def __init__(self, sort_button, itemlist):
        Gtk.Popover.__init__(self)
        self.set_border_width(5)
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
            menu_item.set_label("No recently opened files")
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

            menu_item = Gio.MenuItem()
            menu_item.set_label("Clear history")
            menu_item.set_action_and_target_value("app.clear_recent", None)
            clear_section = Gio.Menu()
            clear_section.prepend_item(menu_item)
            self.append_section(None, clear_section)

        self.prepend_section(None, menu_section)


class MenuPopover(Gtk.Popover):
    def __init__(self):
        Gtk.Popover.__init__(self)

        save_section = Gio.Menu()
        save_section.append("Save all", "save_all")

        settings_section = Gio.Menu()
        settings_section.append("Manage strings", "manage_strings")
        settings_section.append("Customize editor", "custom_editor")

        preferences_section = Gio.Menu()
        preferences_section.append("Preferences", "preferences")

        about_section = Gio.Menu()
        about_section.append("Keyboard shortcuts", "shortcuts")
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

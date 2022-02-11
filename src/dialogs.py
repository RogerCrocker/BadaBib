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
gi.require_version("Gtk", "4.0")

from platform import python_version

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


class SaveChanges(Gtk.MessageDialog):
    def __init__(self, window, filename):
        super().__init__(
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Save changes to file '{}' before closing?".format(filename),
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
            "File '{}'".format(filename)
            + "contains{}{}".format(empty_warning, duplicate_warning)
            + "\n\n"
            + "Save anyhow?"
        )

        super().__init__(
            transient_for=window,
            message_type=Gtk.MessageType.QUESTION,
            text=text,
            title="Bada Bib! - Empty keys",
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
    def __init__(self, window):
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

        # self.set_do_overwrite_confirmation(True)
        add_filters(self)


class FilterPopover(Gtk.Popover):
    def __init__(self, button, itemlist):
        super().__init__()
        self.set_parent(button)
        self.set_position(Gtk.PositionType.TOP)
        self.switches = []
        self.track_changes = True
        self.itemlist = itemlist
        self.assemble()
        self.popup()

    def assemble(self):
        switch_grid = Gtk.Grid()
        switch_grid.set_row_spacing(3)
        switch_grid.set_column_spacing(5)

        all_active = True
        all_count = self.itemlist.bibfile.count_all()
        n = 1
        count = []

        for entrytype in entrytype_dict:
            active = self.itemlist.fltr[entrytype]
            if not active and all_active:
                all_active = False
            count.append(self.itemlist.bibfile.count(entrytype))

            if count[-1] > 0:
                switch = Gtk.Switch()
                switch.set_active(active)
                switch.connect("state-set", self.on_switch_clicked, entrytype)
                self.switches.append(switch)

                label_text = entrytype_dict[entrytype] + " (" + str(count[-1]) + ")"
                label = Gtk.Label(label=label_text)

                switch_grid.attach(label, 0, n, 1, 1)
                switch_grid.attach(switch, 1, n, 1, 1)

                n += 1

        # Other switch
        delta_count = all_count - sum(count)
        if delta_count > 0:
            switch = Gtk.Switch()
            switch.set_active(self.itemlist.fltr["other"])
            switch.connect("state-set", self.on_switch_clicked, "other")
            self.switches.append(switch)

            label_text = "Other (" + str(delta_count) + ")"
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

        self.set_child(switch_grid)

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
        super().__init__()
        self.set_parent(sort_button)
        self.set_position(Gtk.PositionType.TOP)
        self.itemlist = itemlist
        self.assemble()
        self.popup()

    def assemble(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        sort_key_buttons = {sort_fields[0]: None}
        group = None
        for field in sort_fields:
            radio_button = Gtk.CheckButton.new_with_label(field_dict[field])
            radio_button.connect("toggled", self.on_entrytype_clicked, field)
            if group:
                radio_button.set_group(group)
            else:
                group = radio_button
            sort_key_buttons[field] = radio_button
            vbox.append(radio_button)

        vbox.append(Gtk.Separator())

        reverse_buttons = {False: None}
        group = None
        for value, label in {False: "Ascending", True: "Descending"}.items():
            radio_button = Gtk.CheckButton.new_with_label(label)
            radio_button.connect("toggled", self.on_order_clicked, value)
            if group:
                radio_button.set_group(group)
            else:
                group = radio_button
            reverse_buttons[value] = radio_button
            vbox.append(radio_button)

        sort_key_buttons[self.itemlist.sort_key].set_active(True)
        reverse_buttons[self.itemlist.sort_reverse].set_active(True)

        self.set_child(vbox)

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
        super().__init__()

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


class MenuPopover(Gtk.PopoverMenu):
    def __init__(self):
        super().__init__()

        save_all_item = Gio.MenuItem()
        save_all_item.set_label("Save all")
        save_all_item.set_action_and_target_value("app.save_all", None)

        manage_strings_item = Gio.MenuItem()
        manage_strings_item.set_label("Manage strings")
        manage_strings_item.set_action_and_target_value("app.manage_strings", None)

        custom_editor_item = Gio.MenuItem()
        custom_editor_item.set_label("Customize editor")
        custom_editor_item.set_action_and_target_value("app.custom_editor", None)

        preferences_item = Gio.MenuItem()
        preferences_item.set_label("Preferences")
        preferences_item.set_action_and_target_value("app.preferences", None)

        shortcuts_item = Gio.MenuItem()
        shortcuts_item.set_label("Keyboard shortcuts")
        shortcuts_item.set_action_and_target_value("app.shortcuts", None)

        about_item = Gio.MenuItem()
        about_item.set_label("About Bada Bib!")
        about_item.set_action_and_target_value("app.about", None)

        save_section = Gio.Menu()
        save_section.append_item(save_all_item)

        settings_section = Gio.Menu()
        settings_section.append_item(manage_strings_item)
        settings_section.append_item(custom_editor_item)

        preferences_section = Gio.Menu()
        preferences_section.append_item(preferences_item)

        about_section = Gio.Menu()
        about_section.append_item(shortcuts_item)
        about_section.append_item(about_item)

        menu = Gio.Menu()
        menu.append_section(None, save_section)
        menu.append_section(None, settings_section)
        menu.append_section(None, preferences_section)
        menu.append_section(None, about_section)

        self.set_menu_model(menu)


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, window):
        super().__init__(modal=True, transient_for=window)
        self.set_program_name(self.get_program_name() + " " + window.application.version)

        gtk_version = "{}.{}.{}".format(Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        self.set_version("Python {}, GTK {}".format(python_version(), gtk_version))

        self.set_comments("View, search and edit your BibTeX files")
        self.set_logo_icon_name("com.github.rogercrocker.badabib")
        self.set_website("https://github.com/RogerCrocker/BadaBib")
        self.set_website_label("GitHub Repository")
        self.set_license_type(Gtk.License.GPL_3_0)

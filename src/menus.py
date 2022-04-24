# menus.py
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


from gi.repository import Gtk, Gio, GLib

from .store import get_shortest_unique_names

from .config_manager import entrytype_dict
from .config_manager import field_dict
from .config_manager import sort_fields


def create_menu_item(label, action, target=None):
    item = Gio.MenuItem()
    item.set_label(label)
    item.set_action_and_target_value(f"app.{action}", target)
    return item


class RecentFilesMenu(Gio.Menu):
    def __init__(self, recent_files):
        super().__init__()

        menu_section = Gio.Menu()
        short_names = get_shortest_unique_names(recent_files)
        for file, label in short_names.items():
            filename = GLib.Variant.new_string(file)
            # gio.menu swallows underscores
            menu_item = create_menu_item(label.replace("_", "__"), "open_file", filename)
            menu_section.prepend_item(menu_item)

        menu_item = create_menu_item("Clear history", "clear_recent")
        clear_section = Gio.Menu()
        clear_section.prepend_item(menu_item)
        self.append_section(None, clear_section)

        self.prepend_section(None, menu_section)


class FormMenu(Gio.Menu):
    def __init__(self, field):
        super().__init__()

        title_case = create_menu_item("Title Case", "title_case")
        upper_case = create_menu_item("Upper Case", "upper_case")
        lower_case = create_menu_item("Lower Case", "lower_case")
        sanitize = create_menu_item("Sanitize Ranges", "sanitize_range")
        protect = create_menu_item("Protect Upper Case", "protect_caps")
        unicode = create_menu_item("Convert to Unicode", "to_unicode")
        latex = create_menu_item("Convert to LaTeX", "to_latex")
        key = create_menu_item("Generate Key", "generate_key")

        menu_case = Gio.Menu()
        menu_case.append_item(title_case)
        menu_case.append_item(upper_case)
        menu_case.append_item(lower_case)

        menu_convert = Gio.Menu()
        menu_convert.append_item(protect)
        menu_convert.append_item(unicode)
        menu_convert.append_item(latex)

        menu_customize = Gio.Menu()
        menu_customize.append_section(None, menu_case)
        menu_customize.append_section(None, menu_convert)

        customize_section = Gio.Menu()
        customize_section.append_submenu("Customize", menu_customize)

        if field == "pages":
            customize_section.append_item(sanitize)
        if field == "ID":
            customize_section.append_item(key)

        self.prepend_section(None, customize_section)


class MainMenu(Gtk.PopoverMenu):
    def __init__(self):
        super().__init__()

        manage_strings = create_menu_item("Manage Strings", "manage_strings")
        custom_editor = create_menu_item("Customize Editor", "custom_editor")
        preferences = create_menu_item("Preferences", "show_prefs")
        shortcuts = create_menu_item("Keyboard Shortcuts", "show_shortcuts")
        save_all = create_menu_item("Save All", "save_all")
        about = create_menu_item("About Bada Bib!", "show_about")

        save_section = Gio.Menu()
        save_section.append_item(save_all)

        settings_section = Gio.Menu()
        settings_section.append_item(manage_strings)
        settings_section.append_item(custom_editor)

        preferences_section = Gio.Menu()
        preferences_section.append_item(preferences)

        about_section = Gio.Menu()
        about_section.append_item(shortcuts)
        about_section.append_item(about)

        menu = Gio.Menu()
        menu.append_section(None, save_section)
        menu.append_section(None, settings_section)
        menu.append_section(None, preferences_section)
        menu.append_section(None, about_section)

        self.set_menu_model(menu)


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

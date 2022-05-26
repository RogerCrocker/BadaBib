# preferences.py
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


from gi.repository import Gtk, Adw

from .config_manager import get_align_fields
from .config_manager import set_align_fields
from .config_manager import get_field_indent
from .config_manager import set_field_indent
from .config_manager import get_highlight_syntax
from .config_manager import set_highlight_syntax
from .config_manager import get_parse_on_fly
from .config_manager import set_parse_on_fly
from .config_manager import get_create_backup
from .config_manager import set_create_backup
from .config_manager import get_remember_strings
from .config_manager import set_remember_strings


class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, main_window):
        super().__init__(title="Preferences")
        self.main_window = main_window

        self.set_size_request(600, 650)

        page = Adw.PreferencesPage.new()
        page.set_title("Preferences")

        page.add(self.get_group_general())
        page.add(self.get_group_source())

        self.add(page)

        self.show()

    @staticmethod
    def assemble_action_row(title, subtitle, state, callback):
        row = Adw.ActionRow.new()
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)

        switch = Gtk.Switch()
        switch.set_active(state)
        switch.set_valign(Gtk.Align.CENTER)
        switch.connect("state-set", callback)

        box = row.get_child()
        box.append(switch)

        return row

    def assemble_indent_row(self):
        row = Adw.ActionRow.new()
        row.set_title("Indentation Width")
        row.set_subtitle("Set indentation width of fields.")

        spin_button = Gtk.SpinButton.new_with_range(0, 20, 1)
        spin_button.set_valign(Gtk.Align.CENTER)
        spin_button.set_value(get_field_indent())
        spin_button.set_can_focus(False)
        spin_button.connect("value_changed", self.on_indent_changed)

        box = row.get_child()
        box.append(spin_button)

        return row

    def get_group_general(self):
        title = "Dark Theme"
        subtitle = "Use dark Adaita color scheme."
        state = Adw.StyleManager.get_default().get_property("dark")
        callback = self.on_theme_changed
        theme_row = self.assemble_action_row(title, subtitle, state, callback)

        title = "Create Backups"
        subtitle = "Create backups when opening a file. Highly recommendend!"
        state = get_create_backup()
        callback = self.on_backup_changed
        backup_row = self.assemble_action_row(title, subtitle, state, callback)

        title = "Remember Strings"
        subtitle = "Remember imported string definitions between session."
        state = get_remember_strings()
        callback = self.on_strings_changed
        string_row = self.assemble_action_row(title, subtitle, state, callback)

        group = Adw.PreferencesGroup.new()
        group.set_title("General")
        group.add(theme_row)
        group.add(backup_row)
        group.add(string_row)

        return group

    def get_group_source(self):
        title = "Align Fields"
        subtitle = """Align fields along the "=" sign."""
        state = get_align_fields()
        callback = self.on_align_changed
        align_row = self.assemble_action_row(title, subtitle, state, callback)

        title = "Parse BibTeX code on the fly"
        subtitle = "Disable if editing is sluggish, for example, if a file contains many strings."
        stae = get_parse_on_fly()
        callback = self.on_parse_changed
        parse_row = self.assemble_action_row(title, subtitle, state, callback)

        title = "Highlight Syntax"
        subtitle = "Use syntax highlighting for BibTeX entries."
        state = get_highlight_syntax()
        callback = self.on_syntax_changed
        syntax_row = self.assemble_action_row(title, subtitle, state, callback)

        indent_row = self.assemble_indent_row()

        group = Adw.PreferencesGroup.new()
        group.set_title("BibTeX Source")
        group.add(align_row)
        group.add(parse_row)
        group.add(syntax_row)
        group.add(indent_row)

        return group

    def update_writer(self):
        for file in self.main_window.store.bibfiles.values():
            file.writer = file.store.get_default_writer()
        item = self.main_window.main_widget.get_current_item()
        if item:
            item.update_bibtex()
            self.main_window.main_widget.source_view.update(item)

    @staticmethod
    def on_theme_changed(_switch, dark):
        style_manager = Adw.StyleManager.get_default()
        if dark:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

    @staticmethod
    def on_backup_changed(_switch, state):
        set_create_backup(state)

    @staticmethod
    def on_strings_changed(_switch, state):
        set_remember_strings(state)

    def on_align_changed(self, _switch, state):
        set_align_fields(state)
        self.update_writer()

    def on_syntax_changed(self, _switch, state):
        set_highlight_syntax(state)
        self.main_window.main_widget.source_view.highlight_syntax()

    def on_indent_changed(self, spin_button):
        set_field_indent(spin_button.get_value())
        self.update_writer()

    def on_parse_changed(self, _switch, state):
        set_parse_on_fly(state)
        if state:
            mode = "online"
        else:
            mode = "offline"
        self.main_window.main_widget.source_view.set_mode(mode)   

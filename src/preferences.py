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


import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from .config_manager import get_align_fields
from .config_manager import set_align_fields
from .config_manager import get_field_indent
from .config_manager import set_field_indent
from .config_manager import get_parse_on_fly
from .config_manager import set_parse_on_fly
from .config_manager import get_create_backup
from .config_manager import set_create_backup
from .config_manager import get_remember_strings
from .config_manager import set_remember_strings


class PreferencesWindow(Gtk.Window):
    def __init__(self, main_window):
        super().__init__(transient_for=main_window, title="Preferences")
        self.main_window = main_window

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.get_align())
        box.append(self.get_indent())
        box.append(self.get_strings())
        box.append(self.get_parse())
        box.append(self.get_backup())

        self.set_size_request(500, 350)

        self.set_child(box)

        self.show()

    def update_writer(self):
        for file in self.main_window.store.bibfiles.values():
            file.writer = file.store.get_default_writer()
        item = self.main_window.main_widget.get_current_item()
        item.update_bibtex()
        self.main_window.main_widget.source_view.update(item)

    def get_align(self):
        align_label = Gtk.Label(xalign=0)
        align_label.set_text("Align fields")
        align_label.set_hexpand(True)

        align_hint = Gtk.Label(xalign=0)
        align_hint.set_markup("""<small>Align fields in the BibTeX source code along the "=" sign.</small>""")
        align_hint.set_hexpand(True)

        align_switch = Gtk.Switch()
        align_switch.set_active(get_align_fields())
        align_switch.connect("state-set", self.on_align_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.append(align_label)
        vbox1.append(align_hint)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.append(align_switch)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.append(vbox1)
        box.append(vbox2)

        return box

    def on_align_changed(self, _switch, state):
        set_align_fields(state)
        self.update_writer()

    def get_indent(self):
        indent_label = Gtk.Label(xalign=0)
        indent_label.set_text("Indentation width")
        indent_label.set_hexpand(True)

        indent_hint = Gtk.Label(xalign=0)
        indent_hint.set_markup("<small>Set indentation width of fields in the BibTeX source code.</small>")
        indent_hint.set_hexpand(True)

        indent_spin = Gtk.SpinButton.new_with_range(0, 20, 1)
        indent_spin.set_value(get_field_indent())
        indent_spin.set_can_focus(False)
        indent_spin.connect("value_changed", self.on_indent_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.append(indent_label)
        vbox1.append(indent_hint)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.append(indent_spin)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(10)
        box.append(vbox1)
        box.append(vbox2)

        return box

    def on_indent_changed(self, button):
        set_field_indent(button.get_value())
        self.update_writer()

    def get_parse(self):
        parse_label = Gtk.Label(xalign=0)
        parse_label.set_text("Parse BibTeX code on the fly")
        parse_label.set_hexpand(True)

        parse_hint = Gtk.Label(xalign=0)
        parse_hint.set_markup("<small>Disable if editing the source code of BibTeX entries is sluggish.\nThis can be the case if a file contains many strings.</small>")
        parse_hint.set_justify(Gtk.Justification.LEFT)
        parse_hint.set_hexpand(True)

        parse_switch = Gtk.Switch()
        parse_switch.set_active(get_parse_on_fly())
        parse_switch.connect("state-set", self.on_parse_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.append(parse_label)
        vbox1.append(parse_hint)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.append(parse_switch)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.append(vbox1)
        box.append(vbox2)

        return box

    def on_parse_changed(self, _switch, state):
        set_parse_on_fly(state)
        if state:
            mode = "online"
        else:
            mode = "offline"
        self.main_window.main_widget.source_view.set_mode(mode)

    def get_backup(self):
        backup_label = Gtk.Label(xalign=0)
        backup_label.set_text("Create backups when opening BibTeX files.")
        backup_label.set_hexpand(True)

        backup_hint = Gtk.Label(xalign=0)
        backup_hint.set_markup("<small>Highly recommendend!\nBada Bib! is still under development, so it might mess with your files.</small>")
        backup_hint.set_justify(Gtk.Justification.LEFT)
        backup_hint.set_hexpand(True)

        backup_switch = Gtk.Switch()
        backup_switch.set_active(get_create_backup())
        backup_switch.connect("state-set", self.on_backup_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.append(backup_label)
        vbox1.append(backup_hint)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.append(backup_switch)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.append(vbox1)
        box.append(vbox2)

        return box

    @staticmethod
    def on_backup_changed(_switch, state):
        set_create_backup(state)

    def get_strings(self):
        strings_label = Gtk.Label(xalign=0)
        strings_label.set_text("Remember imported strings between sessions.")
        strings_label.set_hexpand(True)

        strings_hint = Gtk.Label(xalign=0)
        strings_hint.set_markup("<small>Enable to remember imported string definitions between session.</small>")
        strings_hint.set_justify(Gtk.Justification.LEFT)
        strings_hint.set_hexpand(True)

        strings_switch = Gtk.Switch()
        strings_switch.set_active(get_remember_strings())
        strings_switch.connect("state-set", self.on_strings_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.append(strings_label)
        vbox1.append(strings_hint)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.append(strings_switch)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.append(vbox1)
        box.append(vbox2)

        return box

    @staticmethod
    def on_strings_changed(_switch, state):
        set_remember_strings(state)

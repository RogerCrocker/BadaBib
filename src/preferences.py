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
gi.require_version("Gtk", "3.0")

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
        Gtk.Window.__init__(self, transient_for=main_window, title="Preferences")
        self.main_window = main_window
        self.set_border_width(10)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self.get_align(), False, False, 15)
        box.pack_start(self.get_indent(), False, False, 15)
        box.pack_start(self.get_strings(), False, False, 15)
        box.pack_start(self.get_parse(), False, False, 15)
        box.pack_start(self.get_backup(), False, False, 15)

        self.add(box)
        self.show_all()

    def update_writer(self):
        for file in self.main_window.store.bibfiles.values():
            file.writer = file.store.get_default_writer()
        item = self.main_window.main_widget.get_current_item()
        item.update_bibtex()
        self.main_window.main_widget.source_view.update(item)

    def get_align(self):
        align_label = Gtk.Label(xalign=0)
        align_label.set_text("Align fields")

        align_hint = Gtk.Label(xalign=0)
        align_hint.set_markup("""<small>Align fields in the BibTeX source code along the "=" sign.</small>""")

        align_switch = Gtk.Switch()
        align_switch.set_active(get_align_fields())
        align_switch.connect("state-set", self.on_align_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.pack_start(align_label, False, False, 0)
        vbox1.pack_start(align_hint, False, False, 0)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.pack_start(align_switch, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(vbox1, False, False, 10)
        box.pack_end(vbox2, False, False, 10)

        return box

    def on_align_changed(self, _switch, state):
        set_align_fields(state)
        self.update_writer()

    def get_indent(self):
        indent_label = Gtk.Label(xalign=0)
        indent_label.set_text("Indentation width")

        indent_hint = Gtk.Label(xalign=0)
        indent_hint.set_markup("<small>Set indentation width of fields in the BibTeX source code.</small>")

        indent_spin = Gtk.SpinButton.new_with_range(0, 20, 1)
        indent_spin.set_value(get_field_indent())
        indent_spin.set_can_focus(False)
        indent_spin.connect("value_changed", self.on_indent_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.pack_start(indent_label, False, False, 0)
        vbox1.pack_start(indent_hint, False, False, 0)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.pack_start(indent_spin, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(vbox1, False, False, 10)
        box.pack_end(vbox2, False, False, 10)

        return box

    def on_indent_changed(self, button):
        set_field_indent(button.get_value())
        self.update_writer()

    def get_parse(self):
        parse_label = Gtk.Label(xalign=0)
        parse_label.set_text("Parse BibTeX code on the fly")

        parse_hint = Gtk.Label(xalign=0)
        parse_hint.set_markup("<small>Disable if editing the source code of BibTeX entries is sluggish.\nThis can be the case if a file contains many strings.</small>")
        parse_hint.set_justify(Gtk.Justification.LEFT)

        parse_switch = Gtk.Switch()
        parse_switch.set_active(get_parse_on_fly())
        parse_switch.connect("state-set", self.on_parse_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.pack_start(parse_label, False, False, 0)
        vbox1.pack_start(parse_hint, False, False, 0)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.pack_start(parse_switch, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(vbox1, False, False, 10)
        box.pack_end(vbox2, False, False, 10)
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

        backup_hint = Gtk.Label(xalign=0)
        backup_hint.set_markup("<small>Highly recommendend!\nBada Bib! is still under development, so it might mess with your files.</small>")
        backup_hint.set_justify(Gtk.Justification.LEFT)

        backup_switch = Gtk.Switch()
        backup_switch.set_active(get_create_backup())
        backup_switch.connect("state-set", self.on_backup_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.pack_start(backup_label, False, False, 0)
        vbox1.pack_start(backup_hint, False, False, 0)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.pack_start(backup_switch, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(vbox1, False, False, 10)
        box.pack_end(vbox2, False, False, 10)
        return box

    @staticmethod
    def on_backup_changed(_switch, state):
        set_create_backup(state)

    def get_strings(self):
        strings_label = Gtk.Label(xalign=0)
        strings_label.set_text("Remember imported strings between sessions.")

        strings_hint = Gtk.Label(xalign=0)
        strings_hint.set_markup("<small>Enable to remember imported string definitions between session.</small>")
        strings_hint.set_justify(Gtk.Justification.LEFT)

        strings_switch = Gtk.Switch()
        strings_switch.set_active(get_remember_strings())
        strings_switch.connect("state-set", self.on_strings_changed)

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox1.pack_start(strings_label, False, False, 0)
        vbox1.pack_start(strings_hint, False, False, 0)

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox2.pack_start(strings_switch, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(vbox1, False, False, 10)
        box.pack_end(vbox2, False, False, 10)
        return box

    @staticmethod
    def on_strings_changed(_switch, state):
        set_remember_strings(state)

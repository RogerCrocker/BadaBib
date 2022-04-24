# editor.py
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


from gi.repository import Gtk

from .config_manager import field_dict

from .forms import fields_to_forms
from .forms import has_entry
from .forms import has_buffer
from .forms import is_entry

from .change import Change


class Editor(Gtk.ScrolledWindow):
    def __init__(self, layout, entrytype=None):
        super().__init__()
        self.set_vexpand(True)
        self.app = Gtk.Application.get_default()

        self.grid = Gtk.Grid()
        self.set_child(self.grid)

        self.entrytype = entrytype
        self.active = True
        self.track_changes = True
        self.forms = {}
        self.current_item = None
        self.current_form = None

        self.set_spacings()
        self.apply_layout(layout)
        if entrytype:
            self.connect_forms()
            self.set_active(False)

    def set_spacings(self):
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(5)
        self.grid.set_margin_top(10)
        self.grid.set_margin_bottom(10)
        self.grid.set_margin_start(10)
        self.grid.set_margin_end(10)

    def apply_layout(self, layout):
        max_width = max([len(fields) for fields in layout])
        left = top = 0
        for fields in layout:
            width = max_width // len(fields)
            forms = fields_to_forms(fields, self)
            for field, form in zip(fields, forms):
                if field == "separator":
                    self.grid.attach(form, left, top, 2 * max_width, 1)
                    break
                self.add_field_with_form(field, form, left, top, 2 * width)
                left += 2 * width
                self.forms[field] = form
            top += 1
            left = 0
        return True

    def add_field_with_form(self, field, form, left, top, width):
        if field_dict[field]:
            label = Gtk.Label(label=field_dict[field])
            self.grid.attach(label, left, top, 1, 1)
            left += 1
            width -= 1

        self.grid.attach(form, left, top, width, 1)

    def connect_forms(self):
        for field, form in self.forms.items():
            if field in has_entry:
                entry = form.get_child()
                entry.connect("changed", self.update_item, form)
            if field in has_buffer:
                buffer = form.get_buffer()
                buffer.connect("changed", self.update_item, form)
            if field in is_entry:
                form.connect("changed", self.update_item, form)
            form.event_controller_focus.connect("enter", self.on_enter, form)
            form.event_controller_focus.connect("leave", self.on_leave, form)

    def show_item(self, item):
        self.current_item = item
        for form in self.forms.values():
            form.update(item)

    def clear(self):
        self.track_changes = False
        for form in self.forms.values():
            form.clear()
        self.track_changes = True
        self.set_active(False)

    def set_active(self, state):
        if self.active != state:
            for form in self.forms.values():
                form.set_sensitive(state)
            self.active = state

    def update_item(self, _widget, form):
        if self.track_changes:
            item = self.current_item
            if form.field in item.entry:
                old_value = item.entry[form.field]
            else:
                old_value = ""
            new_value = form.get_text()
            # work around strange combobox behavior
            empty_entry = form.field in has_entry and not new_value
            if not empty_entry and old_value != new_value:
                change = Change.Edit(item, form, old_value, new_value)
                item.bibfile.itemlist.change_buffer.push_change(change)

    def on_enter(self, _event_controller_focus, current_form):
        self.current_form = current_form
        self.app.enable_menu_actions(current_form.get_text() != "")
        for form in self.forms.values():
            if form != current_form:
                form.deselect()
        return False

    def on_leave(self, _event_controller_focus, current_form):
        self.current_form = None
        return False

# forms.py
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

from gi.repository import Gtk, Gio

from .config_manager import StringStatus
from .config_manager import SourceViewStatus
from .config_manager import entrytype_dict
from .config_manager import field_dict
from .config_manager import month_dict
from .config_manager import get_parse_on_fly


has_entry = ["ENTRYTYPE", "month"]
has_buffer = ["abstract"]
is_not_entry = has_entry + has_buffer + ["separator"]
is_entry = [field for field in field_dict if field not in is_not_entry]


def fields_to_forms(fields, editor):
    forms = []
    for field in fields:
        if field == "newrow":
            form = None
        elif field == "separator":
            form = Separator()
        elif field == "ENTRYTYPE":
            form = EntrytypeBox(field, editor)
        elif field == "month":
            form = MonthBox(field, editor)
        elif field == "abstract":
            form = MultiLine(field, editor)
        else:
            form = SingleLine(field, editor)
        forms.append(form)
    return forms


class MultiLine(Gtk.TextView):
    def __init__(self, field, editor):
        Gtk.TextView.__init__(self)
        self.field = field
        self.editor = editor
        self.set_hexpand(True)
        self.set_size_request(200, 100)
        self.set_margin_top(5)
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self.set_editable(True)
        self.set_monospace(True)

    def get_text(self):
        textbuffer = self.get_buffer()
        start, end = textbuffer.get_bounds()
        return textbuffer.get_text(start, end, True)

    def set_text(self, text):
        textbuffer = self.get_buffer()
        textbuffer.set_text(text)

    def apply(self, func, n=0):
        window = self.get_toplevel()
        itemlist = window.main_widget.get_current_itemlist()
        bibstrings = itemlist.bibfile.database.strings

        textbuffer = self.get_buffer()
        bounds = textbuffer.get_selection_bounds()

        if bounds:
            selection = textbuffer.get_text(bounds[0], bounds[1], True)
            new_selection = func(selection, bibstrings, n)
            textbuffer.delete(bounds[0], bounds[1])
            textbuffer.insert(bounds[0], new_selection, -1)

    def deselect(self):
        buffer = self.get_buffer()
        _, end = buffer.get_bounds()
        buffer.select_range(end, end)

    def select(self):
        buffer = self.get_buffer()
        start, end = buffer.get_bounds()
        buffer.select_range(start, end)

    def update(self, item):
        self.editor.set_active(True)
        self.editor.current_item = item

        self.editor.track_changes = False
        raw_value = item.raw_field(self.field)
        if raw_value is None:
            self.set_text("")
        elif self.get_text() != raw_value:
            self.set_text(raw_value)
        self.editor.track_changes = True

    def clear(self):
        self.set_text("")

    def update_text(self, _=None):
        pass  # implemented by child class

    def update_icon(self, _=None):
        pass  # not implemented

    def set_icon(self, _=None):
        pass  # not implemented


class SingleLine(Gtk.Entry):
    def __init__(self, field, editor):
        Gtk.Entry.__init__(self)
        self.field = field
        self.editor = editor
        self.set_icon(False)
        self.set_hexpand(True)

    def apply(self, func, n=0):
        window = self.get_toplevel()
        itemlist = window.main_widget.get_current_itemlist()
        bibstrings = itemlist.bibfile.database.strings

        bounds = self.get_selection_bounds()
        text = self.get_text()
        if bounds:
            offset = len(text) - bounds[1]
            prefix = text[: bounds[0]]
            selection = text[bounds[0] : bounds[1]]
            postfix = text[bounds[1] :]
            new_selection = func(selection, bibstrings, n)
            new_text = prefix + new_selection + postfix
            pos = len(new_text) - offset
        else:
            new_text = func(text, bibstrings, n)
            pos = -1
        self.set_text(new_text)
        self.set_position(pos)

    def deselect(self):
        self.select_region(-1, -1)

    def select(self):
        self.select_region(0, -1)

    def update(self, item):
        self.update_text(item)
        self.update_icon(item)

    def update_text(self, item):
        self.editor.set_active(True)
        self.editor.current_item = item

        self.editor.track_changes = False
        raw_value = item.raw_field(self.field)
        if not raw_value:
            self.set_text("")
        elif self.get_text() != raw_value:
            self.set_text(raw_value)
        self.editor.track_changes = True

    def update_icon(self, item):
        pos = Gtk.EntryIconPosition.SECONDARY
        string_status = item.bibstring_status(self.field)
        if string_status:
            if string_status == StringStatus.defined:
                tooltip = item.pretty_field(self.field)
            else:
                tooltip = "Undefined string"
            self.set_icon(string_status)
            self.set_icon_tooltip_text(pos, tooltip)
        else:
            self.set_icon(False)
            self.set_icon_tooltip_text(pos, None)

    def set_icon(self, string_status):
        if string_status == StringStatus.defined:
            icon_name = "font-x-generic-symbolic"
        elif string_status == StringStatus.undefined:
            icon_name = "dialog-warning-symbolic"
        else:
            icon_name = None
        pos = Gtk.EntryIconPosition.SECONDARY
        self.set_icon_from_icon_name(pos, icon_name)

    def clear(self):
        self.set_text("")
        self.set_icon(None)


class Box(Gtk.ComboBoxText):
    def __init__(self, field, editor):
        Gtk.ComboBoxText.__init__(self, has_entry=True)
        self.field = field
        self.editor = editor
        self.set_hexpand(True)

    def get_text(self):
        return self.get_active_text()

    def set_text(self, text):
        entry = self.get_child()
        entry.set_text(text)

    def deselect(self):
        entry = self.get_child()
        entry.select_region(-1, -1)

    def select(self):
        entry = self.get_child()
        entry.select_region(0, -1)

    def add_options(self, opt_dict):
        for opt in opt_dict:
            self.append_text(opt_dict[opt])

    def clear(self):
        self.set_text("")


class EntrytypeBox(Box):
    def __init__(self, field, editor):
        Box.__init__(self, field, editor)
        entry = self.get_child()
        entry.set_editable(False)
        self.add_options(entrytype_dict)
        self.set_text(editor.entrytype)

    def get_text(self):
        value = self.get_active_text()
        for key in entrytype_dict:
            if value == entrytype_dict[key]:
                return key
        return value

    def set_text(self, text):
        entry = self.get_child()
        if text in entrytype_dict:
            entry.set_text(entrytype_dict[text])
            self.set_active(list(entrytype_dict).index(text))
        elif text is not None:
            entry.set_text(text)
            self.set_icon(text != "")  # warn about non-empty, non-standard types

    def set_icon(self, status):
        if status:
            icon_name = "dialog-warning-symbolic"
            tooltip = "This entry type is non-standard and might not be fully supported by Bada Bib!"
        else:
            icon_name = None
            tooltip = None
        pos = Gtk.EntryIconPosition.SECONDARY
        entry = self.get_child()
        entry.set_icon_from_icon_name(pos, icon_name)
        entry.set_icon_tooltip_text(pos, tooltip)

    def update(self, item):
        window = self.get_toplevel()
        editor = window.main_widget.get_current_editor()
        entrytype = item.raw_field("ENTRYTYPE")

        if entrytype == self.editor.entrytype == editor.entrytype:
            self.editor.track_changes = False
            self.set_text(entrytype)
            self.editor.track_changes = True
        else:
            editor = window.main_widget.show_editor(entrytype)
            editor.show_item(item)

    def clear(self):
        self.set_text("")


class MonthBox(Box):
    def __init__(self, field, editor):
        Box.__init__(self, field, editor)
        self.add_options(month_dict)

    def get_text(self):
        value = self.get_active_text()
        for key in month_dict:
            if value == month_dict[key]:
                return key
        return value

    def set_text(self, text):
        entry = self.get_child()
        if text and text.lower() in month_dict:
            entry.set_text(month_dict[text.lower()])
            self.set_active(list(month_dict.keys()).index(text.lower()))
        elif text:
            entry.set_text(text)
        else:
            entry.set_text("")

    def update(self, item):
        self.editor.set_active(True)
        self.editor.current_item = item
        if item.raw_field(self.field) != self.get_text():
            self.editor.track_changes = False
            self.set_text(item.raw_field(self.field))
            self.editor.track_changes = True

    def clear(self):
        self.set_text("")


class Separator(Gtk.Separator):
    def __init__(self):
        Gtk.Separator.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self.set_margin_top(5)
        self.set_margin_bottom(5)


class SourceView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.set_vexpand(False)
        self.status = SourceViewStatus.empty
        self.form = MultiLine("source", None)
        self.buffer = self.form.get_buffer()

        source_view_scrolled = Gtk.ScrolledWindow()
        source_view_scrolled.set_propagate_natural_width(True)
        source_view_scrolled.add(self.form)

        self.assemble_offline_bar()
        self.assemble_online_bar()

        self.mode = "online"
        self.pack_start(source_view_scrolled, True, True, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)
        self.pack_end(self.online_bar, False, False, 5)

        if get_parse_on_fly():
            self.set_mode("online")
        else:
            self.set_mode("offline")

    def set_mode(self, mode):
        if mode == "online" and self.mode != "online":
            self.remove(self.offline_bar)
            self.pack_end(self.online_bar, False, False, 5)
            self.mode = "online"
            self.set_status(self.status, True)

        if mode == "offline" and self.mode != "offline":
            self.remove(self.online_bar)
            self.pack_end(self.offline_bar, False, False, 5)
            self.mode = "offline"
            self.set_status(self.status, True)

        self.show_all()

    def assemble_online_bar(self):
        self.icon_size = Gtk.IconSize.LARGE_TOOLBAR
        self.status_icon = Gtk.Image()

        self.online_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.online_bar.set_center_widget(self.status_icon)

    def assemble_offline_bar(self):
        self.apply_button = Gtk.Button.new_with_label("Apply")
        self.apply_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.apply_button.set_sensitive(False)

        self.offline_message = Gtk.Label()
        self.offline_message.set_justify(Gtk.Justification.CENTER)

        self.offline_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.offline_bar.set_center_widget(self.offline_message)
        self.offline_bar.pack_end(self.apply_button, False, False, 5)

    def set_status(self, status, force=False):
        if status == SourceViewStatus.empty:
            self.clear(force)
        elif status == SourceViewStatus.valid:
            self.set_valid(force)
        elif status == SourceViewStatus.invalid:
            self.set_invalid(force)
        elif status == SourceViewStatus.modified:
            self.set_modified(force)

    def set_valid(self, force=False):
        if self.status != SourceViewStatus.valid or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("emblem-ok-symbolic", self.icon_size)
                if self.status == SourceViewStatus.empty:
                    self.pack_end(self.online_bar, False, False, 5)

            if self.mode == "offline":
                self.offline_message.set_text("")
                self.apply_button.set_sensitive(False)

            self.status = SourceViewStatus.valid

    def set_invalid(self, force=False):
        if self.status != SourceViewStatus.invalid or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("action-unavailable-symbolic", self.icon_size)
                if self.status == SourceViewStatus.empty:
                    self.pack_end(self.online_bar, False, False, 5)

            if self.mode == "offline":
                self.offline_message.set_markup("Invalid Entry!")

            self.status = SourceViewStatus.invalid

    def set_modified(self, force=False):
        if self.status != SourceViewStatus.modified or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("dialog-question-symbolic", self.icon_size)
                if self.status == SourceViewStatus.empty:
                    self.pack_end(self.online_bar, False, False, 5)

            if self.mode == "offline":
                self.offline_message.set_markup("<small>Entry has been modified.\nClick on 'Apply' or press 'Ctrl+Enter' to save.</small>")
                self.apply_button.set_sensitive(True)

            self.status = SourceViewStatus.modified

    def clear(self, force=False):
        if self.status != SourceViewStatus.empty or force:
            self.status = SourceViewStatus.empty

            self.form.set_text("")
            self.form.set_sensitive(False)

            if self.mode == "online":
                self.remove(self.online_bar)

            if self.mode == "offline":
                self.offline_message.set_text("")
                self.apply_button.set_sensitive(False)

            self.show_all()

    def update(self, item):
        self.form.set_text(item.bibtex)

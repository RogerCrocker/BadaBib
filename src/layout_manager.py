# layout_manager.py
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

from .config_manager import entrytype_dict
from .config_manager import field_dict
from .config_manager import default_layout_strings
from .config_manager import get_default_entrytype
from .config_manager import set_editor_layout
from .config_manager import get_editor_layout

from .dialogs import WarningDialog

from .editor import Editor


HELP_TEXT = """
Modify or create editor layouts as follows:

- Each line corresponds to one row of the editor.
- Fields are seperated by one or more spaces, rows by one or more line breaks.
- If a row contains only one field, it will span all columns.
- Visual separators between rows can be placed by starting a line with '-'
- Empty lines and lines starting with '#' will be ignored.


For example, the following snippet creates a three column layout with a separator after the first row and a title field spanning all three columns.


ID ENTRYTYPE
---
title
journal volume year
"""


def string_to_layout(string, window):
    layout = []
    unknown = []
    message = ""
    title = "Invalid Layout"

    lines = string.split("\n")
    if len(lines) > 3 * len(field_dict):
        message += "String contains too many lines."
        WarningDialog(message, window, title)
        return []

    for line in lines:
        fields = []
        words = line.split()
        for word in words:
            word = word.strip()
            if word:
                if word[0] == "#":
                    break
                if word[0] == "-":
                    fields.append("separator")
                    break
                if word in field_dict:
                    fields.append(word)
                else:
                    unknown.append(word)
        if fields:
            layout.append(fields)

    if not layout:
        WarningDialog("Empty layout, please add fields.", window, title)
        return []

    if unknown:
        message += "Unknown fields: " + ", ".join(unknown)

    duplicated = []
    all_fields = [field for row in layout for field in row if field != "separator"]
    for field in set(all_fields):
        if all_fields.count(field) > 1:
            duplicated.append(field)

    if duplicated:
        if message:
            message += "\n\n"
        message += "Duplicated fields: " + ", ".join(duplicated)

    if message:
        WarningDialog(message, window, title)
        return []

    return layout


class TopToolbar(Gtk.CenterBox):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.preview_button = Gtk.ToggleButton.new_with_label("Preview")
        self.preview_button.set_margin_start(2)
        self.preview_button.set_margin_top(2)
        self.preview_button.set_margin_bottom(2)

        self.help_button = Gtk.ToggleButton.new_with_label("Help")
        self.help_button.set_margin_start(2)
        self.help_button.set_margin_top(2)
        self.help_button.set_margin_bottom(2)

        start_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        start_box.append(self.preview_button)
        start_box.append(self.help_button)

        self.entrytype_box = Gtk.ComboBoxText()
        self.entrytype_box.set_margin_end(2)
        self.entrytype_box.set_margin_top(2)
        self.entrytype_box.set_margin_bottom(2)
        for label in entrytype_dict.values():
            self.entrytype_box.append_text(label)
        self.entrytype_box.set_active(-1)

        self.set_start_widget(start_box)
        self.set_end_widget(self.entrytype_box)


class BottomToolbar(Gtk.CenterBox):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.default_button = Gtk.Button.new_with_label("Default")
        self.default_button.set_margin_start(2)
        self.default_button.set_margin_top(2)
        self.default_button.set_margin_bottom(2)
        self.default_button.get_style_context().add_class("destructive-action")

        self.reset_button = Gtk.Button.new_with_label("Reset")
        self.reset_button.set_margin_start(2)
        self.reset_button.set_margin_top(2)
        self.reset_button.set_margin_bottom(2)

        start_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        start_box.append(self.default_button)
        start_box.append(self.reset_button)

        self.apply_button = Gtk.Button.new_with_label("Apply")
        self.apply_button.set_margin_end(2)
        self.apply_button.set_margin_top(2)
        self.apply_button.set_margin_bottom(2)
        self.apply_button.get_style_context().add_class("suggested-action")

        self.set_start_widget(start_box)
        self.set_end_widget(self.apply_button)


class ScrolledTextview(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self.textview = Gtk.TextView()
        self.textview.set_hexpand(True)
        self.textview.set_vexpand(True)
        self.textview.set_editable(True)
        self.textview.set_monospace(True)
        self.textview.set_sensitive(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.NONE)

        self.set_child(self.textview)


class SideBar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        field_list = [field for field in field_dict if field not in ["ID", "ENTRYTYPE"]]
        field_list.sort()

        field_string = "ID\nENTRYTYPE\n"
        field_string += "\n".join(field_list)

        fields_header = Gtk.Label()
        fields_header.set_markup("<b>Fields</b>")
        fields_header.set_margin_top(15)
        fields_header.set_margin_bottom(10)

        fields_list = Gtk.Label(label=field_string)
        fields_list.set_selectable(True)

        self.set_margin_bottom(10)
        self.set_margin_start(20)
        self.set_margin_end(30)
        self.set_valign(Gtk.Align.BASELINE)

        self.append(fields_header)
        self.append(fields_list)


class LayoutManagerWindow(Gtk.Window):
    def __init__(self, main_window):
        super().__init__(transient_for=main_window)

        self.main_window = main_window
        self.set_title("Layout Manager")
        self.editor = None
        self.text_buffer = None

        self.assemble()
        self.set_size_request(800, 700)

        # select layout of current entrytype and grab focus
        item = self.main_window.main_widget.get_current_item()
        # if item is not None:
        try:
            idx = list(entrytype_dict.keys()).index(item.entry["ENTRYTYPE"])
        except (AttributeError, ValueError):
            idx = list(entrytype_dict.keys()).index(get_default_entrytype())
        self.entrytype_box.set_active(idx)
        self.textview.grab_focus()

        self.show()

    def assemble(self):
        self.side_bar = SideBar()

        self.top_toolbar = TopToolbar()
        self.preview_button = self.top_toolbar.preview_button
        self.help_button = self.top_toolbar.help_button
        self.entrytype_box = self.top_toolbar.entrytype_box

        self.preview_button.connect("toggled", self.on_preview_toggled)
        self.help_button.connect("toggled", self.on_help_toggled)
        self.entrytype_box.connect("changed", self.on_entrytype_changed)

        self.scrolled_textview = ScrolledTextview()
        self.textview = self.scrolled_textview.textview

        buffer = self.textview.get_buffer()
        buffer.connect("changed", self.text_changed)

        self.bottom_toolbar = BottomToolbar()
        self.default_button = self.bottom_toolbar.default_button
        self.reset_button = self.bottom_toolbar.reset_button
        self.apply_button = self.bottom_toolbar.apply_button

        self.default_button.connect("clicked", self.on_default_clicked)
        self.reset_button.connect("clicked", self.on_reset_clicked)
        self.apply_button.connect("clicked", self.on_apply_clicked)

        self.layout_editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.layout_editor.append(self.top_toolbar)
        self.layout_editor.append(Gtk.Separator())
        self.layout_editor.append(self.scrolled_textview)
        self.layout_editor.append(Gtk.Separator())
        self.layout_editor.append(self.bottom_toolbar)

        background_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        background_box.append(self.side_bar)
        background_box.append(Gtk.Separator())
        background_box.append(self.layout_editor)
        background_box.set_baseline_position(Gtk.BaselinePosition.TOP)

        self.set_child(background_box)

    def get_entrytype(self):
        idx = self.entrytype_box.get_active()
        keys = list(entrytype_dict.keys())
        return keys[idx]

    def get_text(self):
        textbuffer = self.textview.get_buffer()
        start, end = textbuffer.get_bounds()
        return textbuffer.get_text(start, end, True)

    def set_text(self, text):
        textbuffer = self.textview.get_buffer()
        textbuffer.set_text(text)

    def text_changed(self, textview):
        entrytype = self.get_entrytype()
        current_layout = get_editor_layout(entrytype)
        self.apply_button.set_sensitive(current_layout != self.get_text())

    def on_entrytype_changed(self, entrytype_box=None):
        entrytype = self.get_entrytype()
        self.set_text(get_editor_layout(entrytype))
        self.apply_button.set_sensitive(False)

    def activate_preview(self):
        layout_string = self.get_text()
        layout = string_to_layout(layout_string, self)
        if layout:
            self.editor = Editor(layout)
            self.entrytype_box.set_sensitive(False)
            self.bottom_toolbar.hide()
            self.scrolled_textview.hide()
            self.layout_editor.append(self.editor)
            self.help_button.set_sensitive(False)
        else:
            self.preview_button.set_active(False)

    def deactivate_preview(self):
        if self.editor:
            self.layout_editor.remove(self.editor)
            self.editor = None
            self.entrytype_box.set_sensitive(True)
            self.bottom_toolbar.show()
            self.scrolled_textview.show()
            self.help_button.set_sensitive(True)

    def on_preview_toggled(self, button):
        if button.get_active():
            self.activate_preview()
        else:
            self.deactivate_preview()

    def on_help_toggled(self, button):
        if self.text_buffer:
            self.set_text(self.text_buffer)
            self.textview.set_editable(True)
            self.textview.set_wrap_mode(Gtk.WrapMode.NONE)
            self.text_buffer = None
            self.preview_button.set_sensitive(True)
            self.entrytype_box.set_sensitive(True)
            self.bottom_toolbar.show()
        else:
            self.text_buffer = self.get_text()
            self.set_text(HELP_TEXT)
            self.textview.set_editable(False)
            self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
            self.bottom_toolbar.hide()
            self.entrytype_box.set_sensitive(False)
            self.preview_button.set_sensitive(False)

    def on_apply_clicked(self, button):
        layout_string = self.get_text()
        layout = string_to_layout(layout_string, self)
        if layout:
            entrytype = self.get_entrytype()
            set_editor_layout(entrytype, layout_string)
            self.main_window.main_widget.update_editor(entrytype)
            self.apply_button.set_sensitive(False)

    def on_default_clicked(self, button):
        entrytype = self.get_entrytype()
        self.apply_button.set_sensitive(default_layout_strings[entrytype] != get_editor_layout(entrytype))
        self.set_text(default_layout_strings[entrytype])

    def on_reset_clicked(self, button):
        entrytype = self.get_entrytype()
        self.set_text(get_editor_layout(entrytype))
        self.apply_button.set_sensitive(False)

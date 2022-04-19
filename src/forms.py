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
gi.require_version("GtkSource", "5")

from gi.repository import Gtk, Gio, GtkSource

from .config_manager import entrytype_dict
from .config_manager import field_dict
from .config_manager import month_dict
from .config_manager import get_parse_on_fly
from .config_manager import get_highlight_syntax


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


class FormMenu(Gio.Menu):
    def __init__(self, field):
        super().__init__()

        capitalize = Gio.MenuItem()
        capitalize.set_label("Capitalize")
        capitalize.set_action_and_target_value("app.capitalize", None)

        protect = Gio.MenuItem()
        protect.set_label("Protect upper case")
        protect.set_action_and_target_value("app.protect_caps", None)

        unicode = Gio.MenuItem()
        unicode.set_label("Convert to Unicode")
        unicode.set_action_and_target_value("app.to_unicode", None)

        latex = Gio.MenuItem()
        latex.set_label("Convert to LaTeX")
        latex.set_action_and_target_value("app.to_latex", None)

        hyphen = Gio.MenuItem()
        hyphen.set_label("Sanitize ranges")
        hyphen.set_action_and_target_value("app.on_sanitize_range", None)

        key = Gio.MenuItem()
        key.set_label("Generate key")
        key.set_action_and_target_value("app.generate_key", None)

        customize_menu = Gio.Menu()
        customize_menu.append_item(capitalize)
        customize_menu.append_item(protect)
        customize_menu.append_item(unicode)
        customize_menu.append_item(latex)

        customize_section = Gio.Menu()
        customize_section.append_submenu("Customize", customize_menu)

        if field == "pages":
            customize_section.append_item(hyphen)
        if field == "ID":
            customize_section.append_item(key)

        self.prepend_section(None, customize_section)


class MultiLine(GtkSource.View):
    def __init__(self, field, editor=None, entry_style=True):
        super().__init__()
        self.field = field
        self.editor = editor
        self.set_hexpand(True)
        self.set_size_request(200, 100)
        self.set_margin_top(5)
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self.set_editable(True)
        self.set_monospace(True)

        self.set_extra_menu(FormMenu(field))

        self.get_buffer().set_enable_undo(False)

        self.event_controller_focus = Gtk.EventControllerFocus()
        self.add_controller(self.event_controller_focus)

        if entry_style:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(
                b"""
                    text {
                      background-color: alpha(currentColor, .1);
                    }

                    text:disabled {
                      background-color: alpha(currentColor, .05);
                    }

                    textview {
                      border-radius: 6px;
                    }

                    textview:focus-within {
                      outline-color: alpha(@accent_color, .5);
                      outline-width: 2px;
                      outline-offset: -2px;
                      outline-style: solid;
                    }
                """
            )
            self.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def get_text(self):
        textbuffer = self.get_buffer()
        start, end = textbuffer.get_bounds()
        return textbuffer.get_text(start, end, True)

    def set_text(self, text):
        textbuffer = self.get_buffer()
        textbuffer.set_text(text)

    def apply(self, func, n=0):
        window = self.get_root()
        itemlist = window.main_widget.get_current_itemlist()
        bibstrings = itemlist.bibfile.database.strings

        textbuffer = self.get_buffer()
        bounds = textbuffer.get_selection_bounds()
        if not bounds:
            bounds = (textbuffer.get_start_iter(), textbuffer.get_end_iter())
        selection = textbuffer.get_text(bounds[0], bounds[1], True)
        new_selection = func(selection, bibstrings, n)

        if new_selection is not None and new_selection != selection:
            textbuffer.delete(bounds[0], bounds[1])
            textbuffer.insert(bounds[0], new_selection, -1)
            textbuffer.emit("end_user_action")

    def deselect(self):
        buffer = self.get_buffer()
        bounds = buffer.get_bounds()
        buffer.select_range(bounds[0], bounds[0])

    def select(self):
        buffer = self.get_buffer()
        start, end = buffer.get_bounds()
        buffer.select_range(start, end)

    def update(self, item):
        self.editor.set_active(True)
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
        super().__init__()
        self.field = field
        self.editor = editor
        self.set_icon(False)
        self.set_hexpand(True)
        self.set_enable_undo(False)

        self.set_extra_menu(FormMenu(field))

        self.event_controller_focus = Gtk.EventControllerFocus()
        self.add_controller(self.event_controller_focus)

    def apply(self, func, n=0):
        window = self.get_root()
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

        if new_text is not None and new_text != text:
            self.set_text(new_text)
            self.set_position(pos)

    def deselect(self):
        self.select_region(0, 0)

    def select(self):
        self.select_region(0, -1)

    def update(self, item):
        self.update_text(item)
        self.update_icon(item)

    def update_text(self, item):
        self.editor.set_active(True)
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
            if string_status == "defined":
                tooltip = item.pretty_field(self.field)
            else:
                tooltip = "Undefined string"
            self.set_icon(string_status)
            self.set_icon_tooltip_text(pos, tooltip)
        else:
            self.set_icon(False)
            self.set_icon_tooltip_text(pos, None)

    def set_icon(self, string_status):
        if string_status == "defined":
            icon_name = "font-x-generic-symbolic"
        elif string_status == "undefined":
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
        super().__init__(has_entry=True)
        self.field = field
        self.editor = editor
        self.set_hexpand(True)

        self.get_child().set_enable_undo(False)

        self.event_controller_focus = Gtk.EventControllerFocus()
        self.add_controller(self.event_controller_focus)

    def get_text(self):
        return self.get_active_text()

    def set_text(self, text):
        entry = self.get_child()
        entry.set_text(text)

    def deselect(self):
        entry = self.get_child()
        entry.select_region(0, 0)

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
        super().__init__(field, editor)
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
        window = self.get_root()
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
        super().__init__(field, editor)
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
        if item.raw_field(self.field) != self.get_text():
            self.editor.track_changes = False
            self.set_text(item.raw_field(self.field))
            self.editor.track_changes = True

    def clear(self):
        self.set_text("")


class Separator(Gtk.Separator):
    def __init__(self):
        super().__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self.set_margin_top(5)
        self.set_margin_bottom(5)


class SourceView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_vexpand(True)
        self.status = "empty"
        self.form = MultiLine("source", entry_style=False)
        self.form.set_vexpand(True)
        self.form.set_show_line_numbers(True)
        self.buffer = self.form.get_buffer()

        source_view_scrolled = Gtk.ScrolledWindow()
        source_view_scrolled.set_propagate_natural_width(True)
        source_view_scrolled.set_child(self.form)

        self.assemble_offline_bar()
        self.assemble_online_bar()

        self.mode = None
        self.append(source_view_scrolled)
        self.append(Gtk.Separator())
        self.append(self.online_bar)
        self.append(self.offline_bar)

        self.highlight_syntax(get_highlight_syntax())

        if get_parse_on_fly():
            self.set_mode("online")
        else:
            self.set_mode("offline")

    def set_mode(self, mode):
        if mode == "online" and self.mode != "online":
            self.offline_bar.hide()
            self.online_bar.show()
            self.mode = "online"
            self.set_status(self.status, True)

        if mode == "offline" and self.mode != "offline":
            self.online_bar.hide()
            self.offline_bar.show()
            self.mode = "offline"
            self.set_status(self.status, True)

    def assemble_online_bar(self):
        self.status_icon = Gtk.Image()
        self.status_icon.set_icon_size(Gtk.IconSize.LARGE)
        self.online_bar = Gtk.CenterBox()
        self.online_bar.set_center_widget(self.status_icon)
        self.online_bar.set_margin_top(6)
        self.online_bar.set_margin_bottom(6)

    def assemble_offline_bar(self):
        self.apply_button = Gtk.Button.new_with_label("Apply")
        self.apply_button.get_style_context().add_class("suggested-action")
        self.apply_button.set_sensitive(False)
        self.apply_button.set_margin_top(5)
        self.apply_button.set_margin_bottom(5)
        self.apply_button.set_margin_end(5)

        self.offline_message = Gtk.Label()
        self.offline_message.set_justify(Gtk.Justification.CENTER)

        self.offline_bar = Gtk.CenterBox()
        self.offline_bar.set_center_widget(self.offline_message)
        self.offline_bar.set_end_widget(self.apply_button)

    def set_status(self, status, force=False):
        if status == "empty":
            self.clear(force)
        elif status == "valid":
            self.set_valid(force)
        elif status == "invalid":
            self.set_invalid(force)
        elif status == "modified":
            self.set_modified(force)
        else:
            print("Unknown source view status")

    def set_valid(self, force=False):
        if self.status != "valid" or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("emblem-ok-symbolic")
                if self.status == "empty":
                    self.online_bar.show()

            if self.mode == "offline":
                self.offline_message.set_text("")
                self.apply_button.set_sensitive(False)

            self.status = "valid"

    def set_invalid(self, force=False):
        if self.status != "invalid" or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("action-unavailable-symbolic")
                if self.status == "empty":
                    self.online_bar.show()

            if self.mode == "offline":
                self.offline_message.set_markup("Invalid Entry!")

            self.status = "invalid"

    def set_modified(self, force=False):
        if self.status != "modified" or force:
            if self.mode == "online":
                self.status_icon.set_from_icon_name("dialog-question-symbolic")
                if self.status == "empty":
                    self.online_bar.show()

            if self.mode == "offline":
                self.offline_message.set_markup("<small>Entry has been modified.</small>\n<span size='x-small'>Click on 'Apply' or press 'Ctrl+Enter' to apply changes.</span>")
                self.apply_button.set_sensitive(True)

            self.status = "modified"

    def clear(self, force=False):
        if self.status != "empty" or force:
            self.status = "empty"

            self.form.set_text("")
            self.form.set_sensitive(False)

            if self.mode == "online":
                self.online_bar.hide()

            if self.mode == "offline":
                self.offline_message.set_text("")
                self.apply_button.set_sensitive(False)

    def highlight_syntax(self, state):
        if state:
            manager = GtkSource.LanguageManager.get_default()
            language = manager.get_language('bibtex')
            self.buffer.set_language(language)
        else:
            self.buffer.set_language(None)

    def update(self, item):
        self.form.set_text(item.bibtex)
        self.set_status("valid")

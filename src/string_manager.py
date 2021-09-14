# string_manager.py
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

from gi.repository import Gtk, GLib

from bibtexparser.bibdatabase import BibDataString
from bibtexparser.bibdatabase import BibDataStringExpression

from .dialogs import FileChooser
from .dialogs import WarningDialog


expand = BibDataStringExpression.expand_if_expression


class FileList(Gtk.ListBox):
    def __init__(self, filenames, shortnames=None):
        Gtk.ListBox.__init__(self)
        self.set_vexpand(True)
        self.rows = {}
        self.add_rows(filenames, shortnames)

    def add_row(self, filename, shortname=None):
        row = FileRow(filename, shortname)
        self.rows[filename] = row
        self.add(row)
        return row

    def add_rows(self, filenames, shortnames=None):
        if shortnames:
            for filename, shortname in zip(filenames, shortnames):
                self.add_row(filename, shortname)
        else:
            for filename in filenames:
                self.add_row(filename)

    def select_file(self, filename):
        self.select_row(self.rows[filename])


class FileRow(Gtk.ListBoxRow):
    def __init__(self, filename, shortname=None):
        Gtk.ListBoxRow.__init__(self)
        self.filename = filename
        if not shortname:
            shortname = filename
        self.label = Gtk.Label(xalign=0, label=shortname)
        self.label.set_margin_start(5)
        self.add(self.label)


class StringList(Gtk.ListBox):
    def __init__(self, strings, toolbar, search_bar, editable=True):
        Gtk.ListBox.__init__(self)
        self.rows = []
        self.toolbar = toolbar
        self.search_bar = search_bar
        self.search_string = ""
        self.applicable = False
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.set_filter_func(self.filter_by_search)
        self.set_vexpand(True)

        self.add_rows(strings, editable)
        self.set_header_func(self.add_top_space)
        self.set_applicable()

        if editable:
            self.add_new_row_button()

    def set_applicable(self, applicable=None):
        if applicable:
            self.applicable = applicable
        self.toolbar.set_applicable(self.applicable)

    def add_top_space(self, row, before):
        if before:
            row.set_margin_top(0)
        else:
            row.set_margin_top(5)

    def add_row(self, macro, value, editable=True):
        if isinstance(macro, BibDataString):
            macro = macro.name
        row = StringRow(self, macro, value, editable)
        if editable:
            row.delete_button.connect("clicked", self.delete_row, row)
        self.add(row)
        self.rows.append(row)
        return row

    def new_row(self, button):
        button.get_parent().destroy()
        row = StringRow(self, "", "")

        self.add(row)
        self.rows.append(row)
        self.add_new_row_button()
        self.set_applicable(True)

        row.delete_button.connect("clicked", self.delete_row, row)
        row.macro_entry.grab_focus()

        self.show_all()

    def add_rows(self, strings, editable=True):
        for macro, value in strings.items():
            self.add_row(macro, value, editable)

    def delete_row(self, _button, row):
        self.set_applicable(True)
        self.rows.remove(row)
        row.destroy()

    def delete_empty_rows(self):
        empty_rows = [row for row in self.rows if row.is_empty]
        for row in empty_rows:
            self.delete_row(None, row)

    def add_new_row_button(self):
        new_string_row = NewStringRow()
        new_string_row.new_button.connect("clicked", self.new_row)
        self.add(new_string_row)

    def to_dict(self):
        string_dict = {row.macro.lower(): row.value for row in self.rows if row.macro}
        macros = [row.macro for row in self.rows]
        duplicates = [macro for macro in string_dict if macros.count(macro) > 1]
        return string_dict, duplicates

    def filter_by_search(self, row):
        search_string = self.search_bar.search_entry.get_text().lower()
        macro = expand(row.macro)
        value = expand(row.value)
        return search_string in macro.lower() or search_string in value.lower()


class StringRow(Gtk.ListBoxRow):
    def __init__(self, string_list, macro, value, editable=True):
        Gtk.ListBoxRow.__init__(self)
        self.set_can_focus(False)
        self.string_list = string_list
        self.macro = macro
        self.value = value

        self.macro_entry = Gtk.Entry()
        self.macro_entry.set_text(macro)
        self.macro_entry.connect("changed", self.on_macro_changed)
        self.macro_entry.set_margin_start(10)

        self.value_entry = Gtk.Entry()
        self.value_entry.set_text(expand(value))
        self.value_entry.connect("changed", self.on_value_changed)

        if editable:
            self.delete_button = Gtk.Button()
            image = Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
            self.delete_button.add(image)
            self.delete_button.set_relief(Gtk.ReliefStyle.NONE)
            self.delete_button.set_tooltip_text("Delete string")
            self.delete_button.set_margin_end(5)
        else:
            self.macro_entry.set_editable(False)
            self.macro_entry.set_can_focus(False)
            self.value_entry.set_margin_right(10)
            self.value_entry.set_editable(False)
            self.value_entry.set_can_focus(False)

        arrow_image = Gtk.Image()
        arrow_image.set_from_icon_name("media-playlist-consecutive-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        arrow_image.set_margin_start(5)
        arrow_image.set_margin_end(5)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.macro_entry, True, True, 5)
        if editable:
            box.pack_end(self.delete_button, False, False, 0)
        box.pack_end(self.value_entry, True, True, 5)
        box.set_center_widget(arrow_image)

        self.add(box)

    @property
    def is_empty(self):
        if not isinstance(self.value, str):
            return False
        return self.macro.strip() == self.value.strip() == ""

    def on_macro_changed(self, entry):
        self.macro = entry.get_text()
        self.string_list.set_applicable(True)

    def on_value_changed(self, entry):
        self.value = entry.get_text()
        self.string_list.set_applicable(True)


class NewStringRow(Gtk.ListBoxRow):
    def __init__(self):
        Gtk.ListBoxRow.__init__(self)
        self.set_can_focus(False)
        self.macro = ""
        self.value = ""

        image = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)

        self.new_button = Gtk.Button()
        self.new_button.set_relief(Gtk.ReliefStyle.NONE)
        self.new_button.set_tooltip_text("Add new string")
        self.new_button.set_margin_start(15)
        self.new_button.set_margin_end(15)
        self.new_button.add(image)

        self.add(self.new_button)


class StringToolbar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        self.apply_button = Gtk.Button.new_with_label("Apply")
        self.apply_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.apply_button.set_sensitive(False)

        search_image = Gtk.Image.new_from_icon_name("system-search-symbolic", Gtk.IconSize.BUTTON)
        self.search_button = Gtk.Button()
        self.search_button.add(search_image)

        self.pack_start(self.search_button, False, False, 5)
        self.pack_end(self.apply_button, False, False, 5)

    def set_applicable(self, applicable):
        self.apply_button.set_sensitive(applicable)


class ImportToolbar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        add_image = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        self.add_button = Gtk.Button()
        self.add_button.set_relief(Gtk.ReliefStyle.NONE)
        self.add_button.add(add_image)
        self.add_button.set_tooltip_text("Add file")

        del_image = Gtk.Image.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.BUTTON)
        self.del_button = Gtk.Button()
        self.del_button.set_relief(Gtk.ReliefStyle.NONE)
        self.del_button.add(del_image)
        self.del_button.set_tooltip_text("Remove file")

        self.pack_start(self.add_button, False, False, 5)
        self.pack_start(self.del_button, False, False, 5)


class StringManagerWindow(Gtk.Window):
    def __init__(self, main_window):
        Gtk.Window.__init__(self, transient_for=main_window, title="String Manager")
        self.main_window = main_window
        self.store = main_window.main_widget.store
        self.string_lists = {}

        self.paned = Gtk.Paned()
        self.assemble_left_pane()
        self.assemble_right_pane()
        self.add(self.paned)

        self.search_bar.set_search_mode(False)
        self.filelist.select_file(main_window.main_widget.get_current_file().name)
        self.set_size_request(950, 700)
        self.paned.set_position(400)
        self.show_all()

    def assemble_left_pane(self):
        open_files_label = Gtk.Label()
        open_files_label.set_margin_top(10)
        open_files_label.set_margin_bottom(10)
        open_files_label.set_markup("<b>Open Files</b>")

        filenames = self.store.bibfiles.keys()
        shortnames = [bibfile.short_name for bibfile in self.store.bibfiles.values()]

        self.filelist = FileList(filenames, shortnames)
        self.filelist.connect("row-selected", self.on_open_file_selected)
        scrollable_files = Gtk.ScrolledWindow()
        scrollable_files.add(self.filelist)

        import_files_label = Gtk.Label()
        import_files_label.set_margin_top(10)
        import_files_label.set_markup("<b>Imported Files</b>")

        import_hint_label = Gtk.Label()
        import_hint_label.set_margin_bottom(10)
        import_hint_label.set_justify(Gtk.Justification.CENTER)
        import_hint_label.set_markup("<small>Add files here to import their strings.\nImported strings are read-only and available in all open files.</small>")

        self.import_list = FileList(self.store.string_files.keys())
        self.import_list.connect("row-selected", self.on_import_file_selected)
        scrollable_import = Gtk.ScrolledWindow()
        scrollable_import.add(self.import_list)

        self.import_toolbar = ImportToolbar()
        self.import_toolbar.add_button.connect("clicked", self.import_strings)
        self.import_toolbar.del_button.connect("clicked", self.remove_imported_strings)

        left_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_pane.pack_start(open_files_label, False, False, 0)
        left_pane.pack_start(Gtk.Separator(), False, False, 0)
        left_pane.pack_start(scrollable_files, True, True, 0)
        left_pane.pack_start(Gtk.Separator(), False, False, 0)
        left_pane.pack_start(import_files_label, False, False, 0)
        left_pane.pack_start(import_hint_label, False, False, 0)
        left_pane.pack_start(Gtk.Separator(), False, False, 0)
        left_pane.pack_start(scrollable_import, True, True, 0)
        left_pane.pack_start(Gtk.Separator(), False, False, 0)
        left_pane.pack_start(self.import_toolbar, False, False, 5)

        self.paned.add1(left_pane)

    def assemble_right_pane(self):
        self.string_stack = Gtk.Stack()

        search_entry = Gtk.SearchEntry()
        search_entry.connect("search_changed", self.on_search_changed)
        self.search_bar = Gtk.SearchBar()
        self.search_bar.add(search_entry)
        self.search_bar.search_entry = search_entry
        self.search_bar.set_search_mode(True)
        self.search_bar.connect_entry(search_entry)

        self.string_toolbar = StringToolbar()
        self.string_toolbar.apply_button.connect("clicked", self.update_local_strings)
        self.string_toolbar.search_button.connect("clicked", self.search_string_list)

        right_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_pane.pack_start(self.string_stack, True, True, 0)
        right_pane.pack_start(self.search_bar, False, False, 0)
        right_pane.pack_start(Gtk.Separator(), False, False, 0)
        right_pane.pack_start(self.string_toolbar, False, False, 5)

        self.paned.add2(right_pane)

    def on_search_changed(self, search_entry):
        row = self.filelist.get_selected_row()
        if not row:
            row = self.import_list.get_selected_row()

        if row:
            string_list = self.string_lists[row.filename]
            string_list.invalidate_filter()

    def search_string_list(self, _button=None):
        self.search_bar.set_search_mode(not self.search_bar.get_search_mode())

    def on_open_file_selected(self, filelist, row):
        if row:
            filename = row.filename
            self.show_local_string_list(filename)
            self.import_list.unselect_all()
            self.show_all()

    def on_import_file_selected(self, filelist, row):
        if row:
            filename = row.filename
            self.show_global_string_list(filename)
            self.filelist.unselect_all()
            self.show_all()

    def show_local_string_list(self, filename):
        if filename not in self.string_lists:
            self.add_local_string_list(filename)
        self.string_lists[filename].set_applicable()
        self.string_lists[filename].invalidate_filter()
        self.string_stack.set_visible_child_name(filename)

    def show_global_string_list(self, filename):
        if filename not in self.string_lists:
            self.add_global_string_list(filename)
        self.string_lists[filename].set_applicable()
        self.string_lists[filename].invalidate_filter()
        self.string_stack.set_visible_child_name(filename)

    def add_local_string_list(self, filename):
        strings = self.store.bibfiles[filename].local_strings
        string_list = StringList(strings, self.string_toolbar, self.search_bar)
        string_list_scrolled = Gtk.ScrolledWindow()
        string_list_scrolled.add(string_list)
        self.string_lists[filename] = string_list
        self.string_stack.add_named(string_list_scrolled, filename)
        string_list_scrolled.show_all()

        return string_list

    def add_global_string_list(self, filename):
        strings = self.store.string_files[filename]
        string_list = StringList(strings, self.string_toolbar, self.search_bar, False)
        string_list_scrolled = Gtk.ScrolledWindow()
        string_list_scrolled.add(string_list)
        self.string_lists[filename] = string_list
        self.string_stack.add_named(string_list_scrolled, filename)
        string_list_scrolled.show_all()

    def update_local_strings(self, _button):
        filename = self.filelist.get_selected_row().filename
        file = self.store.bibfiles[filename]

        self.string_toolbar.apply_button.set_sensitive(False)
        file.itemlist.set_unsaved(True)
        string_list = self.string_lists[filename]
        string_list.delete_empty_rows()
        string_dict, duplicates = string_list.to_dict()
        if duplicates:
            message = "The following strings are defined multiple times:\n\n"
            for macro in duplicates:
                message += "- " + macro + "\n"
            message += "\nHaving duplicate strings is feasible, but ususally not intended."
            WarningDialog(message, window=self)
        self.store.update_file_strings(filename, string_dict)
        GLib.idle_add(self.refresh_display, file)

    def refresh_display(self, file):
        file.itemlist.refresh()
        file.itemlist.reselect_current_row()

    def import_strings(self, _button):
        dialog = FileChooser()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()

            if filename in self.store.bibfiles or filename in self.store.string_files:
                message = "File '" + filename + "' is already open."
                WarningDialog(message, window=self)
                return

            success = self.main_window.store.import_strings(filename)
            if success:
                if len(self.store.string_files[filename]) == 0:
                    self.store.string_files.pop(filename)
                    message = "File '" + filename + "' does not contain strings."
                    WarningDialog(message, window=self)
                    return

                row = self.import_list.add_row(filename)
                self.import_list.select_row(row)
                for file in self.store.bibfiles.values():
                    GLib.idle_add(self.refresh_display, file)
            else:
                message = "Cannot read file '" + filename + "'\n"
                WarningDialog(message, window=self)

        dialog.destroy()

    def remove_imported_strings(self, _button):
        row = self.import_list.get_selected_row()
        if row:
            index = row.get_index()

            # remove global strings and update files
            self.store.string_files.pop(row.filename)
            self.store.update_global_strings()
            self.string_lists.pop(row.filename)
            self.import_list.remove(row)

            # remove string list
            stack_page = self.string_stack.get_child_by_name(row.filename)
            self.string_stack.remove(stack_page)

            # select next imported file...
            for file in self.store.bibfiles.values():
                GLib.idle_add(self.refresh_display, file)

            new_row = self.import_list.get_row_at_index(index)
            if new_row:
                self.import_list.select_row(new_row)
                return

            new_row = self.import_list.get_row_at_index(index - 1)
            if new_row:
                self.import_list.select_row(new_row)
                return

            # ...or first open file
            new_row = self.filelist.get_row_at_index(0)
            self.filelist.select_row(new_row)

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


from gi.repository import Gtk, GLib

from bibtexparser.bibdatabase import BibDataString
from bibtexparser.bibdatabase import BibDataStringExpression

from .dialogs import FileChooser
from .dialogs import WarningDialog


expand = BibDataStringExpression.expand_if_expression


class FileList(Gtk.ListBox):
    def __init__(self, filenames, shortnames=None):
        super().__init__()
        self.set_vexpand(True)
        self.rows = {}
        self.add_rows(filenames, shortnames)

    def add_row(self, filename, shortname=None):
        row = FileRow(filename, shortname)
        self.rows[filename] = row
        self.append(row)
        return row

    def remove_row(self, row):
        self.rows.pop(row.filename)
        self.remove(row)

    def add_rows(self, filenames, shortnames=None):
        if shortnames:
            for filename, shortname in zip(filenames, shortnames):
                self.add_row(filename, shortname)
        else:
            for filename in filenames:
                self.add_row(filename)

    def add_loading_rows(self, N):
        for n in range(N):
            self.add_row(str(n), "Loading...")

    def remove_loading_rows(self):
        loading_rows = [row for row in self.rows.values() if row.shortname == "Loading..."]
        for row in loading_rows:
            self.remove_row(row)

    def select_file(self, filename):
        self.select_row(self.rows[filename])


class FileRow(Gtk.ListBoxRow):
    def __init__(self, filename, shortname=None):
        super().__init__()
        self.filename = filename
        if shortname is None:
            self.shortname = filename
        else:
            self.shortname = shortname

        self.label = Gtk.Label(xalign=0, label=self.shortname)
        self.label.set_margin_start(5)
        self.set_child(self.label)


class StringList(Gtk.ListBox):
    def __init__(self, strings, toolbar, search_bar, editable=True):
        super().__init__()
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

    @staticmethod
    def add_top_space(row, before):
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
        self.append(row)
        self.rows.append(row)
        return row

    def new_row(self, button):
        self.delete_row(None, button.get_parent())
        row = StringRow(self, "", "")

        self.append(row)
        self.rows.append(row)
        self.add_new_row_button()
        self.set_applicable(True)

        row.delete_button.connect("clicked", self.delete_row, row)
        row.macro_entry.grab_focus()

    def add_rows(self, strings, editable=True):
        for macro, value in strings.items():
            self.add_row(macro, value, editable)

    def delete_row(self, _button, row):
        self.set_applicable(True)
        if row in self.rows:
            self.rows.remove(row)
        self.remove(row)

    def delete_empty_rows(self):
        empty_rows = [row for row in self.rows if row.is_empty]
        for row in empty_rows:
            self.delete_row(None, row)

    def add_new_row_button(self):
        new_string_row = NewStringRow()
        new_string_row.new_button.connect("clicked", self.new_row)
        self.append(new_string_row)

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
        super().__init__()
        self.set_can_focus(True)
        self.string_list = string_list
        self.macro = macro
        self.value = value

        self.macro_entry = Gtk.Entry()
        self.macro_entry.set_text(macro)
        self.macro_entry.connect("changed", self.on_macro_changed)
        self.macro_entry.set_margin_start(10)
        self.macro_entry.set_hexpand(True)

        self.value_entry = Gtk.Entry()
        self.value_entry.set_text(expand(value))
        self.value_entry.connect("changed", self.on_value_changed)
        self.value_entry.set_hexpand(True)

        if editable:
            self.delete_button = Gtk.Button.new_from_icon_name("edit-delete-symbolic")
            self.delete_button.set_has_frame(False)
            self.delete_button.set_tooltip_text("Delete string")
            self.delete_button.set_margin_end(5)
        else:
            self.macro_entry.set_editable(False)
            self.macro_entry.set_can_focus(False)
            self.value_entry.set_margin_end(10)
            self.value_entry.set_editable(False)
            self.value_entry.set_can_focus(False)

        arrow_image = Gtk.Image.new_from_icon_name("media-playlist-consecutive-symbolic")
        arrow_image.set_margin_start(10)
        arrow_image.set_margin_end(10)

        value_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        value_box.set_hexpand(True)
        value_box.append(self.value_entry)
        if editable:
            value_box.append(self.delete_button)

        center_box = Gtk.CenterBox(orientation=Gtk.Orientation.HORIZONTAL)
        center_box.set_start_widget(self.macro_entry)
        center_box.set_center_widget(arrow_image)
        center_box.set_end_widget(value_box)

        self.set_child(center_box)

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
        super().__init__()
        self.set_can_focus(False)
        self.macro = ""
        self.value = ""

        self.new_button = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.new_button.set_has_frame(False)
        self.new_button.set_tooltip_text("Add new string")
        self.new_button.set_margin_start(15)
        self.new_button.set_margin_end(15)

        self.set_child(self.new_button)


class StringToolbar(Gtk.CenterBox):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.apply_button = Gtk.Button.new_with_label("Apply")
        self.apply_button.get_style_context().add_class("suggested-action")
        self.apply_button.set_sensitive(False)
        self.apply_button.set_margin_end(2)
        self.apply_button.set_margin_top(2)
        self.apply_button.set_margin_bottom(2)

        self.search_button = Gtk.Button.new_from_icon_name("system-search-symbolic")
        self.search_button.set_margin_start(2)
        self.search_button.set_margin_top(2)
        self.search_button.set_margin_bottom(2)

        self.set_start_widget(self.search_button)
        self.set_end_widget(self.apply_button)

    def set_applicable(self, applicable):
        self.apply_button.set_sensitive(applicable)


class ImportToolbar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.add_button = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.add_button.set_has_frame(False)
        self.add_button.set_tooltip_text("Add file")
        self.add_button.set_margin_start(2)
        self.add_button.set_margin_top(2)
        self.add_button.set_margin_bottom(2)

        self.del_button = Gtk.Button.new_from_icon_name("list-remove-symbolic")
        self.del_button.set_has_frame(False)
        self.del_button.set_tooltip_text("Remove file")
        self.del_button.set_margin_top(2)
        self.del_button.set_margin_bottom(2)

        self.append(self.add_button)
        self.append(self.del_button)


class StringManagerWindow(Gtk.Window):
    def __init__(self, main_window):
        super().__init__(transient_for=main_window, title="String Manager")
        self.main_window = main_window
        self.store = main_window.main_widget.store
        self.string_lists = {}

        self.paned = Gtk.Paned()
        self.assemble_left_pane()
        self.assemble_right_pane()
        self.set_child(self.paned)

        self.search_bar.set_search_mode(False)
        self.filelist.select_file(main_window.main_widget.get_current_itemlist().bibfile.name)
        self.set_size_request(950, 700)
        self.paned.set_position(400)

        self.show()

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
        scrollable_files.set_child(self.filelist)

        import_files_label = Gtk.Label()
        import_files_label.set_margin_top(10)
        import_files_label.set_markup("<b>Imported Files</b>")

        import_hint_label = Gtk.Label()
        import_hint_label.set_margin_bottom(10)
        import_hint_label.set_justify(Gtk.Justification.CENTER)
        import_hint_label.set_markup("<small>Add files with string definitions here.\nImported strings are read-only and available in all open files.</small>")

        self.import_list = FileList(self.store.string_files.keys())
        self.import_list.connect("row-selected", self.on_import_file_selected)
        scrollable_import = Gtk.ScrolledWindow()
        scrollable_import.set_child(self.import_list)

        self.import_toolbar = ImportToolbar()
        self.import_toolbar.add_button.connect("clicked", self.import_strings)
        self.import_toolbar.del_button.connect("clicked", self.remove_imported_strings)

        left_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_pane.append(open_files_label)
        left_pane.append(Gtk.Separator())
        left_pane.append(scrollable_files)
        left_pane.append(Gtk.Separator())
        left_pane.append(import_files_label)
        left_pane.append(import_hint_label)
        left_pane.append(Gtk.Separator())
        left_pane.append(scrollable_import)
        left_pane.append(Gtk.Separator())
        left_pane.append(self.import_toolbar)

        self.paned.set_start_child(left_pane)

    def assemble_right_pane(self):
        self.string_stack = Gtk.Stack()

        search_entry = Gtk.SearchEntry()
        search_entry.connect("search_changed", self.on_search_changed)
        self.search_bar = Gtk.SearchBar()
        self.search_bar.set_child(search_entry)
        self.search_bar.search_entry = search_entry
        self.search_bar.set_search_mode(True)
        self.search_bar.connect_entry(search_entry)

        self.string_toolbar = StringToolbar()
        self.string_toolbar.apply_button.connect("clicked", self.update_local_strings)
        self.string_toolbar.search_button.connect("clicked", self.search_string_list)

        right_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_pane.append(self.string_stack)
        right_pane.append(self.search_bar)
        right_pane.append(Gtk.Separator())
        right_pane.append(self.string_toolbar)

        self.paned.set_end_child(right_pane)

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

    def on_import_file_selected(self, filelist, row):
        if row:
            filename = row.filename
            self.show_global_string_list(filename)
            self.filelist.unselect_all()

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
        string_list_scrolled.set_child(string_list)
        self.string_lists[filename] = string_list
        self.string_stack.add_named(string_list_scrolled, filename)

        return string_list

    def add_global_string_list(self, filename):
        strings = self.store.string_files[filename]
        string_list = StringList(strings, self.string_toolbar, self.search_bar, False)
        string_list_scrolled = Gtk.ScrolledWindow()
        string_list_scrolled.set_child(string_list)
        self.string_lists[filename] = string_list
        self.string_stack.add_named(string_list_scrolled, filename)

    def update_local_strings(self, _button):
        filename = self.filelist.get_selected_row().filename
        file = self.store.bibfiles[filename]

        self.string_toolbar.apply_button.set_sensitive(False)
        file.itemlist.set_unsaved(True)
        string_list = self.string_lists[filename]
        string_list.delete_empty_rows()
        string_dict, duplicates = string_list.to_dict()
        if duplicates:
            message = (
                "The following strings are defined multiple times:"
                + "\n\n"
                + "\n".join(duplicates)
                + "\n\n"
                + "Having duplicate strings is feasible, but ususally not intended."
            )
            WarningDialog(message, window=self)
        self.store.update_file_strings(filename, string_dict)
        GLib.idle_add(self.refresh_display, file)

    @staticmethod
    def refresh_display(file):
        file.itemlist.refresh()

    def import_strings(self, _button):
        dialog = FileChooser(self)
        dialog.connect("response", self.on_import_response)
        dialog.show()

    def on_import_response(self, dialog, response):
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            files = dialog.get_files()
            self.import_list.add_loading_rows(len(files))
            GLib.idle_add(self.import_strings_thread, [file.get_path() for file in files])

    def import_strings_thread(self, filenames):
        # read databases
        statuses = [self.main_window.store.import_strings(filename) for filename in filenames]

        # remove loading rows
        self.import_list.remove_loading_rows()

        # add file rows
        first = True
        messages = []
        for filename, status in zip(filenames,  statuses):

            # file does not exist or cannot be read
            if status in ("file_error", "parse_error"):
                messages.append(f"Cannot read file '{filename}'.")

            # file is empty
            elif status == "empty":
                messages.append(f"File '{filename}' does not contain string definitions.")

            elif status == "success":
                if filename in [row.filename for row in self.import_list]:
                    row = self.import_list.rows[filename]
                else:
                    row = self.import_list.add_row(filename)
                if first:
                    self.import_list.select_row(row)
                    first = False

        # show warining, if any
        if messages:
            WarningDialog(messages, window=self)

        # refresh display
        for file in self.store.bibfiles.values():
            GLib.idle_add(self.refresh_display, file)

    def remove_imported_strings(self, _button):
        row = self.import_list.get_selected_row()
        if row:
            index = row.get_index()

            # remove global strings and update files
            self.store.string_files.pop(row.filename)
            self.store.update_global_strings()
            self.string_lists.pop(row.filename)
            self.import_list.remove_row(row)

            # remove string list
            stack_page = self.string_stack.get_child_by_name(row.filename)
            self.string_stack.remove(stack_page)

            # refresh display
            for file in self.store.bibfiles.values():
                GLib.idle_add(self.refresh_display, file)

            # select next file in list...
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

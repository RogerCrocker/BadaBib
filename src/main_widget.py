# main_widget.py
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


from gi.repository import Gtk, Gdk, GLib, Gio

from time import sleep

from .config_manager import add_to_recent
from .config_manager import remove_from_recent
from .config_manager import get_editor_layout
from .config_manager import get_parse_on_fly
from .config_manager import get_default_entrytype

from .layout_manager import string_to_layout

from .bibitem import entries_equal

from .forms import SourceView

from .change import Change

from .editor import Editor

from .watcher import Watcher

from .itemlist import Itemlist
from .itemlist import ItemlistNotebook
from .itemlist import ItemlistToolbar

from .menus import FilterPopover
from .menus import SortPopover

from .dialogs import SaveChangesDialog
from .dialogs import SaveDialog
from .dialogs import ConfirmSaveDialog


DEFAULT_EDITOR = get_default_entrytype()


class MainWidget(Gtk.Paned):
    def __init__(self, store):
        super().__init__()

        self.store = store
        self.editors = {}
        self.watchers = {}
        self.copy_paste_buffer = None

        self.assemble_left_pane()
        self.assemble_right_pane()

        self.add_editor(DEFAULT_EDITOR)
        self.outer_stack.set_visible_child_name("editor")

    def assemble_left_pane(self):
        # notebook to hold itemlists and toolbar
        self.notebook = ItemlistNotebook()
        self.notebook.connect("switch_page", self.on_switch_page)
        self.notebook.connect("page_removed", self.on_page_removed)

        # Toolbar
        self.toolbar = ItemlistToolbar()
        self.toolbar.new_button.connect("clicked", self.add_items)
        self.toolbar.delete_button.connect("clicked", self.delete_selected_items)
        self.toolbar.sort_button.connect("clicked", self.sort_itemlist)
        self.toolbar.filter_button.connect("clicked", self.filter_itemlist)
        self.toolbar.goto_button.connect("clicked", self.focus_on_current_item)
        self.toolbar.search_button.connect("clicked", self.search_itemlist)

        # box notebook and toolbar
        self.left_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_pane.append(self.notebook)
        self.left_pane.append(self.toolbar)

        self.set_start_child(self.left_pane)

    def assemble_right_pane(self):
        # editors
        self.editor_stack = Gtk.Stack()
        editor_stack_scrolled = Gtk.ScrolledWindow()
        editor_stack_scrolled.set_child(self.editor_stack)

        # source view
        self.source_view = SourceView()
        self.source_view.buffer.connect("end_user_action", self.on_source_view_modified)
        self.source_view.apply_button.connect("clicked", self.update_bibtex)

        # stack of editors and source view
        self.outer_stack = Gtk.Stack()
        self.outer_stack.add_titled(editor_stack_scrolled, "editor", "Editor")
        self.outer_stack.add_titled(self.source_view, "source", "BibTeX")

        # switcher
        outer_stack_switcher = Gtk.StackSwitcher()
        outer_stack_switcher.set_margin_top(5)
        outer_stack_switcher.set_stack(self.outer_stack)
        switcher_box = Gtk.CenterBox()
        switcher_box.set_center_widget(outer_stack_switcher)

        # editors
        right_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_pane.prepend(switcher_box)
        right_pane.append(self.outer_stack)

        self.set_end_child(right_pane)

    # Editor

    def show_editor(self, entrytype):
        editor = self.get_editor(entrytype)
        self.editor_stack.set_visible_child_name(entrytype)
        return editor

    def add_editor(self, entrytype):
        layout_string = get_editor_layout(entrytype)
        layout = string_to_layout(layout_string, self.get_root())
        editor = Editor(layout, entrytype)
        self.editor_stack.add_named(editor, entrytype)
        self.editors[entrytype] = editor
        return editor

    def update_editor(self, entrytype):
        if entrytype in self.editors:
            editor = self.editors.pop(entrytype)
            self.editor_stack.remove(editor)

        item = self.get_current_item()
        if item:
            item.bibfile.itemlist.unselect_row(item.row)
            item.bibfile.itemlist.select_row(item.row)
        else:
            self.show_editor(DEFAULT_EDITOR)

    def get_editor(self, entrytype):
        if entrytype not in self.editors:
            editor = self.add_editor(entrytype)
        else:
            editor = self.editors[entrytype]
        return editor

    def get_current_editor(self):
        return self.editor_stack.get_visible_child()

    # Itemlist

    def add_itemlist(self, bibfile, state=None, change_buffer=None):
        itemlist = Itemlist(bibfile, state, change_buffer)
        itemlist.connect("selected-rows-changed", self.on_selected_rows_changed)
        itemlist.event_controller.connect("key-pressed", self.on_itemlist_key_pressed)
        itemlist.drop_target.connect("drop", self.on_drop)

        bibfile.itemlist = itemlist
        return itemlist

    def get_current_itemlist(self):
        page_num = self.notebook.get_current_page()
        return self.notebook.get_nth_page(page_num).itemlist

    def sort_itemlist(self, button):
        itemlist = self.get_current_itemlist()
        if itemlist:
            SortPopover(button, itemlist)

    def filter_itemlist(self, button):
        itemlist = self.get_current_itemlist()
        if itemlist:
            FilterPopover(button, itemlist)

    def search_itemlist(self, _button=None):
        itemlist = self.get_current_itemlist()
        if itemlist:
            searchbar = itemlist.page.searchbar
            searchbar.set_search_mode(not searchbar.get_search_mode())

    def on_itemlist_key_pressed(self, _event_controller_key, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Delete:
            self.delete_selected_items()
        if keyval == Gdk.KEY_Return:
            self.focus_on_current_item()

    def on_drop(self, _drop_target, file, _x, _y):
        self.open_files(file.get_path())

    # Item

    def get_selected_items(self, itemlist=None):
        if itemlist is None:
            itemlist = self.get_current_itemlist()
        if itemlist:
            return itemlist.get_selected_items()
        return []

    def get_current_item(self, itemlist=None):
        items = self.get_selected_items(itemlist)
        if len(items) != 1:
            return None
        return items[0]

    def add_items(self, _button=None, entries=None):
        itemlist = self.get_current_itemlist()
        if not entries:
            entries = [None]

        if itemlist:
            items = [itemlist.bibfile.append_item(entry) for entry in entries]
            itemlist.add_rows(items)
            change = Change.Show(items)
            itemlist.change_buffer.push_change(change)

    def delete_items(self, items):
        itemlist = self.get_current_itemlist()
        if itemlist and items:
            change = Change.Hide(items)
            itemlist.change_buffer.push_change(change)

    def delete_selected_items(self, _button=None):
        items = self.get_selected_items()
        self.delete_items(items)

    def focus_on_current_item(self, _button=None):
        itemlist = self.get_current_itemlist()
        if itemlist:
            itemlist.focus_on_selected_items()

    def on_selected_rows_changed(self, itemlist):
        itemlist.focus_idx = 0
        # work around listbox scrolling horizontally on row changes
        itemlist.get_parent().get_parent().get_hadjustment().set_value(0)
        item = self.get_current_item(itemlist)
        if item and item.bibfile:
            entrytype = item.entry["ENTRYTYPE"]
            self.show_editor(entrytype).show_item(item)
            self.source_view.set_status("valid")
            self.source_view.form.set_sensitive(True)
            self.source_view.form.set_text(item.bibtex)
        else:
            self.get_current_editor().clear()
            self.source_view.clear()

    def generate_key(self):
        item = self.get_current_item()
        new_key = item.bibfile.generate_key_for_item(item)
        if new_key != item.entry["ID"]:
            editor = self.get_current_editor()
            form = editor.forms["ID"]
            old_key = item.entry["ID"]
            change = Change.Edit(item, form, old_key, new_key)
            item.bibfile.itemlist.change_buffer.push_change(change)

    # Notebook

    def on_tab_closed(self, header=None, action=None, data=None):
        if header is None:
            page_num = self.notebook.get_current_page()
            page = self.notebook.get_nth_page(page_num)
        else:
            page = header.get_parent().page
            # work around notebook selecting the closed page bug
            if self.notebook.previous_page is not None:
                self.notebook.set_current_page(self.notebook.previous_page)

        if page.itemlist:
            self.close_files(page.itemlist.bibfile)
        else:
            self.notebook.remove_page(page.number)

    def on_page_removed(self, notebook, page, page_num):
        if notebook.get_n_pages() == 0:
            self.new_file()
        self.notebook.update_pagenumbers(notebook, page, page_num)

    def on_switch_page(self, notebook, page, page_num):
        if page.itemlist is None:
            self.source_view.set_status("empty", True)
            self.get_current_editor().clear()
            return None
        itemlist = page.itemlist
        itemlist.grab_focus()

        # work around notebook switching to page when closing it
        if notebook.current_page is not None:
            notebook.previous_page = notebook.current_page
        notebook.current_page = itemlist.page.number

        rows = itemlist.get_selected_rows()
        if rows:
            # work around ListBox not selecting multiple rows on page switch
            GLib.idle_add(itemlist.reselect_rows, rows)
            GLib.idle_add(itemlist.focus_on_selected_items, 0)
        else:
            self.source_view.set_status("empty", True)
            self.get_current_editor().clear()

    # Source view

    def on_source_view_modified(self, _buffer):
        if get_parse_on_fly():
            self.update_bibtex()
        else:
            self.source_view.set_status("modified")

    def update_bibtex(self, _button=None):
        bibtex = self.source_view.form.get_text()
        if bibtex:
            item = self.get_current_item()
            new_entry = item.bibfile.parse_entry(bibtex)
            old_entry = item.entry
            if new_entry:
                self.source_view.set_status("valid")
                if not entries_equal(old_entry, new_entry):
                    change = Change.Replace(item, old_entry, new_entry)
                    item.bibfile.itemlist.change_buffer.push_change(change)
            else:
                self.source_view.set_status("invalid")

    # File watcher

    def add_watcher(self, filename):
        sleep(0.1)  # give file time to settle
        self.watchers[filename] = Watcher(self, filename)

    def remove_watcher(self, filename):
        if filename in self.watchers:
            watcher = self.watchers.pop(filename)
            watcher.monitor.cancel()

    # File

    def new_file(self):
        bibfile = self.store.new_file()
        itemlist = self.add_itemlist(bibfile)
        page = self.notebook.add_itemlist_page(bibfile.name)
        page.header.close_button.connect("clicked", self.on_tab_closed)
        page.add_itemlist(itemlist)

        self.notebook.set_current_page(itemlist.page.number)

    def open_files(self, names, states=None, page_nums=None, open_tab=None):
        if not isinstance(names, list):
            names = [names]

        if states is None:
            states = len(names) * [None]
        elif not isinstance(states, list):
            states = [states]

        if page_nums is None:
            page_nums = len(names) * [None]
        elif not isinstance(page_nums, list):
            page_nums = [page_nums]

        if open_tab is None:
            open_tab = names[0]

        empty_file = self.notebook.contains_empty_new_file()

        for name, state, page_num in zip(names, states, page_nums):
            page = self.open_file(name, state, page_num)
            if name == open_tab:
                self.notebook.set_current_page(page.number)

        if empty_file:
            self.close_files(empty_file, force=True)

    def open_file(self, name, state=None, page_num=None):
        # add loading page to notebook
        page = self.notebook.add_itemlist_page(name, page_num)
        page.header.close_button.connect("clicked", self.on_tab_closed)

        def parse_file(task, _obj, _data, _cancellable):
            status = self.store.add_file(name)
            task.return_value(status)

        def on_file_parsed(_obj, task):
            success, status = task.propagate_value()
            if not success:
                status = ["error"]

            if "error" in status:
                page.show_error_screen(status)
                remove_from_recent(name)
                self.get_root().update_recent_file_menu()
            elif "file_open" in status:
                self.notebook.remove_page(page.number)
            else:
                bibfile = self.store.bibfiles[name]
                itemlist = self.add_itemlist(bibfile, state)
                page.add_itemlist(itemlist)
                GLib.idle_add(self.add_watcher, name)
                if "empty" in status:
                    page.empty_bar.reveal()

        # open file in thread
        task = Gio.Task.new(None, None, on_file_parsed)
        task.run_in_thread(parse_file)

        return page

    def reload_file(self, bibfile):
        name = bibfile.name
        state = bibfile.itemlist.state_to_string()
        page_num = bibfile.itemlist.page.number

        self.close_files(bibfile, force=True)
        self.open_files(name, state, page_num, name)

    def declare_file_created(self, name):
        self.store.bibfiles[name].created = True
        self.store.bibfiles[name].set_unsaved(True)
        self.watchers.pop(name)

    def close_files(self, bibfiles, force=False, close_app=False):
        # make sure 'bibfiles' is a list
        if not isinstance(bibfiles, list):
            bibfiles = [bibfiles]
        self.close_files_dialog(None, Gtk.ResponseType.CLOSE, bibfiles, 0, force, close_app)

    def handle_close_response(self, dialog, response, bibfiles, n, force, close_app):
        if dialog:
            dialog.destroy()
        if response == Gtk.ResponseType.CANCEL:
            return True
        if response == Gtk.ResponseType.OK:
            self.save_and_close(bibfiles, n-1, force, close_app)
            return True
        return False

    def close_files_dialog(self, dialog, response, bibfiles, n, force, close_app):
        handled = self.handle_close_response(dialog, response, bibfiles, n, force, close_app)
        if handled:
            return None

        bibfile = bibfiles[n]
        if bibfile.unsaved and not force:
            self.notebook.set_current_page(bibfile.itemlist.page.number)
            dialog = SaveChangesDialog(self.get_root(), bibfile.name)
            if n < len(bibfiles) - 1:
                dialog.connect("response", self.close_files_dialog, bibfiles, n+1, force, close_app)
            else:
                dialog.connect("response", self.close_files_finalize, bibfiles, n+1, force, close_app)
            dialog.show()
        else:
            if n < len(bibfiles) - 1:
                self.close_files_dialog(None, Gtk.ResponseType.CLOSE, bibfiles, n+1, force, close_app)
            else:
                self.close_files_finalize(None, Gtk.ResponseType.CLOSE, bibfiles, n+1, force, close_app)
        return None

    def close_files_finalize(self, dialog, response, bibfiles, n, force, close_app):
        handled = self.handle_close_response(dialog, response, bibfiles, n, force, close_app)
        if handled:
            return None

        if close_app:
            self.get_root().session_manager.save()

        for bibfile in bibfiles:
            if not bibfile.created and not close_app:
                add_to_recent(bibfile)
                self.get_root().update_recent_file_menu()

            self.remove_watcher(bibfile.name)
            self.notebook.remove_page(bibfile.itemlist.page.number)
            self.store.remove_file(bibfile.name)

        if close_app:
            self.get_root().destroy()

    def save_file(self, bibfile=None, close_data=None):
        if bibfile is None:
            itemlist = self.get_current_itemlist()
            if itemlist:
                bibfile = itemlist.bibfile
            else:
                return None

        if bibfile.unsaved:
            if bibfile.created:
                self.save_file_as(close_data=close_data)
            else:
                self.save_file_as(bibfile, bibfile.name, close_data)
        return None

    def save_all_files(self):
        for bibfile in self.store.bibfiles.values():
            self.save_file(bibfile)

    def save_and_close(self, bibfiles, n, force, close_app):
        close_data = (bibfiles, n, force, close_app)
        self.save_file(bibfiles[n], close_data)

    def save_file_as(self, bibfile=None, new_name=None, close_data=None):
        if bibfile is None:
            itemlist = self.get_current_itemlist()
            if itemlist:
                bibfile = itemlist.bibfile
            else:
                return None
        self.confirm_save_dialog(bibfile, new_name, close_data)
        return None

    def confirm_save_dialog(self, bibfile, new_name, close_data):
        has_empty_keys = bibfile.has_empty_keys()
        duplicate_keys = bibfile.get_duplicate_keys()
        if has_empty_keys or duplicate_keys:
            dialog = ConfirmSaveDialog(self.get_root(), bibfile.name, has_empty_keys, duplicate_keys)
            dialog.connect("response", self.save_file_dialog, bibfile, new_name, close_data)
            dialog.show()
        else:
            self.save_file_dialog(None, Gtk.ResponseType.YES, bibfile, new_name, close_data)

    def save_file_dialog(self, dialog, response, bibfile, new_name, close_data):
        if dialog:
            dialog.destroy()

        if response != Gtk.ResponseType.YES:
            return None

        if not new_name:
            dialog = SaveDialog(self.get_root(), bibfile.base_name)
            dialog.connect("response", self.save_file_as_finalize, bibfile, new_name, close_data)
            dialog.show()
        else:
            self.save_file_as_finalize(None, None, bibfile, new_name, close_data)

    def save_file_as_finalize(self, dialog, response, bibfile, new_name, close_data):
        if dialog:
            dialog.destroy()
            if response == Gtk.ResponseType.ACCEPT:
                new_name = dialog.get_file().get_path()
                new_name = new_name.strip()
                if new_name[-4:] != ".bib":
                    new_name = new_name + ".bib"
            else:
                return None

        if new_name != bibfile.name:
            if new_name in self.store.bibfiles:
                self.close_files(self.store.bibfiles[new_name], force=True)

            if not bibfile.created:
                add_to_recent(bibfile)
                self.get_root().update_recent_file_menu()

            self.remove_watcher(bibfile.name)
            self.store.rename_file(bibfile.name, new_name)

        self.remove_watcher(bibfile.name)
        errors = self.store.save_file(new_name)

        if "save" in errors:
            bibfile.created = True
            bibfile.set_unsaved(True)
            bibfile.itemlist.page.save_bar.reveal()
            return None

        if "backup" in errors:
            bibfile.itemlist.page.backup_bar.reveal()

        GLib.idle_add(self.add_watcher, new_name)
        bibfile.created = False
        bibfile.set_unsaved(False)

        if close_data is not None:
            self.close_files_dialog(None, Gtk.ResponseType.CLOSE, *close_data)

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


import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk, GLib

from time import sleep

from threading import Thread

from .config_manager import add_to_recent
from .config_manager import remove_from_recent
from .config_manager import get_editor_layout
from .config_manager import get_parse_on_fly
from .config_manager import get_new_file_name
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

from .dialogs import FilterPopover
from .dialogs import SortPopover
from .dialogs import SaveChanges
from .dialogs import WarningDialog
from .dialogs import SaveDialog
from .dialogs import ConfirmSaveDialog


DEFAULT_EDITOR = get_default_entrytype()


class MainWidget(Gtk.Paned):
    def __init__(self, store):
        super().__init__()

        self.store = store
        self.itemlists = {}
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

        # Toolbar
        self.toolbar = ItemlistToolbar()
        self.toolbar.new_button.connect("clicked", self.add_items)
        self.toolbar.delete_button.connect("clicked", self.delete_selected_items)
        self.toolbar.sort_button.connect("clicked", self.sort_itemlist)
        self.toolbar.filter_button.connect("clicked", self.filter_itemlist)
        self.toolbar.goto_button.connect("clicked", self.focus_on_current_row)
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
        self.source_view.form.event_controller_key.connect("key-pressed", self.on_source_view_key_pressed)

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
        row = self.get_current_row()
        if row:
            row.unselect()
            row.select()
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

    def add_itemlist(self, bibfile, state=None, change_buffer=None):
        itemlist = Itemlist(bibfile, state, change_buffer)
        itemlist.connect("selected-rows-changed", self.on_row_selected)
        itemlist.event_controller.connect("key-pressed", self.on_itemlist_key_pressed)
        itemlist.header.close_button.connect("clicked", self.on_tab_closed)

        bibfile.itemlist = itemlist
        self.itemlists[bibfile.name] = itemlist
        self.notebook.append_itemlist(itemlist)

        if len(bibfile.items) == 0:
            self.source_view.set_status("empty", True)
            self.get_current_editor().clear()

        return itemlist

    def remove_itemlist(self, filename):
        itemlist = self.itemlists.pop(filename)
        self.store.bibfiles[filename].itemlist = None
        self.notebook.remove_page(itemlist.page.number)

    def get_current_itemlist(self):
        page = self.notebook.get_current_page()
        return self.notebook.get_nth_page(page).itemlist

    def on_itemlist_key_pressed(self, _event_controller_key, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Delete:
            self.delete_selected_items()
        if keyval == Gdk.KEY_Return:
            self.focus_on_current_row()

    def get_current_file(self):
        return self.get_current_itemlist().bibfile

    def get_current_row(self):
        if self.get_current_itemlist().get_n_selected() > 1:
            return None
        return self.get_current_itemlist().get_selected_row()

    def get_current_item(self):
        if self.get_current_itemlist().get_n_selected() > 1:
            return None

        row = self.get_current_row()
        if row:
            return row.item
        return None

    def get_selected_items(self, itemlist=None):
        if not itemlist:
            itemlist = self.get_current_itemlist()
        return [row.item for row in itemlist.get_selected_rows()]

    def add_items(self, _button=None, entries=[]):
        itemlist = self.get_current_itemlist()
        items = []

        if not entries:
            entries = [None]

        for entry in entries:
            item = itemlist.bibfile.append_item(entry)
            items.append(item)
            itemlist.add_row(item)

        change = Change.Show(items)
        itemlist.change_buffer.push_change(change)

    def delete_items(self, items):
        itemlist = self.get_current_itemlist()

        # prevents new row from being selected on key press
        itemlist.grab_focus()

        if items:
            change = Change.Hide(items)
            itemlist.change_buffer.push_change(change)

    def delete_selected_items(self, _button=None):
        items = self.get_selected_items()
        self.delete_items(items)

    def sort_itemlist(self, button):
        itemlist = self.get_current_itemlist()
        SortPopover(button, itemlist)

    def focus_on_current_row(self, _button=None):
        itemlist = self.get_current_itemlist()
        items = self.get_selected_items(itemlist)
        if items:
            itemlist.focus_idx = (itemlist.focus_idx + 1) % len(items)
            row = items[itemlist.focus_idx].row
            itemlist.get_adjustment().set_value(row.get_index() * row.get_height())

    def filter_itemlist(self, button):
        itemlist = self.get_current_itemlist()
        FilterPopover(button, itemlist)

    def search_itemlist(self, _button=None):
        searchbar = self.get_current_itemlist().page.searchbar
        searchbar.set_search_mode(not searchbar.get_search_mode())

    def on_row_selected(self, itemlist, row=None):
        itemlist.focus_idx = 0
        if itemlist.get_n_selected() > 1:
            self.get_current_editor().clear()
            self.source_view.clear()
            return None

        if not row:
            row = self.get_current_row()

        if row:
            entrytype = row.item.entry["ENTRYTYPE"]
            editor = self.show_editor(entrytype)
            editor.show_item(row.item)

            self.source_view.set_status("valid")
            self.source_view.form.set_sensitive(True)
            self.source_view.form.set_text(row.item.bibtex)

    def on_tab_closed(self, button=None):
        if button is None:
            itemlist = self.get_current_itemlist()
        else:
            itemlist = button.get_parent().itemlist
            # work around notebook selecting the closed page bug
            if self.notebook.previous_page is not None:
                self.notebook.set_current_page(self.notebook.previous_page)
        self.close_files(itemlist.bibfile.name)

    def on_switch_page(self, notebook, page, page_num):
        try:
            itemlist = page.itemlist
        except AttributeError:
            return None

        # prevents new row from being selected on tab change
        itemlist.grab_focus()

        # work around notebook selecting the closed page bug
        if notebook.current_page is not None:
            notebook.previous_page = notebook.current_page
        notebook.current_page = itemlist.page.number

        row = itemlist.get_selected_row()
        if row:
            self.on_row_selected(itemlist, row)
        else:
            self.source_view.set_status("empty", True)
            self.get_current_editor().clear()

    def generate_key(self):
        item = self.get_current_item()
        new_key = item.bibfile.generate_key_for_item(item)
        if new_key != item.entry["ID"]:
            editor = self.get_current_editor()
            form = editor.forms["ID"]
            old_key = item.entry["ID"]
            change = Change.Edit(item, form, old_key, new_key)
            item.bibfile.itemlist.change_buffer.push_change(change)

    def on_source_view_modified(self, _buffer):
        if get_parse_on_fly():
            self.update_bibtex()
        else:
            self.source_view.set_status("modified")

    def on_source_view_key_pressed(self, _event_controller_key, keyval, _keycode, state):
        if state == Gdk.ModifierType.CONTROL_MASK and keyval == Gdk.KEY_Return:
            self.update_bibtex()
            return True
        return False

    def update_bibtex(self, _button=None):
        bibtex = self.source_view.form.get_text()
        if bibtex:
            item = self.get_current_item()
            bibfile = self.get_current_file()
            new_entry = bibfile.parse_entry(bibtex)
            old_entry = item.entry
            if new_entry:
                self.source_view.set_status("valid")
                if not entries_equal(old_entry, new_entry):
                    change = Change.Replace(item, old_entry, new_entry)
                    item.bibfile.itemlist.change_buffer.push_change(change)
            else:
                self.source_view.set_status("invalid")

    def add_watcher(self, filename):
        self.watchers[filename] = Watcher(self, filename)

    def remove_watcher(self, filename):
        if filename in self.watchers:
            watcher = self.watchers.pop(filename)
            watcher.monitor.cancel()

    def open_files(self, filenames, states=None, select_file=None):
        # make sure 'filenames' is a list
        if isinstance(filenames, str):
            filenames = [filenames]
        N = len(filenames)

        # close default empty file
        close_empty = self.notebook.contains_empty_new_file()

        # initialize empty state string list
        if not states:
            states = N * [None]

        # add loading pages and select first one
        n_pages = self.notebook.get_n_pages()
        self.notebook.add_loading_pages(N)
        self.notebook.set_current_page(n_pages)

        # open files in thread
        GLib.idle_add(self.open_files_thread, filenames, states, select_file, close_empty)

    def open_files_thread(self, filenames, states, select_file, close_empty):
        # read databases
        statuses = [self.store.add_file(filename) for filename in filenames]

        # remove loading pages
        self.notebook.remove_loading_pages()

        # add itemlists
        messages = []
        first_file = None
        for filename, status, state in zip(filenames, statuses, states):

            # file does not exist or cannot be read
            if "file_error" in status or "parse_error" in status:
                remove_from_recent(filename)
                self.get_root().update_recent_file_menu()
                if not self.store.bibfiles:
                    self.new_file()
                message = "Cannot read file '{}'.".format(filename)
                messages.append(message)
                continue

            # file is empty
            if "empty" in status:
                message = "No BibTeX entries found in file '{}'.".format(filename)
                messages.append(message)

            # could not create backup
            if "no_backup" in status:
                message = (
                    "Bada Bib! could not create a backup for '{}'".format(filename)
                    + "\n\n"
                    + "To fix this, try deleting or renaming any .bak-files that were not created by Bada Bib!"
                    + "\n\n"
                    + "<b>Be careful when editing this file!</b>"
                )
                messages.append(message)

            if "file_open" in status:
                # get itemlist if file is already open
                itemlist = self.itemlists[filename]
            else:
                # or add itemlist and watcher
                itemlist = self.add_itemlist(self.store.bibfiles[filename], state)
                self.add_watcher(filename)

            if not first_file:
                first_file = filename
                if not select_file:
                    select_file = first_file

        # remove empty default file
        if close_empty:
            self.close_files(get_new_file_name(), force=True)

        # select requested page
        if select_file:
            for n in range(self.notebook.get_n_pages()):
                itemlist = self.notebook.get_nth_page(n).itemlist
                if itemlist.bibfile.name == select_file:
                    self.notebook.set_current_page(itemlist.page.number)

        # display warnings, if any
        if messages:
            WarningDialog(messages, self.get_root())

    def new_file(self):
        bibfile = self.store.new_file()
        itemlist = self.add_itemlist(bibfile)
        self.notebook.set_current_page(itemlist.page.number)

    def reload_file(self, filename):
        itemlist = self.itemlists[filename]
        state = itemlist.state_to_string()
        page_number = itemlist.page.number

        self.notebook.add_loading_pages(1)
        loading_page = self.notebook.get_nth_page(-1)
        self.notebook.reorder_child(loading_page, page_number)
        self.notebook.set_current_page(page_number)

        close_empty = self.notebook.contains_empty_new_file()

        self.close_files(filename, force=True)
        GLib.idle_add(self.open_files_thread, [filename], state, None, close_empty)

        thread = Thread(target=self.move_new_tab, args=(filename, page_number))
        thread.start()

    def move_new_tab(self, filename, page_number):
        # wait for file to finish opening
        while True:
            try:
                last_page = self.notebook.get_nth_page(-1)
                if last_page.itemlist.bibfile.name == filename:
                    break
            except AttributeError:
                pass
            sleep(0.02)
        self.notebook.reorder_child(last_page, page_number)

    def declare_file_created(self, filename):
        self.store.bibfiles[filename].created = True
        self.itemlists[filename].set_unsaved(True)
        self.watchers.pop(filename)

    def close_files(self, filenames, force=False, close_app=False):
        # make sure 'filenames' is a list
        if not isinstance(filenames, list):
            filenames = [filenames]
        self.close_files_dialog(None, Gtk.ResponseType.CLOSE, filenames, 0, force, close_app)

    def close_files_dialog(self, dialog, response, filenames, n, force, close_app):
        if dialog:
            dialog.destroy()

        if response == Gtk.ResponseType.CANCEL:
            return None
        if response == Gtk.ResponseType.OK:
            close_data = (filenames, n-1, force, close_app)
            self.save_file(filenames[n-1], close_data)
            return None

        itemlist = self.itemlists[filenames[n]]
        if itemlist.bibfile.unsaved and not force:
            self.notebook.set_current_page(itemlist.page.number)
            dialog = SaveChanges(self.get_root(), filenames[n])
            if n < len(filenames) - 1:
                dialog.connect("response", self.close_files_dialog, filenames, n+1, force, close_app)
            else:
                dialog.connect("response", self.close_files_finalize, filenames, n+1, force, close_app)
            dialog.show()
        else:
            if n < len(filenames) - 1:
                self.close_files_dialog(None, Gtk.ResponseType.CLOSE, filenames, n+1, force, close_app)
            else:
                self.close_files_finalize(None, Gtk.ResponseType.CLOSE, filenames, n+1, force, close_app)

    def close_files_finalize(self, dialog, response, filenames, n, force, close_app):
        if dialog:
            dialog.destroy()

        if response == Gtk.ResponseType.CANCEL:
            return None
        if response == Gtk.ResponseType.OK:
            close_data = (filenames, n-1, force, close_app)
            self.save_file(filenames[n-1], close_data)
            return None

        if close_app:
            self.get_root().session_manager.save()

        for filename in filenames:
            bibfile = self.store.bibfiles[filename]
            if not bibfile.created and not close_app:
                add_to_recent(bibfile)
                self.get_root().update_recent_file_menu()

            self.remove_itemlist(filename)
            self.remove_watcher(filename)
            self.store.remove_file(filename)

        if self.notebook.get_n_pages() == 0 and not close_app:
            self.new_file()

        if close_app:
            self.get_root().destroy()

    def save_file(self, filename=None, close_data=None):
        if not filename:
            itemlist = self.get_current_itemlist()
            filename = itemlist.bibfile.name
        else:
            itemlist = self.itemlists[filename]
        bibfile = itemlist.bibfile

        if bibfile.unsaved:
            if bibfile.created:
                self.save_file_as(close_data=close_data)
            else:
                self.save_file_as(filename, filename, close_data)

    def save_all_files(self):
        for filename in self.store.bibfiles:
            self.save_file(filename)

    def save_file_as(self, new_name=None, old_name=None, close_data=None):
        if not old_name:
            itemlist = self.get_current_itemlist()
            old_name = itemlist.bibfile.name
        else:
            itemlist = self.itemlists[old_name]
        bibfile = itemlist.bibfile

        self.confirm_save_dialog(new_name, old_name, bibfile, close_data)

    def confirm_save_dialog(self, new_name, old_name, bibfile, close_data):
        has_empty_keys = bibfile.has_empty_keys()
        duplicate_keys = bibfile.get_duplicate_keys()
        if has_empty_keys or duplicate_keys:
            dialog = ConfirmSaveDialog(self.get_root(), old_name, has_empty_keys, duplicate_keys)
            dialog.connect("response", self.save_file_dialog, new_name, old_name, bibfile, close_data)
            dialog.show()
        else:
            self.save_file_dialog(None, Gtk.ResponseType.YES, new_name, old_name, bibfile, close_data)

    def save_file_dialog(self, dialog, response, new_name, old_name, bibfile, close_data):
        if dialog:
            dialog.destroy()

        if response != Gtk.ResponseType.YES:
            return None

        if not new_name:
            dialog = SaveDialog(self.get_root())
            dialog.connect("response", self.save_file_as_finalize, new_name, old_name, bibfile, close_data)
            dialog.show()
        else:
            self.save_file_as_finalize(None, None, new_name, old_name, bibfile, close_data)

    def save_file_as_finalize(self, dialog, response, new_name, old_name, bibfile, close_data):
        if dialog:
            dialog.destroy()
            if response == Gtk.ResponseType.ACCEPT:
                new_name = dialog.get_file().get_path()
                new_name = new_name.strip()
                if new_name[-4:] != ".bib":
                    new_name = new_name + ".bib"
            else:
                return None

        if close_data:
            files = close_data[0]
            n = close_data[1]
            files[n] = new_name

        if new_name != old_name:
            if new_name in self.store.bibfiles:
                self.close_files(new_name, force=True)

            if not bibfile.created:
                add_to_recent(bibfile)
                self.get_root().update_recent_file_menu()

            self.itemlists.pop(old_name)
            self.store.rename_file(old_name, new_name)
            self.itemlists[new_name] = bibfile.itemlist

        bibfile.created = False
        bibfile.itemlist.update_filename(new_name)
        bibfile.itemlist.set_unsaved(False)
        bibfile.itemlist.page.deleted_bar.set_revealed(False)
        bibfile.itemlist.change_buffer.update_saved_state()

        self.remove_watcher(old_name)
        self.store.save_file(new_name)
        self.add_watcher(new_name)

        if close_data is not None:
            self.close_files_dialog(None, Gtk.ResponseType.CLOSE, *close_data)

# itemlist.py
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


from gi.repository import Gtk, Gdk, Gio

from os.path import split

from .change import ChangeBuffer

from .config_manager import entrytype_dict
from .config_manager import link_fields
from .config_manager import get_row_indent
from .config_manager import get_new_file_name


row_indent = get_row_indent() * " "

entrytypes = list(entrytype_dict.keys()) + ["other"]

MIN_MAX_CHAR = ('', chr(0x10FFFF))
ROW_HEIGHT = 95


class ItemlistNotebook(Gtk.Notebook):
    def __init__(self):
        super().__init__()
        self.set_scrollable(True)
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.popup_enable()

        # work around notebook selecting the closed page bug
        self.previous_page = None
        self.current_page = None

        self.connect("page-reordered", self.update_pagenumbers)
        self.connect("page-added", self.update_pagenumbers)

    def add_itemlist_page(self, name, page_num=None):
        page = ItemlistPage(name)
        if page_num is None:
            page.number = self.append_page(page, page.header)
        else:
            page.number = self.insert_page(page, page.header, page_num)
        self.set_menu_label_text(page, name)
        self.set_tab_reorderable(page, True)
        return page

    def contains_empty_new_file(self):
        if self.get_n_pages() != 1:
            return False
        itemlist = self.get_nth_page(0).itemlist
        if itemlist is None:
            return False
        bibfile = itemlist.bibfile
        if bibfile.name == get_new_file_name() and bibfile.is_empty():
            return bibfile
        return False

    def next_page(self, delta):
        n_pages = self.get_n_pages()
        if n_pages > 1:
            n_page = self.get_current_page()
            self.set_current_page((n_page + delta) % n_pages)

    @staticmethod
    def update_pagenumbers(notebook, _page, _page_num):
        n_pages = notebook.get_n_pages()
        for n in range(n_pages):
            notebook.get_nth_page(n).number = n


class TabHeader(Gtk.Box):
    def __init__(self, page, name):
        super().__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.page = page

        self.title_label = Gtk.Label()

        self.close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.close_button.set_has_frame(False)

        self.append(self.title_label)
        self.append(self.close_button)

        self.update(name=name)

    def disassemble(self):
        self.remove(self.title_label)
        self.remove(self.close_button)
        self.page = None

    def update(self, unsaved=False, name=None):
        if name:
            base_name = split(name)[1]
        elif self.page.itemlist:
            name = self.page.itemlist.bibfile.name
            base_name = self.page.itemlist.bibfile.base_name
        if unsaved:
            base_name = "*" + base_name

        self.title_label.set_text(base_name)
        self.set_tooltip_text(name)


class ItemlistPage(Gtk.Box):
    def __init__(self, name):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.itemlist = None
        self.number = -1
        self.header = TabHeader(self, name=name)

        self.center_box = Gtk.CenterBox(orientation=Gtk.Orientation.VERTICAL)
        self.center_box.set_vexpand(True)

        self.deleted_bar = ItemlistInfoBar("File was deleted, renamed or moved.\nYou are now editing an unsaved copy.")
        self.empty_bar = ItemlistInfoBar("File does not contain any BibTeX entries.")
        self.backup_bar = ItemlistInfoBar("<b>Bada Bib! was unable to create a backup file!</b>\nTry deleting or renaming any .bak-files that were not created by Bada Bib!")
        self.save_bar = ItemlistInfoBar("<b>File could not be saved!</b>\nYou might not have write permissions for this file or folder.")
        self.changed_bar = ItemlistChangedBar()
        self.searchbar = ItemlistSearchBar()

        self.set_vexpand(True)
        self.set_hexpand(True)

        self.show_loading_screen()

    def disassemble(self):
        self.header.disassemble()
        self.remove(self.deleted_bar)
        self.remove(self.empty_bar)
        self.remove(self.backup_bar)
        self.remove(self.save_bar)
        self.remove(self.changed_bar)
        self.remove(self.scrolled_window)
        self.remove(self.searchbar)
        self.itemlist = None
        self.header = None

    def add_itemlist(self, itemlist):
        self.itemlist = itemlist
        self.itemlist.page = self
        self.searchbar.search_entry.connect("search_changed", self.itemlist.set_search_string)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_child(itemlist)

        self.append(self.deleted_bar)
        self.append(self.empty_bar)
        self.append(self.backup_bar)
        self.append(self.save_bar)
        self.append(self.changed_bar)
        self.append(self.scrolled_window)
        self.append(self.searchbar)

        self.remove(self.center_box)

    def show_loading_screen(self):
        loading_image = Gtk.Image.new_from_icon_name("preferences-system-time-symbolic")
        loading_image.set_pixel_size(100)

        loading_label = Gtk.Label()
        loading_label.set_margin_top(10)
        loading_label.set_markup("<big>Loading...</big>")
        loading_label.set_justify(Gtk.Justification.CENTER)

        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        loading_box.append(loading_image)
        loading_box.append(loading_label)

        self.center_box.set_center_widget(loading_box)
        self.append(self.center_box)

    def show_error_screen(self, status):
        if "file_error" in status:
            message = "Cannot open file.\nFile might have been moved or deleted."
        elif "parse_error" in status:
            message = "Cannot parse file.\nFile might be corrupted or might not be a BibTeX file."
        else:
            message = "Cannot open file."

        error_image = Gtk.Image.new_from_icon_name("computer-fail-symbolic")
        error_image.set_pixel_size(100)

        error_label = Gtk.Label()
        error_label.set_margin_top(10)
        error_label.set_text(message)
        error_label.set_justify(Gtk.Justification.CENTER)

        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        error_box.append(error_image)
        error_box.append(error_label)

        self.center_box.set_center_widget(error_box)


class ItemlistInfoBar(Gtk.InfoBar):
    def __init__(self, message):
        super().__init__()
        self.message = message
        self.label = Gtk.Label()
        self.add_child(self.label)
        self.set_revealed(False)
        self.set_show_close_button(True)
        self.connect("response", self.on_response)

    def show_text(self, state):
        if state:
            self.label.set_markup(self.message)
        else:
            self.label.set_text("")

    def reveal(self):
        self.show_text(True)
        self.set_revealed(True)

    def on_response(self, infobar, response):
        if response == Gtk.ResponseType.CLOSE:
            self.set_revealed(False)
            self.show_text(False)


class ItemlistChangedBar(Gtk.InfoBar):
    def __init__(self):
        super().__init__()
        self.label = Gtk.Label(label="")
        self.add_child(self.label)
        self.set_revealed(False)
        self.set_show_close_button(True)

        self.add_button("Reload", Gtk.ResponseType.YES)
        self.connect("response", self.on_response)

    def show_text(self, state):
        if state:
            self.label.set_text("This file changed on disk or was edited in another application.\nYou are now editing an unsaved copy.")
        else:
            self.label.set_text("")

    def reveal(self):
        self.show_text(True)
        self.set_revealed(True)

    def on_response(self, infobar, response):
        if response == Gtk.ResponseType.CLOSE:
            self.set_revealed(False)
            self.show_text(False)
        elif response == Gtk.ResponseType.YES:
            self.set_revealed(False)
            self.show_text(False)
            window = self.get_root()
            bibfile = window.main_widget.get_current_itemlist().bibfile
            window.main_widget.reload_file(bibfile)


class ItemlistSearchBar(Gtk.SearchBar):
    def __init__(self):
        super().__init__()
        self.search_entry = Gtk.SearchEntry()
        self.set_child(self.search_entry)
        self.connect_entry(self.search_entry)


class ItemlistToolbar(Gtk.CenterBox):
    def __init__(self):
        super().__init__()
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.assemble()

    def assemble(self):
        self.delete_button = Gtk.Button.new_with_label("Delete")
        self.delete_button.set_margin_start(5)
        self.delete_button.get_style_context().add_class("destructive-action")
        self.delete_button.set_tooltip_text("Delete entry")
        self.set_start_widget(self.delete_button)

        self.new_button = Gtk.Button.new_with_label("New")
        self.new_button.set_margin_end(5)
        self.new_button.get_style_context().add_class("suggested-action")
        self.new_button.set_tooltip_text("Create new entry")
        self.set_end_widget(self.new_button)

        center_box = Gtk.Box()
        self.set_center_widget(center_box)

        self.search_button = Gtk.Button.new_from_icon_name("system-search-symbolic")
        self.search_button.set_tooltip_text("Search entry list")
        center_box.prepend(self.search_button)

        self.sort_button = Gtk.Button.new_with_label("Sort")
        self.sort_button.set_tooltip_text("Sort entry list")
        self.sort_button.set_margin_end(2)
        center_box.prepend(self.sort_button)

        self.filter_button = Gtk.Button.new_with_label("Filter")
        self.filter_button.set_tooltip_text("Filter entry list")
        self.filter_button.set_margin_end(2)
        center_box.prepend(self.filter_button)

        image = Gtk.Image.new_from_resource("/com/github/rogercrocker/badabib/icons/find-location-symbolic.svg")
        self.goto_button = Gtk.Button()
        self.goto_button.set_child(image)
        self.goto_button.set_tooltip_text("Go to selected entry")
        self.goto_button.set_margin_end(2)
        center_box.prepend(self.goto_button)


class Row(Gtk.ListBoxRow):
    def __init__(self, item):
        super().__init__()
        self.set_activatable(False)
        self.item = item

        self.id_label = Gtk.Label(xalign=0)
        self.author_label = Gtk.Label(xalign=0)
        self.title_label = Gtk.Label(xalign=0)
        self.journal_label = Gtk.Label(xalign=0)
        self.publisher_label = Gtk.Label(xalign=0)

        self.link_image = Gtk.Image()
        self.link_image.set_margin_start(10)

        self.assemble()
        self.update()

    def assemble(self):
        self.idbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.idbox.set_margin_top(5)
        self.idbox.append(self.id_label)
        self.idbox.append(self.link_image)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.append(self.idbox)
        self.vbox.append(self.author_label)
        self.vbox.append(self.title_label)
        self.vbox.append(self.journal_label)
        self.vbox.append(self.publisher_label)

        self.set_child(self.vbox)

    def disassemble(self):
        self.vbox.remove(self.idbox)
        self.vbox.remove(self.author_label)
        self.vbox.remove(self.title_label)
        self.vbox.remove(self.journal_label)
        self.vbox.remove(self.publisher_label)
        self.item = None

    def update(self):
        for field in ["ID", "author", "title", "journal", "publisher"]:
            self.update_field(field)
        self.update_link()

    def update_field(self, field):
        if field in ["ID", "ENTRYTYPE"]:
            self.update_id()
        elif field in ["author", "editor"]:
            self.update_author()
        elif field == "title":
            self.update_title()
        elif field in ["journal", "booktitle"]:
            self.update_journal()
        elif field in ["publisher", "year"]:
            self.update_publisher()
        elif field in link_fields:
            self.update_link()

    def update_id(self):
        label = row_indent
        if "ID" in self.item.entry:
            label += self.item.entry["ID"]
        label = f"""<b>{label}</b> ({self.item.pretty_field("ENTRYTYPE")})"""
        self.id_label.set_markup(label)
        self.changed()

    def update_author(self):
        label = row_indent
        if "author" in self.item.entry:
            label += self.item.pretty_field("author")
        if "editor" in self.item.entry:
            if label != row_indent:
                label += ", "
            label += f"""Ed: {self.item.pretty_field("editor")}"""
        self.author_label.set_markup(label)
        self.changed()

    def update_title(self):
        label = row_indent
        if "title" in self.item.entry:
            label += self.item.pretty_field("title")
        self.title_label.set_markup(label)
        self.changed()

    def update_journal(self):
        label = row_indent
        if "journal" in self.item.entry:
            label += f"""<i>{self.item.pretty_field("journal")}</i>"""
        if "booktitle" in self.item.entry:
            if label != row_indent:
                label += ", "
            label += f"""<i>{self.item.pretty_field("booktitle")}</i>"""
        self.journal_label.set_markup(label)
        self.changed()

    def update_publisher(self):
        label = row_indent
        if "publisher" in self.item.entry:
            label += self.item.pretty_field("publisher")
        if "year" in self.item.entry:
            if label != row_indent:
                label += ", "
            label += self.item.pretty_field("year")
        self.publisher_label.set_markup(label)
        self.changed()

    def update_link(self):
        if set(link_fields) & set(self.item.entry.keys()):
            self.link_image.set_from_icon_name("mail-attachment-symbolic")
        else:
            self.link_image.clear()


class Itemlist(Gtk.ListBox):
    def __init__(self, bibfile, state_string=None, change_buffer=None):
        super().__init__()
        self.bibfile = bibfile
        self.page = None
        self.focus_idx = 0

        self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.set_activate_on_single_click(False)

        self.sort_key = "ID"
        self.sort_reverse = False
        self.search_string = ""
        self.fltr = {entrytype: True for entrytype in entrytypes}

        if state_string:
            self.string_to_state(state_string)

        self.set_sort_func(self.sort_by_field)
        self.set_filter_func(self.filter_by_search)

        self.set_show_separators(True)

        self.event_controller = Gtk.EventControllerKey()
        self.add_controller(self.event_controller)

        # Dropping multiple files is not supported right now
        # Compare: https://discourse.gnome.org/t/drag-dropping-files-with-gtk4/6084
        self.drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        self.add_controller(self.drop_target)

        if change_buffer:
            self.change_buffer = change_buffer
        else:
            self.change_buffer = ChangeBuffer()

        self.add_rows(bibfile.items)

    def unref(self):
        self.page.disassemble()
        while True:
            row = self.get_row_at_index(0)
            if not row:
                break
            row.disassemble()
            self.remove(row)
        self.page = None
        self.bibfile = None
        self.change_buffer = None

    def update_filename(self):
        self.page.header.update()

    def set_unsaved(self, unsaved):
        if unsaved and not self.bibfile.unsaved:
            self.page.header.update(unsaved=True)
        elif not unsaved and self.bibfile.unsaved:
            self.page.header.update(unsaved=False)
            self.page.deleted_bar.set_revealed(False)
            self.change_buffer.update_saved_state()

    def add_row(self, item):
        row = Row(item)
        self.append(row)
        item.row = row
        return row

    def add_rows(self, items):
        for item in items:
            self.add_row(item)

    def get_next_row(self, row, increment):
        while row:
            index = row.get_index()
            row = self.get_row_at_index(index + increment)
            if row and self.filter_by_search(row):
                return row
        return None

    def select_next_row(self, row):
        # get next row...
        next_row = self.get_next_row(row, 1)
        if not next_row:
            next_row = self.get_next_row(row, -1)

        # ...and select it
        if next_row:
            self.select_row(next_row)
            return next_row

        # ...or unselect all and return None
        self.unselect_all()
        return None

    def focus_on_selected_items(self, idx=None):
        items = self.get_selected_items()
        if items:
            if idx is None:
                self.focus_idx = (self.focus_idx + 1) % len(items)
                idx = self.focus_idx
            row = items[idx].row
            preceeding_rows = 0
            while row := self.get_next_row(row, -1):
                preceeding_rows += 1
            self.get_adjustment().set_value(preceeding_rows * ROW_HEIGHT)

    def reselect_rows(self, rows, adj=None):
        self.unselect_all()
        for row in rows:
            self.select_row(row)
        if adj is not None:
            self.get_adjustment().set_value(adj)

    def get_selected_items(self):
        return [row.item for row in self.get_selected_rows()]

    def refresh(self):
        index = 0
        while True:
            row = self.get_row_at_index(index)
            if not row:
                break
            row.item.refresh()
            row.update()
            index += 1
        rows = self.get_selected_rows()
        self.reselect_rows(rows)

    def set_search_string(self, search_entry):
        self.search_string = search_entry.get_text()
        self.invalidate_filter()

    def sort_by_field(self, row1, row2):
        items = (row1.item, row2.item)
        values = [0, 0]

        for n, item in enumerate(items):
            # sort entries without ID to the top, irrespective of sort order
            if item.entry["ID"]:
                values[n] = item.sort_values[self.sort_key]
            else:
                values[n] = MIN_MAX_CHAR[self.sort_reverse]

        # fall back to ID if ordering is ambigious
        if values[0] == values[1] and values[0] not in MIN_MAX_CHAR:
            values = [items[0].sort_values["ID"], items[1].sort_values["ID"]]

        comp = 1 if values[0] >= values[1] else -1

        if self.sort_reverse:
            return -comp

        return comp

    def filter_by_search(self, row):
        search = self.search_string.lower()
        item = row.item

        if item.deleted:
            return False
        if item.entry["ENTRYTYPE"] not in self.fltr:
            return self.fltr["other"]
        if not self.fltr[item.entry["ENTRYTYPE"]]:
            return False
        if not item.entry["ID"]:
            return True

        # poor man's fuzzy search
        phrases = search.split('"')
        quoted = [False]
        for phrase in phrases[1:]:
            quoted.append(not quoted[-1])
        if len(phrases) % 2 == 0:
            quoted[-1] = False

        for phrase, protected in filter(None, zip(phrases, quoted)):
            if protected:
                words = [phrase]
            else:
                words = phrase.split()
            for word in words:
                for field in item.entry:
                    if word in item.raw_field(field).lower():
                        break
                    if word in item.pretty_field(field).lower():
                        break
                else:
                    return False
        return True

    def state_to_string(self):
        string = f"{self.sort_key}|{self.sort_reverse}"
        for value in self.fltr.values():
            string += f"|{value}"
        return string

    def string_to_state(self, text):
        values = text.split("|")
        if len(values) < 2:
            return

        self.sort_key = values.pop(0)
        self.sort_reverse = values.pop(0) == "True"
        for entrytype in entrytypes:
            if values:
                value = values.pop(0)
            else:
                value = "True"
            self.fltr[entrytype] = value == "True"

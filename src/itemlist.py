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


import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from os.path import split

from .change import ChangeBuffer

from .config_manager import entrytype_dict
from .config_manager import link_fields
from .config_manager import get_row_indent
from .config_manager import get_new_file_name
from .config_manager import SourceViewStatus


row_indent = get_row_indent() * " "

MIN_MAX_CHAR = ('', chr(0x10FFFF))


class ItemlistNotebook(Gtk.Notebook):
    def __init__(self):
        Gtk.Notebook.__init__(self)
        self.set_scrollable(True)
        self.popup_enable()

        self.connect("page-reordered", self.update_pagenumbers)
        self.connect("page-added", self.update_pagenumbers)
        self.connect("page-removed", self.update_pagenumbers)

    def append_itemlist(self, itemlist):
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(itemlist)
        page = self.append_page(scrolled, itemlist.header)
        itemlist.on_page = page
        self.set_menu_label_text(scrolled, itemlist.header.title_label.get_label())
        self.set_tab_reorderable(scrolled, True)
        self.set_current_page(page)

        return page

    def contains_empty_new_file(self):
        if self.get_n_pages() == 1:
            try:
                scrolled = self.get_nth_page(0)
                itemlist = scrolled.get_child().get_child()
            except AttributeError:
                return False
            if itemlist.bibfile.name == get_new_file_name() and len(itemlist) == 0:
                return True
        return False

    def add_loading_page(self):
        image = Gtk.Image.new_from_icon_name("preferences-system-time-symbolic", Gtk.IconSize.DIALOG)
        image.show()

        page = self.append_page(image, None)
        self.set_tab_label_text(image, "Loading...")
        self.set_current_page(page)

    def remove_loading_page(self):
        n_pages = self.get_n_pages()
        for n in range(n_pages):
            page = self.get_nth_page(n)
            if isinstance(page, Gtk.Image):
                self.remove_page(n)

    def update_pagenumbers(self, notebook, _itemlist, _page):
        n_pages = notebook.get_n_pages()
        for page in range(n_pages):
            try:
                scrolled = notebook.get_nth_page(page)
                itemlist = scrolled.get_child().get_child()
                itemlist.on_page = page
            except AttributeError:
                pass


class ItemlistSearchBar(Gtk.SearchBar):
    def __init__(self):
        Gtk.SearchBar.__init__(self)
        self.search_entry = Gtk.SearchEntry()
        self.add(self.search_entry)
        self.connect_entry(self.search_entry)


class ItemlistToolbar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.assemble()

    def assemble(self):
        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.new_button = Gtk.Button.new_with_label("New")
        self.new_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.new_button.set_tooltip_text("Create new entry")
        self.pack_end(self.new_button, False, False, 5)

        self.delete_button = Gtk.Button.new_with_label("Delete")
        self.delete_button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.delete_button.set_tooltip_text("Delete entry")
        self.pack_start(self.delete_button, False, False, 5)

        center_box = Gtk.Box()
        center_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_center_widget(center_box)

        self.search_button = Gtk.Button.new_from_icon_name("system-search-symbolic", Gtk.IconSize.BUTTON)
        self.search_button.set_tooltip_text("Search entry list")
        center_box.pack_start(self.search_button, False, False, 5)

        self.sort_button = Gtk.Button.new_with_label("Sort")
        self.sort_button.set_tooltip_text("Sort entry list")
        center_box.pack_start(self.sort_button, False, False, 5)

        self.filter_button = Gtk.Button.new_with_label("Filter")
        self.filter_button.set_tooltip_text("Filter entry list")
        center_box.pack_start(self.filter_button, False, False, 5)

        self.goto_button = Gtk.Button.new_from_icon_name("find-location-symbolic", Gtk.IconSize.BUTTON)
        self.goto_button.set_tooltip_text("Go to selected entry")
        center_box.pack_start(self.goto_button, False, False, 5)


class TabHeader(Gtk.Box):
    def __init__(self, itemlist):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.itemlist = itemlist

        head_tail = split(itemlist.bibfile.name)
        self.title_label = Gtk.Label(label=head_tail[1])
        self.set_tooltip_text(itemlist.bibfile.name)

        self.close_button = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        self.close_button.set_relief(Gtk.ReliefStyle.NONE)

        self.pack_start(self.title_label, True, True, 0)
        self.pack_end(self.close_button, False, False, 0)

        self.show_all()


class Row(Gtk.ListBoxRow):
    def __init__(self, item):
        Gtk.ListBoxRow.__init__(self)
        self.item = item

        self.id_label = Gtk.Label(xalign=0)
        self.author_label = Gtk.Label(xalign=0)
        self.title_label = Gtk.Label(xalign=0)
        self.journal_label = Gtk.Label(xalign=0)
        self.publisher_label = Gtk.Label(xalign=0)

        self.link_image = Gtk.Image()
        self.link_image.set_margin_start(10)
        self.link_icon_size = Gtk.IconSize.SMALL_TOOLBAR

        self.assemble()
        self.update()

    def assemble(self):
        idbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        idbox.set_margin_top(5)
        idbox.pack_start(self.id_label, False, True, 0)
        idbox.pack_start(self.link_image, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(idbox, True, True, 0)
        vbox.pack_start(self.author_label, True, True, 0)
        vbox.pack_start(self.title_label, True, True, 0)
        vbox.pack_start(self.journal_label, True, True, 0)
        vbox.pack_start(self.publisher_label, True, True, 0)

        self.add(vbox)

    def update(self):
        for field in ["ID", "author", "title", "journal", "publisher"]:
            self.update_field(field)
        self.update_link()

    def update_field(self, field):
        if field in ["ID", "ENTRYTYPE"]:
            self.update_id()
        elif field == "author":
            self.update_author()
        elif field == "title":
            self.update_title()
        elif field in ["journal", "booktitle"]:
            self.update_journal()
        elif field in ["publisher", "year"]:
            self.update_publisher()
        elif field in link_fields:
            self.update_link()
        self.select()

    def update_id(self):
        string = row_indent
        if "ID" in self.item.entry:
            string += self.item.entry["ID"]
        self.id_label.set_markup("<b>" + string + "</b> (" + self.item.pretty_field("ENTRYTYPE") + ")")
        self.changed()

    def update_author(self):
        string = row_indent
        if "author" in self.item.entry:
            string += self.item.pretty_field("author")
        if "editor" in self.item.entry:
            if string != row_indent:
                string += ", "
            string += "Ed: " + self.item.pretty_field("editor")
        self.author_label.set_markup(string)
        self.changed()

    def update_title(self):
        string = row_indent
        if "title" in self.item.entry:
            string += self.item.pretty_field("title")
        self.title_label.set_markup(string)
        self.changed()

    def update_journal(self):
        string = row_indent
        if "journal" in self.item.entry:
            string += "<i>" + self.item.pretty_field("journal") + "</i>"
        if "booktitle" in self.item.entry:
            if string != row_indent:
                string += ", "
            string += "<i>" + self.item.pretty_field("booktitle") + "</i>"
        self.journal_label.set_markup(string)
        self.changed()

    def update_publisher(self):
        string = row_indent
        if "publisher" in self.item.entry:
            string += self.item.pretty_field("publisher")
        if "year" in self.item.entry:
            if string != row_indent:
                string += ", "
            string += self.item.pretty_field("year")
        self.publisher_label.set_markup(string)
        self.changed()

    def update_link(self):
        if set(link_fields) & set(self.item.entry.keys()):
            self.link_image.set_from_icon_name("mail-attachment-symbolic", self.link_icon_size)
        else:
            self.link_image.clear()

    def select(self):
        if not self.is_selected() and self.item.bibfile.itemlist != None:
            self.item.bibfile.itemlist.select_row(self)

    def unselect(self):
        if self.is_selected() and self.item.bibfile.itemlist != None:
            self.item.bibfile.itemlist.unselect_row(self)

    def get_next(self, increment):
        row = self
        while row:
            index = row.get_index()
            row = row.item.bibfile.itemlist.get_row_at_index(index + increment)
            if row and not row.item.deleted:
                return row
        return None


class Itemlist(Gtk.ListBox):
    def __init__(self, bibfile, state_string=None, change_buffer=None):
        Gtk.ListBox.__init__(self)
        self.bibfile = bibfile
        self.unsaved = False
        self.on_page = -1

        self.sort_key = "ID"
        self.sort_reverse = False
        self.search_string = ""
        self.fltr = {entytype: True for entytype in entrytype_dict}

        if state_string:
            self.string_to_state(state_string)

        self.set_sort_func(self.sort_by_field)
        self.set_filter_func(self.filter_by_search)

        self.header = TabHeader(self)
        self.set_header_func(self.add_separator)

        if change_buffer:
            self.change_buffer = change_buffer
        else:
            self.change_buffer = ChangeBuffer()

        self.add_rows(bibfile.items)

    def add_separator(self, row, before):
        if before:
            row.set_header(Gtk.Separator())
        else:
            row.set_header(None)

    def update_filename(self, name):
        self.bibfile.update_filename(name)
        self.header.set_tooltip_text(name)
        header_children = self.header.get_children()
        label = header_children[0]
        label.set_label(self.bibfile.tail)

    def set_unsaved(self, unsaved):
        if unsaved and not self.unsaved:
            self.unsaved = unsaved
            children = self.header.get_children()
            label = children[0]
            text = label.get_label()
            label.set_label("*" + text)
        elif not unsaved and self.unsaved:
            self.unsaved = unsaved
            self.update_filename(self.bibfile.name)

    def add_row(self, item):
        row = Row(item)
        self.add(row)
        item.row = row
        return row

    def add_rows(self, items):
        for item in items:
            self.add_row(item)

    def row_deleted(self, row):
        self.invalidate_filter()
        next_row = row.get_next(1)
        if not next_row:
            next_row = row.get_next(-1)

        if next_row:
            next_row.select()
            return False
        else:
            self.unselect_all()
            window = self.get_toplevel()
            window.main_widget.source_view.set_status(SourceViewStatus.empty)
            return True

    def reselect_current_row(self):
        row = self.get_selected_row()
        if row:
            row.unselect()
            row.select()

    def refresh(self):
        current_row = self.get_selected_row()
        row = self.get_row_at_index(0)
        while row:
            row.item.refresh()
            row.update()
            row = row.get_next(1)
        self.select_row(current_row)

    def clear(self):
        self.foreach(lambda row, data : self.remove(row), None)

    def sort_by_field(self, row1, row2):
        items = (row1.item, row2.item)
        values = [0, 0]

        for n, item in enumerate(items):
            if not item.entry["ID"]:
                # sort entries without ID to the top
                values[n] = MIN_MAX_CHAR[self.sort_reverse]
            elif item.sort_values[self.sort_key]:
                values[n] = item.sort_values[self.sort_key]
            else:
                # sort entries without sort key field to the bottom
                values[n] = MIN_MAX_CHAR[not self.sort_reverse]

        # fall back to ID if ordering is ambigious
        if values[0] == values[1] and values[0] not in MIN_MAX_CHAR:
            values = [items[0].sort_values["ID"], items[1].sort_values["ID"]]

        comp = 1 if values[0] >= values[1] else -1

        if self.sort_reverse:
            return -comp
        else:
            return comp

    def filter_by_search(self, row):
        search = self.search_string.lower()
        item = row.item

        if item.deleted:
            return False
        if item.entry["ENTRYTYPE"] not in self.fltr:
            return True
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
        string = self.sort_key + "|" + str(self.sort_reverse)
        for value in self.fltr.values():
            string += "|" + str(value)
        return string

    def string_to_state(self, text):
        values = text.split("|")
        if len(values) < 2:
            return

        self.sort_key = values.pop(0)
        self.sort_reverse = values.pop(0) == "True"
        for entrytype in entrytype_dict:
            if values:
                value = values.pop(0)
            else:
                value = "True"
            self.fltr[entrytype] = value == "True"

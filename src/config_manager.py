# config_manager.py
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

from gi.repository import Gio, GLib

from enum import Enum

from .default_layouts import default_layout_strings


setting = Gio.Settings.new("com.github.rogercrocker.badabib")


entrytype_dict = {
    "article": "Article",
    "book": "Book",
    "booklet": "Booklet",
    "conference": "Conference",
    "inbook": "In Book",
    "incollection": "In Collection",
    "inproceedings": "In Proceedings",
    "manual": "Manual",
    "masterthesis": "Master Thesis",
    "misc": "Misc.",
    "online": "Online",
    "phdthesis": "Ph.D. Thesis",
    "proceedings": "Proceedings",
    "techreport": "Tech Report",
    "unpublished": "Unpublished",
}


field_dict = {
    "ENTRYTYPE": "Entry Type",
    "ID": "BibTeX Key",
    "author": "Author",
    "editor": "Editor",
    "title": "Title",
    "journal": "Journal",
    "booktitle": "Book Title",
    "chapter": "Chapter",
    "volume": "Volume",
    "number": "Number",
    "series": "Series",
    "edition": "Edition",
    "type": "Type",
    "pages": "Pages",
    "year": "Year",
    "month": "Month",
    "publisher": "Publisher",
    "organization": "Organization",
    "institution": "Institution",
    "school": "School",
    "address": "Address",
    "doi": "DOI",
    "url": "URL",
    "file": "File",
    "email": "Email",
    "note": "Note",
    "annote": "Annotation",
    "keywords": "Keywords",
    "howpublished": "How published",
    "crossref": "Cross-Reference",
    "abstract": "Abstract",
}


month_dict = {
    "jan": "January",
    "feb": "February",
    "mar": "March",
    "apr": "April",
    "may": "May",
    "jun": "June",
    "jul": "July",
    "aug": "August",
    "sep": "September",
    "oct": "October",
    "nov": "November",
    "dec": "December",
}


sort_fields = ["ID", "author", "title", "journal", "year"]
link_fields = ["doi", "url", "eprint", "file"]


class StringStatus(Enum):
    none = 0
    defined = 1
    undefined = 2


class SourceViewStatus(Enum):
    empty = 0
    valid = 1
    invalid = 2
    modified = 3


def get_align_fields():
    return setting.get_boolean("align-fields")


def set_align_fields(state):
    setting.set_boolean("align-fields", state)


def get_field_indent():
    return setting.get_int("field-indent")


def set_field_indent(n):
    setting.set_int("field-indent", n)


def get_homogenize_fields():
    return setting.get_boolean("homogenize-fields")


def get_homogenize_latex():
    return setting.get_boolean("homogenize-latex-encoding")


def get_parse_on_fly():
    return setting.get_boolean("parse-on-fly")


def set_parse_on_fly(state):
    setting.set_boolean("parse-on-fly", state)


def get_create_backup():
    return setting.get_boolean("create-backup")


def set_create_backup(state):
    setting.set_boolean("create-backup", state)


def get_window_geom():
    return setting.get_value("window-geom")


def set_window_geom(lis):
    g_variant = GLib.Variant("ai", lis)
    setting.set_value("window-geom", g_variant)


def get_undo_delay():
    return setting.get_double("undo-delay")


def set_undo_delay(d):
    setting.set_double("undo-delay", d)


def get_row_indent():
    return setting.get_int("row-indent")


def set_row_indent(indent):
    setting.set_int("row-indent", indent)


def get_watcher_sleep_time():
    return setting.get_int("watcher-sleep-time")


def set_watcher_sleep_time(T):
    setting.set_int("watcher-sleep-time", T)


def get_default_entrytype():
    return setting.get_string("default-entrytype")


def set_default_entrytype(entrytype):
    setting.set_string("default-entrytype", entrytype)


def get_new_file_name():
    return setting.get_string("new-file-name")


def set_new_file_name(name):
    setting.set_string("new-file-name", name)


def get_open_files():
    files = setting.get_value("open-files")
    states = setting.get_value("open-file-states")
    return dict(zip(files, states))


def set_open_files(open_files):
    g_variant_files = GLib.Variant("as", list(open_files.keys()))
    g_variant_states = GLib.Variant("as", list(open_files.values()))
    setting.set_value("open-files", g_variant_files)
    setting.set_value("open-file-states", g_variant_states)


def get_open_tab():
    return setting.get_string("open-tab")


def set_open_tab(filename):
    setting.set_string("open-tab", filename)


def get_num_recent():
    return setting.get_int("num-recent")


def set_num_recent(n):
    setting.set_int("num-recent", n)


def get_recent_files():
    files = setting.get_value("recent-files")
    states = setting.get_value("recent-file-states")
    return dict(zip(files, states))


def set_recent_files(recent_files):
    g_variant_files = GLib.Variant("as", list(recent_files.keys()))
    g_variant_states = GLib.Variant("as", list(recent_files.values()))
    setting.set_value("recent-files", g_variant_files)
    setting.set_value("recent-file-states", g_variant_states)


def add_to_recent(badabib_file):
    recent_files = get_recent_files()
    if badabib_file.name in recent_files:
        recent_files.pop(badabib_file.name)
    recent_files[badabib_file.name] = badabib_file.itemlist.state_to_string()

    if len(recent_files) > get_num_recent():
        first_file = list(recent_files.keys())[0]
        recent_files.pop(first_file)

    set_recent_files(recent_files)


def remove_from_recent(filename):
    recent_files = get_recent_files()
    if filename in recent_files:
        recent_files.pop(filename)
    set_recent_files(recent_files)


def get_editor_layout(entrytype):
    if entrytype not in entrytype_dict:
        return default_layout_strings[get_default_entrytype()]

    layouts = setting.get_value("editor-layouts")
    if layouts:
        idx = list(entrytype_dict.keys()).index(entrytype)
        if layouts[idx]:
            return layouts[idx]

    return default_layout_strings[entrytype]


def set_editor_layout(entrytype, layout):
    layouts = list(setting.get_value("editor-layouts"))
    if len(layouts) != len(entrytype_dict):
        layouts = len(entrytype_dict) * [""]

    if entrytype in entrytype_dict:
        idx = list(entrytype_dict.keys()).index(entrytype)
        if layout == default_layout_strings[entrytype]:
            layouts[idx] = ""
        else:
            layouts[idx] = layout
        g_variant = GLib.Variant("as", layouts)
        setting.set_value("editor-layouts", g_variant)

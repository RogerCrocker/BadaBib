# bibfile.py
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


from os.path import split

from unicodedata import normalize

from .customization import convert_to_unicode

from .config_manager import entrytype_dict
from .config_manager import get_default_editor

from .bibitem import BadaBibItem


UPPERCASE_A_ASCII = 65
LOWERCASE_A_ASCII = 97

DEFAULT_EDITOR = get_default_editor()


class BadaBibFile:
    def __init__(self, store, name, database, created=False):
        self.store = store
        self.name = name
        self.short_name = None
        self.head, self.tail = split(name)
        self.database = database
        self.local_strings = {}
        self.writer = store.get_default_writer()
        self.items = []
        self.itemlist = None
        self.created = created

        self.read_database()

    def read_database(self):
        """
        Convert entries of a database to BadaBibItems. This function should only
        be called once on initialization
        """
        self.local_strings = self.database.strings
        for idx in range(len(self.database.entries)):
            self.items.append(BadaBibItem(self, idx))


    def append_item(self, bibtex=None):
        idx = len(self.database.entries)
        if bibtex:
            self.database.entries.append(bibtex)
        else:
            self.database.entries.append({"ID": "", "ENTRYTYPE": DEFAULT_EDITOR})
        item = BadaBibItem(self, idx)
        self.items.append(item)
        return item

    def update_filename(self, name):
        self.name = name
        self.head, self.tail = split(name)

    def has_empty_keys(self):
        for entry in self.database.entries:
            if not entry["ID"]:
                return True
        return False

    def get_duplicate_keys(self):
        keys = [item.entry["ID"] for item in self.items if not item.deleted]
        duplicates = [key for key in set(keys) if keys.count(key) > 1]
        return duplicates

    def key_is_unique(self, key):
        keys = [item.entry["ID"] for item in self.items if not item.deleted]
        return keys.count(key) == 0

    def generate_key_for_item(self, item):
        # get last name of first author, covert to ascii, and capitalize
        # if the paper has exactly two authors, get both last names
        last_names = item.last_name_list()
        if "author" in item.entry and last_names:
            utf_name = convert_to_unicode(last_names[0])
            ascii_name = normalize("NFKD", utf_name).encode("ascii", "ignore").decode("utf-8")
            key = ascii_name[:1].upper() + ascii_name[1:]
            if len(last_names) == 2:
                utf_name = convert_to_unicode(last_names[1])
                ascii_name = normalize("NFKD", utf_name).encode("ascii", "ignore").decode("utf-8")
                key += ascii_name[:1].upper() + ascii_name[1:]
        else:
        	# use entrytpye as key otherwise
            key = item.entry["ENTRYTYPE"]

        # add year
        if "year" in item.entry:
            key += str(item.raw_field("year"))

        # if necessary, add suffix to avoid duplicates
        if key and key != item.entry["ID"]:
            if key[-1].islower():
                suffix_code = UPPERCASE_A_ASCII
            else:
                suffix_code = LOWERCASE_A_ASCII

            has_suffix = False
            while not self.key_is_unique(key):
                if has_suffix:
                    key = key[:-1]
                else:
                    has_suffix = True
                key += chr(suffix_code)
                suffix_code += 1

        return key

    @staticmethod
    def get_sort_key_func(field):
        """Get function that returns the sort key for a given field"""
        def sort_key_func(item):
            return item.sort_values[field]
        return sort_key_func

    def parse_entry(self, bibtex):
        """Parse a single bibtex entry"""
        parser = self.store.get_default_parser()
        writer = self.store.get_default_writer()

        # add strings to bibtex entry and try to parse it
        strings_and_bibtex = writer._strings_to_bibtex(self.database) + bibtex
        try:
            test_database = parser.parse(strings_and_bibtex)
        except Exception:
            return None

        # we expect a database with a single entry
        if test_database and len(test_database.entries) == 1:
            return test_database.entries.pop(-1)
        else:
            return None

    def strings_to_text(self):
        # only write local strings to the file
        all_strings = self.database.strings
        self.database.strings = self.local_strings

        text = self.writer._strings_to_bibtex(self.database)
        text = text.replace("\n\n", "\n")

        # restore global strings
        self.database.strings = all_strings

        return text

    def entries_to_text(self):
        text = ""
        sort_key_func = self.get_sort_key_func(self.itemlist.sort_key)
        self.items.sort(reverse=self.itemlist.sort_reverse, key=sort_key_func)
        for item in self.items:
            if not item.deleted:
                if self.writer.align_values:
                    self.writer._max_field_width = item.max_field_width
                text += self.writer._entry_to_bibtex(item.entry)

        return text

    def to_text(self):
        strings = self.strings_to_text()
        if strings:
            return strings + "\n\n" + self.entries_to_text()
        else:
            return self.entries_to_text()


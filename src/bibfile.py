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

from .config_manager import get_default_entrytype

from .bibitem import BadaBibItem


# 'a' and 'A' to create unique keys by iterating over ASCII characters
UPPERCASE_A_ASCII = 65
LOWERCASE_A_ASCII = 97

# Editor shown when no entry is selected
DEFAULT_EDITOR = get_default_entrytype()


class BadaBibFile:
    """
    Representation of a .bib file and its entries. BadaBibFiles wrap around a
    bibtexparser database and are managed by a BadaBibStore.
    """

    def __init__(self, store, name, database, created=False):
        """
        Initilize BadaBibFile.

        Parameters
        ----------
        store: BadaBibStore
            Store managing this file
        name: str
            Full path of the .bib file
        database: BibDatabase
            bibtexparser database
        created: bool, optional
            Was this file created by BadaBib!? The default value is 'False'.
        """
        self.store = store                          # Store managing this file
        self.name = name                            # Full path
        self.short_name = None                      # Shortest unique name
        self.base_name = split(name)[1]             # File name, not necesarily unique
        self.database = database                    # bibtexparser database with entries
        self.local_strings = {}                     # Strings defined in the .bib file
        self.writer = store.get_default_writer()    # bibtexparser writer
        self.items = []                             # list of bib items
        self.itemlist = None                        # itemlist showing entries of this file
        self.unsaved = False                        # File contains unsaved changes
        self.created = created                      # File was created by Bada Bib!
        self.backup_on_save = True                  # Backup file when saving

        # Read database to create items from entries
        self.read_database()

    def unref(self):
        """Delete BadaBibFile to free memory."""
        for item in self.items:
            item.unref()
        self.itemlist.unref()
        self.writer = None
        self.database = None
        self.local_strings = None
        self.itemlist = None

    def read_database(self):
        """
        Convert entries of a database to BadaBibItems. This function should only
        be called once on initialization
        """
        self.local_strings = self.database.strings
        for idx in range(len(self.database.entries)):
            self.items.append(BadaBibItem(self, idx))

    def append_item(self, entry=None):
        """
        Convert bibtexparser entry to Bada Bib! item and append it to this file.

        Parameters
        ----------
        entry: dict, optional
            Entry as parsed by bibtexparser. If None, a new empty entry is
            created. The default value is None.

        Returns
        -------
        item: BadaBibItem
            Item created from entry
        """
        # Append entry to database
        idx = len(self.database.entries)
        if entry:
            self.database.entries.append(entry)
        else:
            self.database.entries.append({"ID": "", "ENTRYTYPE": DEFAULT_EDITOR})
        # Create item from entry and append to list
        item = BadaBibItem(self, idx)
        self.items.append(item)
        return item

    def count(self, entrytype):
        """
        Count number of non-deleted entries of given type.

        Parameters
        ----------
        entrytype: str
            Entry type of interest

        Returns
        -------
        int
            Number of non-deleted items of given type
        """
        return sum(item.entry["ENTRYTYPE"] == entrytype for item in self.items if not item.deleted)

    def count_all(self):
        """
        Count all non-deleted items of this file

        Returns
        -------
        int
            Number of non-deleted items
        """
        return sum(not item.deleted for item in self.items)

    def is_empty(self):
        """
        Check if file is empty, that is, it does not contain any items or
        strings.

        Returns
        -------
        bool
            True if file is empty, False otherwise
        """
        n_items = self.count_all()
        n_strings = len(self.local_strings)
        return n_items == n_strings == 0

    def update_filename(self, name):
        """
        Update the name of this file, for example, if it saved under a different
        name or location.

        Parameters
        ----------
        name: str
            New file name
        """
        self.name = name
        self.base_name = split(name)[1]
        # Propagate name change to itemlist
        if self.itemlist:
            self.itemlist.update_filename()

    def set_unsaved(self, unsaved):
        """
        Declare file saved/unsaved

        Parameters
        ----------
        unsaved: bool
            New state of the file
        """
        # Propagate state change to itemlist
        if self.itemlist:
            self.itemlist.set_unsaved(unsaved)
        self.unsaved = unsaved

    def has_empty_keys(self):
        """Check if file contains non-deleted entries without keys"""
        return any(not item.entry["ID"] and not item.deleted for item in self.items)

    def get_duplicate_keys(self):
        """
        Get all non-unique entry keys.

        Returns
        -------
        duplicates: list of str
            List of duplicate keys
        """
        keys = [item.entry["ID"] for item in self.items if not item.deleted]
        duplicates = [key for key in set(keys) if keys.count(key) > 1]
        return duplicates

    def key_is_unique(self, key):
        """
        Check if a given key is unqiue among the non-deleted entires.

        Parameters
        ----------
        key: str
            Key in question

        Returns
        -------
        bool
            True if key is unique
        """
        keys = [item.entry["ID"] for item in self.items if not item.deleted]
        return keys.count(key) == 0

    def generate_key_for_item(self, item):
        """
        Generate a unique key for a given item.

        Parameters
        ----------
        item: BadaBibItem
            Item in question

        Returns
        -------
        key: str
            Unique entry key
        """
        # Get last name of first author, covert to ascii, and capitalize.
        # If the paper has exactly two authors, get both last names
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
        """
        Wrap sort key of item in a function so that it can be passed to the
        list.sort() method.

        Parameters
        ----------
        fields: str
            Field of interest

        Returns
        -------
        sort_key_func: function
            sort key function
        """
        def sort_key_func(item):
            return item.sort_values[field]
        print(type(sort_key_func))
        return sort_key_func

    def parse_entry(self, bibtex):
        """
        Parse a single bibtex entry with default parser.

        Parameters
        ----------
        bibtex: str
            Raw BibTeX entry

        Returns
        -------
        dict or None
            bibparser database entry or None, if bibtex parameter is invalid
        """
        parser = self.store.get_default_parser()
        writer = self.store.get_default_writer()

        # add strings to bibtex entry and try to parse it
        strings_and_bibtex = writer._strings_to_bibtex(self.database) + bibtex
        try:
            test_database = parser.parse(strings_and_bibtex)
        except UnicodeDecodeError:
            return None

        # we expect a database with a single entry
        if test_database and len(test_database.entries) == 1:
            return test_database.entries.pop(-1)
        return None

    def comments_to_text(self):
        """
        Write all comments in this file to a string.

        Returns
        -------
        text: str
            String of comments
        """
        text = self.writer._comments_to_bibtex  (self.database)
        text = text.replace("\n\n", "\n")   # Use single line break between comments
        return text

    def strings_to_text(self):
        """
        Write all string/macro definitions to a string.

        Returns
        -------
        text: str
            String of all macros
        """
        # only write local strings to the file
        all_strings = self.database.strings
        self.database.strings = self.local_strings

        text = self.writer._strings_to_bibtex(self.database)
        text = text.replace("\n\n", "\n")   # Use single line break between strings

        # restore global strings
        self.database.strings = all_strings

        return text

    def entries_to_text(self):
        """
        Write all entries to a string, sort by current order of the itemlist.

        Returns
        -------
        text: str
            String of all entries
        """
        text = ""

        # Sort by order of itemlist
        sort_key_func = self.get_sort_key_func(self.itemlist.sort_key)
        self.items.sort(reverse=self.itemlist.sort_reverse, key=sort_key_func)

        for item in self.items:
            # Only write non-deleted items
            if not item.deleted:
                # If setting is active, align along '=' sign
                if self.writer.align_values:
                    self.writer._max_field_width = item.max_field_width
                text += self.writer._entry_to_bibtex(item.entry)

        return text

    def to_text(self):
        """
        Write comments, macros and entries to string. Sections are separated
        by two line breaks.

        Returns
        -------
        text: str
            String with BibTeX file content
        """
        comments = self.comments_to_text()
        strings = self.strings_to_text()
        text = ""
        if comments:
            text += comments + "\n\n"
        if strings:
            text += strings + "\n\n"
        return text + self.entries_to_text()

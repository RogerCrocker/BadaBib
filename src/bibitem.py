# bibitem.py
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


from bibtexparser.latexenc import latex_to_unicode

from bibtexparser.bibdatabase import BibDataString
from bibtexparser.bibdatabase import BibDataStringExpression
from bibtexparser.bibdatabase import UndefinedString

from bibtexparser.customization import getnames
from bibtexparser.customization import splitname
from bibtexparser.customization import InvalidName

from .customization import prettify_unicode_field

from .config_manager import StringStatus
from .config_manager import sort_fields


MAX_CHAR = chr(0x10FFFF)
MIN_CHAR = chr(0)


def expand(value):
    """Expand expression to string"""
    try:
        expanded = BibDataStringExpression.expand_if_expression(value)
    except UndefinedString:
        expanded = expression_to_string(value)
    return expanded


def contains_bibstring(string, bibstrings):
    if not string:
        return False

    for word in string.split(" "):
        if word.lower() in bibstrings:
            return True
    return False


def string_to_expression(string, database):
    words = string.split(" ")
    expr_list = []
    substring = ""

    # iterate over all words in string
    for word in words:
        # catch strings
        if word.lower() in database.strings:
            # if it exists, add current substring to expression list
            if len(substring) > 0:
                expr_list.append(substring)
            # add space if previous expression is a BibDataString
            if expr_list and isinstance(expr_list[-1], BibDataString):
                expr_list.append(" ")
            # add BibDataString to expression list and initialize new substring
            expr_list.append(BibDataString(database, word))
            substring = " "
        else:
            # otherwise add the word to the current substring
            substring += word + " "

    if len(substring) > 1:
        expr_list.append(substring[:-1])

    return BibDataStringExpression(expr_list)


def expression_to_string(expression):
    value = ""
    for string in expression.expr:
        if isinstance(string, BibDataString):
            # capitalize strings
            value += string.name.upper()
        else:
            value += string
    return value


def entries_equal(entry1, entry2):
    if set(entry1.keys()) != set(entry2.keys()):
        return False

    for field in entry1:
        is_expr1 = isinstance(entry1[field], BibDataStringExpression)
        is_expr2 = isinstance(entry2[field], BibDataStringExpression)

        if is_expr1 != is_expr2:
            return False
        elif is_expr1:
            value1 = expression_to_string(entry1[field])
            value2 = expression_to_string(entry2[field])
            if value1 != value2:
                return False
        else:
            if entry1[field] != entry2[field]:
                return False

    return True


class BadaBibItem(object):
    def __init__(self, bibfile, idx, state=None):
        self.bibfile = bibfile
        self.idx = idx
        self.row = None
        self.sort_values = {}
        self.bibtex = ""
        self.unsaved = False
        self.deleted = False

        self.update_all_sort_values()

    @property
    def entry(self):
        return self.bibfile.database.entries[self.idx]

    @property
    def max_field_width(self):
        return max([len(field) for field in self.entry if field != "ENTRYTYPE"])

    def raw_field(self, field):
        if field in self.entry:
            if isinstance(self.entry[field], BibDataStringExpression):
                return expression_to_string(self.entry[field])
            else:
                return self.entry[field]
        else:
            return None

    def pretty_field(self, field):
        if field in self.entry:
            value = expand(self.entry[field])
            value = latex_to_unicode(value)
            value = prettify_unicode_field(field, value)
            return value
        else:
            return None

    def bibstring_status(self, field):
        defined = contains_bibstring(self.raw_field(field), self.bibfile.database.strings)
        if defined:
            return StringStatus.defined
        elif field in self.entry and isinstance(self.entry[field], BibDataStringExpression):
            return StringStatus.undefined
        else:
            return StringStatus.none

    def last_name_list(self):
        if "author" not in self.entry:
            return []

        value = expand(self.entry["author"])
        value = latex_to_unicode(value)
        value = prettify_unicode_field("author", value)
        if not value:
            return []

        clean_value = value.replace("\n", " ").replace("\\", "")
        name_list = [name.strip() for name in clean_value.split(" and ")]
        names = getnames(name_list)

        last_name_list = []
        for name in names:
            try:
                name_parts = splitname(name)["last"]
                name_str = ""
                for part in name_parts:
                    name_str += part
                last_name_list.append(name_str)
            except InvalidName:
                pass

        return last_name_list

    def lowercase_last_names(self):
        last_name_list = self.last_name_list()
        last_name_str = ""
        for last_name in last_name_list:
            for part in last_name:
                last_name_str += part.lower()

        return last_name_str

    def update_field(self, field, value, update_bibtex=True):
        if field == "ID":
            self.entry[field] = value
        elif value:
            if isinstance(value, str) and contains_bibstring(value, self.bibfile.database.strings):
                self.entry[field] = string_to_expression(value, self.bibfile.database)
            else:
                self.entry[field] = value
        elif field in self.entry:
            self.entry.pop(field)

        if field in sort_fields:
            self.update_sort_value(field)

        if update_bibtex:
            self.update_bibtex()

    def refresh(self):
        entry = self.entry.copy()
        for field, value in entry.items():
            self.update_field(field, value, update_bibtex=False)

    def update_entry(self, entry, update_bibtex=False):
        self.bibfile.database.entries[self.idx] = entry
        self.update_all_sort_values()
        if update_bibtex:
            self.update_bibtex()

    def update_bibtex(self):
        writer = self.bibfile.writer
        if writer.align_values:
            writer._max_field_width = self.max_field_width
        self.bibtex = writer._entry_to_bibtex(self.entry)

    def update_sort_value(self, field):
        if field == "author":
            # sort by lower case last naems
            if "author" in self.entry:
                self.sort_values["author"] = self.lowercase_last_names()
            else:
                self.sort_values["author"] = None

        elif field == "journal":
            # if "journal" is not defiend, try "booktitle"
            if "journal" in self.entry:
                _field = "journal"
            elif "booktitle" in self.entry:
                _field = "booktitle"
            else:
                _field = None

            if _field:
                value = expand(self.entry[_field])
                value = latex_to_unicode(value)
                value = prettify_unicode_field(_field, value).lower()
                self.sort_values["journal"] = value
            else:
                self.sort_values["journal"] = None

        elif field in self.entry:
            value = expand(self.entry[field])
            value = latex_to_unicode(value)
            value = prettify_unicode_field(field, value).lower()
            self.sort_values[field] = value

        else:
            self.sort_values[field] = None

    def update_all_sort_values(self):
        for field in sort_fields:
            self.update_sort_value(field)

    def sort_value(self, field):
        # sort entries without ID to the top
        if not self.entry["ID"]:
            if self.bibfile.itemlist.sort_reverse:
                return MAX_CHAR
            else:
                return MIN_CHAR

        if self.sort_values[field]:
            return self.sort_values[field]
        else:
            # sort entries without "field" to the bottom
            if self.bibfile.sort_reverse:
                return MIN_CHAR
            else:
                return MAX_CHAR

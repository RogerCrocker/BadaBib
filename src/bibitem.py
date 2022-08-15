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

from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bibdatabase import BibDataString
from bibtexparser.bibdatabase import BibDataStringExpression
from bibtexparser.bibdatabase import UndefinedString

from bibtexparser.customization import getnames
from bibtexparser.customization import splitname
from bibtexparser.customization import InvalidName

from .customization import prettify_unicode_field

from .config_manager import month_dict
from .config_manager import sort_fields


# bibtexparser database containing dict with month macros
month_database = BibDatabase()
month_database.strings = month_dict

# maximum char to sort entries to the end of a list
MAX_CHAR = chr(0x10FFFF)


def expand_pretty(expression):
    """
    Expand bibtexparser expression to plain text. Intended to show pretty
    fields in the itemlist.

    Parameters
    ----------
    expression: str or BibDataStringExpression

    Returns
    -------
    text: str
        Text obtained by expanding the expression
    """
    try:
        text = BibDataStringExpression.expand_if_expression(expression)
    except UndefinedString:
        # If expression contains undefined strings, fall back to raw expansion
        text = expand_raw(expression)
    return text


def expand_raw(expression):
    """
    Expand bibtexparser expression, but do not expand strings. Instead, mark
    them by capitalizing the string name in the text. Intended to show raw
    fields in the editor.

    Parameters
    ----------
    expression: str or BibDataStringExpression

    Returns
    -------
    text: str
        Text obtained by expanding the expression
    """
    text = ""
    for expr in expression.expr:
        if isinstance(expr, BibDataString):
            text += expr.name.upper()
        else:
            text += expr
    return text


def get_n_strings_expr(expression):
    """
    Get number of strings contained in expression. Does count undefined
    strings!

    Parameters
    ----------
    expression: str or BibDataStringExpression

    Returns
    -------
    int
    """
    if not isinstance(expression, BibDataStringExpression):
        return 0
    return sum(isinstance(expr, BibDataString) for expr in expression.expr)


def get_n_strings_text(text, bibstrings):
    """
    Get number of strings contained in raw text. Strings are defined in dict
    passed as second parameter.

    Parameters
    ----------
    text: str
    bibstrings: dict

    Returns
    -------
    int
    """
    if not text:
        return 0
    return sum(word.lower() in bibstrings for word in text.split(" "))


def text_to_expression(text, database):
    """
    Convert raw text input to a bibtexparser expression.

    Parameters
    ----------
    text: str
    database: BibDatabase
        databse containing string definitions

    Returns
    -------
    BibDataStringExpression
    """
    words = text.split(" ")     # split text argument
    expr_list = []              # initialize list of expressions
    text_sequence = ""          # sequence of words

    # iterate over all words in text
    for word in words:
        # catch strings
        if word.lower() in database.strings:
            # if it exists, add current text sequence to expression list
            if len(text_sequence) > 0:
                expr_list.append(text_sequence)
            # add space if previous expression is a BibDataString
            if expr_list and isinstance(expr_list[-1], BibDataString):
                expr_list.append(" ")
            # add BibDataString to expression list and initialize new text sequence
            expr_list.append(BibDataString(database, word))
            text_sequence = " "
        else:
            # otherwise add the word to the current text sequence
            text_sequence += word + " "

    # Append text sequence, if it is non-empty
    if len(text_sequence) > 1:
        expr_list.append(text_sequence[:-1])

    return BibDataStringExpression(expr_list)


def entries_equal(entry1, entry2):
    """
    Check if two entries are identical. Strings are expanded for this
    comparison.

    Parameters
    ----------
    entry1, entry2: dict

    Returns
    -------
    bool
        True if equal
    """
    # Check if entries contain the same fields
    if set(entry1.keys()) != set(entry2.keys()):
        return False

    # Compare field text
    for field in entry1:
        if expand_pretty(entry1[field]) != expand_pretty(entry2[field]):
            return False
    return True


class BadaBibItem:
    """
    Representation of a BibTeX entry. BadaBibItems wrap around a
    bibtexparser entry and are managed by a BadaBibFile.
    """
    def __init__(self, bibfile, idx):
        """
        Initilize BadaBibItem.

        Parameters
        ----------
        bibfile: BadaBibFile
            File this entry belongs to
        idx: int
            Index of this entry in the database of the bibfile
        """
        self.bibfile = bibfile
        self.idx = idx
        self.row = None             # Row of itemlist containing this entry
        self.sort_values = {}       # Sort keys of this entry
        self.bibtex = None          # Raw BibTeX source
        self.deleted = False        # True if entry was deleted

        self.update_bibtex()            # Generate source
        self.update_all_sort_values()   # Generate sort keys

    @property
    def entry(self):
        """Shortcut to entry in database"""
        return self.bibfile.database.entries[self.idx]

    @property
    def max_field_width(self):
        """Length of longest field name except entry type"""
        return max([len(field) for field in self.entry if field != "ENTRYTYPE"])

    def unref(self):
        """Delete references to file and widgets to force-free memory"""
        self.bibfile = None
        self.row = None
        self.sort_values = None
        self.bibtex = None

    def pretty_field(self, field):
        """
        Get pretty text in given field.

        Parameters
        ----------
        field: str

        Returns
        -------
        str
        """
        # Check if field exists in this entry
        if field not in self.entry:
            return None

        value = expand_pretty(self.entry[field])        # Expand strings
        value = latex_to_unicode(value)                 # Convert to unicode
        value = prettify_unicode_field(field, value)    # Prettify
        return value

    def raw_field(self, field):
        """
        Get raw text in given field.

        Parameters
        ----------
        field: str

        Returns
        -------
        str
        """
        # Check if field exists in this entry
        if field not in self.entry:
            return None

        # Mark strings if necessary, return raw text otherwise
        if isinstance(self.entry[field], BibDataStringExpression):
            return expand_raw(self.entry[field])
        return self.entry[field]

    def bibstring_status(self, field):
        """
        Check if field contains strings, undefined strings, or no strings.

        Parameters
        ----------
        field: str

        Returns
        -------
        str or None
            Either "defined", "undefined" or None
        """
        # Check if field exists in this entry
        if field not in self.entry:
            return None

        # Check if field contains strings, and if the number of defined strings
        # equals the number of all strings
        n_strings_expr = get_n_strings_expr(self.entry[field])
        n_strings_text = get_n_strings_text(self.raw_field(field), self.bibfile.database.strings)
        if n_strings_expr > 0:
            if n_strings_expr == n_strings_text:
                return "defined"
            return "undefined"
        return None

    def last_name_list(self):
        """
        Get list of last names for key generation.

        Returns
        -------
        last_name_list: list of str
        """
        # Check that author field exists
        if "author" not in self.entry:
            return []

        # Expand and prittify author field
        value = expand_pretty(self.entry["author"])
        value = latex_to_unicode(value)
        value = prettify_unicode_field("author", value)
        if not value:
            return []

        # remove line breaks and split names along "and"
        clean_value = value.replace("\n", " ").replace("\\", "")
        name_list = [name.strip() for name in clean_value.split(" and ")]
        names = getnames(name_list)

        # Extract last names, ignore if no last name is defined
        last_name_list = []
        for name in names:
            try:
                name_parts = splitname(name)["last"]
                name_str = " ".join(name_parts)
                last_name_list.append(name_str)
            except InvalidName:
                pass

        return last_name_list

    def lowercase_last_names(self):
        """
        String all lower case last name together. This is used as a sort key
        when ordering the itenlist.

        Returns
        -------
        last_name_str: str
        """
        last_name_list = self.last_name_list()
        last_name_str = ""
        for last_name in last_name_list:
            for part in last_name:
                last_name_str += part.lower().strip(" ()[]{}")
        return last_name_str

    def update_field(self, field, value, update_bibtex=True):
        """
        Update text or expression in a field to a new value

        Parameters
        ----------
        field: str
        value: str or BibDataStringExpression
        update_bibtex: bool
            If True, regenerate the raw BibTeX source
        """
        # Case: BibTeX key is changed
        if field == "ID":
            # BibTeX key field is not allowed to contain strings
            self.entry[field] = value
        # Case: Any other field but BibTeX key is changed
        elif value:
            # Pick database with strings
            if field == "month":
                database = month_database
            else:
                database = self.bibfile.database

            # Check if value is a text that contains strings. If so, convert
            # to expression. Otherwise use raw value.
            if isinstance(value, str) and get_n_strings_text(value, database.strings):
                self.entry[field] = text_to_expression(value, database)
            else:
                self.entry[field] = value
        # Case: Value is empty -> remove field from entry
        elif field in self.entry:
            self.entry.pop(field)

        # Update sort key, if sort field was changed
        if field in sort_fields:
            self.update_sort_value(field)

        # Update BibTeX source
        if update_bibtex:
            self.update_bibtex()

    def refresh(self):
        """Re-read all fields of entry. Useful if strings are defined or deleted."""
        entry = self.entry.copy()
        for field, value in entry.items():
            self.update_field(field, value, update_bibtex=False)

    def update_entry(self, entry, update_bibtex=False):
        """
        Overwrite this entry with a new one. This function is called when a
        user modifies the source directly, not via the editor.

        Parameters
        ----------
        entry: dict
            New entry that  replaces the current one
        update_bibtex: bool
            If True, update BibTeX source. This is typically not required since
            the user directly modified the source already.
        """
        self.bibfile.database.entries[self.idx] = entry
        self.update_all_sort_values()
        if update_bibtex:
            self.update_bibtex()

    def update_bibtex(self):
        """Regenerate BibTeX source for entry."""
        writer = self.bibfile.writer
        # Align fields along '=' if setting is active
        if writer.align_values:
            writer._max_field_width = self.max_field_width
        self.bibtex = writer._entry_to_bibtex(self.entry)

    def update_sort_value(self, field):
        """
        Regenerate the sort key for a given field.

        Parameters
        ----------
        field: str
        """
        if field == "author":
            # Sort by lower case last names
            if "author" in self.entry:
                self.sort_values["author"] = self.lowercase_last_names()
            else:
                # Sort to end of list if auther is not defined
                self.sort_values["author"] = MAX_CHAR
        else:
            # If "journal" is not defiend, try "booktitle"
            if field == "journal" and "journal" not in self.entry:
                _field_ = "booktitle"
            # If "year" is not defined, try "date"
            elif field == "year" and "year" not in self.entry:
                _field_ = "date"
            else:
                _field_ = field

            if _field_ in self.entry:
                # If field exists, sort by lower case pretty value
                value = expand_pretty(self.entry[_field_])
                value = latex_to_unicode(value)
                value = prettify_unicode_field(_field_, value).lower()
                self.sort_values[field] = value
            else:
                # Sort to end of list otherwise
                self.sort_values[field] = MAX_CHAR

        # Catch existing but empty fields
        if not self.sort_values[field]:
            self.sort_values[field] = MAX_CHAR

    def update_all_sort_values(self):
        """Update sort key for all fields in itemlist sort menu."""
        for field in sort_fields:
            self.update_sort_value(field)

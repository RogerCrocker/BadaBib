# customizations.py
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
from bibtexparser.latexenc import string_to_latex

from bibtexparser.customization import getnames
from bibtexparser.customization import InvalidName

from .config_manager import get_title_case_n


# Dashes potentially used in page ranges
DASHES = ["-",      # minus
          "－",     # fullwidth minus
          "‐",      # hyphen
          "‑",      # non-breaking hyphen
          "–",      # En dash
          "—",      # Em dash
          "⸺",    # Two-Em dash
          "⸻",   # Three-Em dash
          "‒",      # Figure dash
          "―"]      # horizontal bar
# compare https://c.r74n.com/unicode/dashes and
# https://github.com/sciunto-org/python-bibtexparser/blob/master/bibtexparser/customization.py


def prettify_unicode_string(value):
    """
    Manually convert some LaTeX symbols to unicode.

    Parameters
    ----------
    value: str

    Returns
    -------
    str
    """
    return (
        value.replace("\n", " ")
        .replace("&", "&amp;")
        .replace("$", "")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("--", "–")
        .replace("---", "⸺")
    )


def prettify_unicode_names(value):
    """
    Reformat and standardize author names. This function is used to display
    names in the itemlist.

    Parameters
    ----------
    value: str

    Returns
    -------
    str
    """
    # Catch empty input string
    if not value:
        return ""

    # Use bibtexparser to extract names from input string
    name_list = [name.strip() for name in value.split(" and ")]
    try:
        names = getnames(name_list)

    # Leave string unchanged if it cannot be processed
    except InvalidName:
        return value

    # Remove trailing commas
    if names:
        pretty_names = [name.rstrip(" ,") for name in names]
        return " and ".join(pretty_names)
    return ""


def prettify_unicode_field(field, value):
    """
    Prettify a unicode string. Distinguishes between regular fields and fields
    containing names (currently only 'author' and 'editor').

    Parameters
    ----------
    field, value: str

    Returns
    -------
    str
    """
    if field in ("author", "editor"):
        return prettify_unicode_names(value)
    return prettify_unicode_string(value)


# Costumizations that can be applied to fields. All functions take parameters
# of the form (str, dict, int) and return a str.


def convert_to_unicode(string, bibstrings=None):
    """Convert LaTeX to pretty unicode."""
    unicode_string = latex_to_unicode(string)
    return prettify_unicode_string(unicode_string)


def convert_to_latex(string, bibstrings=None):
    """Prettify unicode and convert to LaTeX."""
    unicode_string = latex_to_unicode(string)
    pretty_string = prettify_unicode_string(unicode_string)
    return string_to_latex(pretty_string)


def title_case_word(word, bibstrings):
    """
    Capitalize word if it contains more than n characters. Do not capitalize LaTeX
    strings/macros.
    """
    # Check if word is too short or a LaTeX macro
    if word.lower() in bibstrings or len(word) < get_title_case_n():
        return word

    # Capitalize all parts of hyphenated words
    parts = word.split("-")
    Parts = []
    for part in parts:
        if part and part[0] != "{":
            Parts.append(part[0].upper() + part[1:].lower())
        else:
            Parts.append(part)
    return "-".join(Parts)


def upper_case_word(word, bibstrings):
    """Convert word to upper case unless it is a macro."""
    if word.lower() in bibstrings:
        return word
    return word.upper()


def lower_case_word(word, bibstrings):
    """Convert word to lower case unless it is a macro."""
    if word.lower() in bibstrings:
        return word
    return word.lower()


def title_case(value, bibstrings):
    """Convert field to title case, capitalize words longer than n characters."""
    if not value:
        return None
    words = value.split(" ")
    return " ".join(title_case_word(word, bibstrings) for word in words)


def upper_case(value, bibstrings):
    """Convert field to upper case."""
    if not value:
        return None
    words = value.split(" ")
    return " ".join(upper_case_word(word, bibstrings) for word in words)


def lower_case(value, bibstrings):
    """Convert field to lower case."""
    if not value:
        return None
    words = value.split(" ")
    return " ".join(lower_case_word(word, bibstrings) for word in words)


def protect_caps(string, bibstrings):
    """
    Protect upper case characters by putting them in brackets. Sequences of
    upper case characters are put in a single pair of brackets.
    """
    # Check for empty inputs
    if not string:
        return None

    protected = ""              # Text processes so far
    upper_case_sequence = ""    # Sequence of upper case chars
    pre_char = ""               # Character preceeding current one

    for char in string:
        # If char is upper case, add it to sequence
        if char.isupper():
            upper_case_sequence += char

        # If char is lower case
        else:
            # Check if a sequence just ended
            if upper_case_sequence:
                # Check if sequence is a macro or protected already. Do not alter
                # sequence in this case.
                if (
                    upper_case_sequence.lower() in bibstrings
                    or (pre_char == "{" and char == "}")
                ):
                    protected += upper_case_sequence
                # Otherwise, put it in brackets
                else:
                    protected += "{" + upper_case_sequence + "}"

                # And start new, empty sequence
                upper_case_sequence = ""

            # Char is lower case, does not need to be protected.
            protected += char

            # Remeber preceeding char
            pre_char = char

    # Catch string ending in a sequence of upper case chars
    if upper_case_sequence:
        if upper_case_sequence.lower() in bibstrings:
            protected += upper_case_sequence
        else:
            protected += "{" + upper_case_sequence + "}"
        upper_case_sequence = ""

    return protected


def sanitize_range(range_raw, bibstrings):
    """Replace all kinds of dashes in page ranges with "--"."""
    range_clean = range_raw
    for dash in DASHES:
        if dash in range_raw:
            # Remove spaces and dashes
            parts = [part.strip().strip(dash) for part in range_raw.split(dash)]
            # Remove empty strings
            parts = list(filter(None, parts))
            # Rejoin page ranges using correct dash
            range_clean = '--'.join(parts)
    return range_clean

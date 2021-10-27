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


SEPARATORS = ["-",      # minus
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
    if not value:
        return ""

    name_list = [name.strip() for name in value.split(" and ")]

    try:
        names = getnames(name_list)
    except InvalidName:
        return value

    if names:
        pretty_names = [name.rstrip(" ,") for name in names]
        return " and ".join(pretty_names)

    return ""


def prettify_unicode_field(field, value):
    if field == "author":
        return prettify_unicode_names(value)
    return prettify_unicode_string(value)


def convert_to_unicode(string, bibstrings=None, n=0):
    unicode_string = latex_to_unicode(string)
    return prettify_unicode_string(unicode_string)


def convert_to_latex(string, bibstrings=None, n=0):
    unicode_string = latex_to_unicode(string)
    pretty_string = prettify_unicode_string(unicode_string)
    return string_to_latex(pretty_string)


def capitalize_word(word, bibstrings, n=0):
    if word.lower() in bibstrings or len(word) < n:
        return word

    parts = word.split("-")
    Parts = []
    for part in parts:
        if part and part[0] != "{":
            Parts.append(part[0].upper() + part[1:])
        else:
            Parts.append(part)

    return "-".join(Parts)


def capitalize(value, bibstrings, n=0):
    if not value:
        return None
    words = value.split(" ")
    value_cap = capitalize_word(words[0], bibstrings, 0)
    for word in words[1:]:
        value_cap += " " + capitalize_word(word, bibstrings, n)

    return value_cap


def protect_word(word, bibstrings):
    if not word or word.lower() in bibstrings:
        return word

    protected = 0
    bracket_open = 0

    if word and word[0] == "{":
        word_out = "{"
        protected = 1
        bracket_open = 1
    elif word and word[0].isupper():
        word_out = "{"
        word_out += word[0]
        bracket_open = 1
    else:
        word_out = word[0]

    char = None
    for char in word[1:]:
        if protected:
            word_out += char
            if char == "}":
                protected -= 1
                bracket_open -= 1
        else:
            if char == "{":
                protected += 1
                bracket_open += 1
            elif bracket_open and char.islower():
                word_out += "}"
                bracket_open -= 1
            elif not bracket_open and char.isupper():
                word_out += "{"
                bracket_open += 1
            word_out += char

    if bracket_open and char != "}":
        word_out += "}"

    return word_out


def protect(string, bibstrings, n=0):
    if not string:
        return None
    protected = [protect_word(word, bibstrings) for word in string.split(" ")]
    return " ".join(protected)


def correct_hyphen(string, bibstrings, n=0):
    string_out = string
    for separator in SEPARATORS:
        if separator in string_out:
            parts = [part.strip().strip(separator) for part in string_out.split(separator)]
            parts = list(filter(None, parts))  # remove empty strings
            string_out = '--'.join(parts)
    return string_out

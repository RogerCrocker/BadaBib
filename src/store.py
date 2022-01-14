# store.py
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
from os.path import exists

from shutil import copyfile

from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import homogenize_latex_encoding

from .config_manager import get_homogenize_latex
from .config_manager import get_homogenize_fields
from .config_manager import get_align_fields
from .config_manager import get_field_indent
from .config_manager import get_new_file_name
from .config_manager import get_create_backup

from .bibfile import BadaBibFile


BACKUP_TAG = "% Bada Bib! Backup File"


def has_backup_tag(filename):
    try:
        with open(filename, 'r') as file:
            tag = file.read(len(BACKUP_TAG))
        return tag == BACKUP_TAG
    except Exception:
        return False


def backup_file(filename):
    backup = filename + ".bak"
    if exists(backup) and not has_backup_tag(backup):
        return False

    try:
        if has_backup_tag(filename):
            copyfile(filename, backup)
        else:
            with open(filename, 'r') as original:
                data = original.read()
            with open(backup, 'w') as modifed:
                modifed.write(BACKUP_TAG + "\n\n" + data)
    except Exception:
        return False

    return True


def get_shortest_unique_names(files):
    names = {}
    heads = {}
    tails = {}
    for file in files:
        head, tail = split(file)
        heads[file] = head
        tails[file] = tail

    for file in files:
        names[file] = tails[file]
        heads[file] = heads[file].split("/")

    while len(names.values()) != len(set(names.values())):
        for file in files:
            if len(heads[file]) > 0:
                names[file] = heads[file].pop() + "/" + names[file]

    return names


class BadaBibStore:
    def __init__(self):
        self.bibfiles = {}
        self.string_files = {}
        self.global_strings = {}

    @staticmethod
    def get_default_parser():
        parser = BibTexParser(interpolate_strings=False,
                              ignore_nonstandard_types=False)
        if get_homogenize_latex():
            parser.customization = homogenize_latex_encoding
        if get_homogenize_fields():
            parser.homogenize_fields = True
        return parser

    @staticmethod
    def get_default_writer():
        writer = BibTexWriter()
        writer.align_values = get_align_fields()
        writer.indent = get_field_indent() * " "
        return writer

    def add_file(self, name):
        # check if file is already open
        if name in self.bibfiles:
            return ["file_open"]

        try:
            # try parsing
            with open(name) as bibtex_file:
                parser = self.get_default_parser()
                try:
                    database = parser.parse_file(bibtex_file)
                except Exception:
                    return ["parsing_error"]

            # create backup, if desired
            backup = True
            if get_create_backup():
                if exists(name + ".bak"):
                    backup = backup_file(name + ".bak")
                backup = backup and backup_file(name)

            # remove backup tags, if present
            while BACKUP_TAG in database.comments:
                database.comments.remove(BACKUP_TAG)

            # initialize bibfile
            bibfile = BadaBibFile(self, name, database)
            self.bibfiles[name] = bibfile
            self.update_global_strings(bibfile)
            self.update_short_names()

            status = []
            if not backup:
                status.append("no_backup")
            if len(bibfile.database.entries) == 0:
                status.append("empty")

            return status

        except FileNotFoundError:
            return ["file_error"]

    def rename_file(self, old, new):
        file = self.bibfiles.pop(old)
        file.update_filename(new)
        self.bibfiles[new] = file
        self.update_short_names()

    def new_file(self):
        n = 1
        name = get_new_file_name()
        while name in self.bibfiles:
            name = get_new_file_name().replace(".bib", " ") + str(n) + ".bib"
            n += 1
        database = BibDatabase()
        bibfile = BadaBibFile(self, name, database, created=True)
        self.bibfiles[name] = bibfile
        self.update_short_names()

        return bibfile

    def save_file(self, filename):
        with open(filename, "w") as file:
            file.seek(0)
            file.write(self.bibfiles[filename].to_text())
            file.truncate()

    def remove_file(self, name):
        return self.bibfiles.pop(name)

    def get_state_strings(self):
        return [file.itemlist.state_to_string() for file in self.bibfiles.values()]

    def update_short_names(self):
        names = get_shortest_unique_names(self.bibfiles)
        for filename, file in self.bibfiles.items():
            file.short_name = names[filename]

    def import_strings(self, filename):
        if filename not in self.string_files:
            try:
                with open(filename) as string_file:
                    parser = self.get_default_parser()
                    try:
                        database = parser.parse_file(string_file)
                        if len(database.strings) == 0:
                            return "empty"
                        self.string_files[filename] = database.strings
                        self.update_global_strings()
                        return "success"
                    except Exception:
                        return "parse_error"
            except FileNotFoundError:
                return "file_error"
        else:
            return "success"

    def update_global_strings(self, file=None):
        global_strings = {}
        for strings in self.string_files.values():
            global_strings = {**strings, **global_strings}
        self.global_strings = global_strings

        # update files
        if file:
            files = [file]
        else:
            files = self.bibfiles.values()
        for f in files:
            f.database.strings = {**self.global_strings, **f.local_strings}

    def update_file_strings(self, filename, strings):
        file = self.bibfiles[filename]
        file.local_strings = strings
        file.database.strings = {**self.global_strings, **file.local_strings}

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
    except OSError:
        return False


def backup_file(name):
    backup = name + ".bak"
    if exists(backup) and not has_backup_tag(backup):
        return False

    try:
        if has_backup_tag(name):
            copyfile(name, backup)
        else:
            with open(name, 'r') as infile, open(backup, 'w+') as outfile:
                outfile.write(BACKUP_TAG + "\n\n")
                for line in infile:
                    outfile.write(line)
    except OSError:
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
                except UnicodeDecodeError:
                    return ["error", "parse_error"]

            # initialize bibfile
            bibfile = BadaBibFile(self, name, database)
            self.bibfiles[name] = bibfile
            self.update_global_strings(bibfile)
            self.update_short_names()

            # remove backup tags, if present
            while BACKUP_TAG in database.comments:
                database.comments.remove(BACKUP_TAG)

            # check if file contain bibtex entries
            if len(bibfile.database.entries) == 0:
                bibfile.backup_on_save = False
                return ["empty"]

            return []

        except OSError:
            return ["error", "file_error"]

    def rename_file(self, old_name, new_name):
        bibfile = self.bibfiles.pop(old_name)
        bibfile.update_filename(new_name)
        self.bibfiles[new_name] = bibfile
        self.update_short_names()

    def new_file(self):
        name = get_new_file_name()
        basename = name.split(".")[0]

        # Append unique number if file already exists
        n = 1
        while name in self.bibfiles:
            name = f"{basename} {n}.bib"
            n += 1

        database = BibDatabase()
        bibfile = BadaBibFile(self, name, database, created=True)
        self.bibfiles[name] = bibfile
        self.update_short_names()

        return bibfile

    def save_file(self, name):
        bibfile = self.bibfiles[name]
        errors = []

        # create backup, if desired
        backup = True
        if get_create_backup() and bibfile.backup_on_save:
            bibfile.backup_on_save = False
            if exists(name + ".bak"):
                backup = backup_file(name + ".bak")
            backup = backup and backup_file(name)

        if not backup:
            errors.append("backup")

        try:
            with open(name, "w") as file:
                file.seek(0)
                file.write(bibfile.to_text())
                file.truncate()
        except OSError:
            errors.append("save")

        return errors

    def remove_file(self, name):
        if name in self.bibfiles:
            bibfile = self.bibfiles.pop(name)
            bibfile.unref()

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
                    except UnicodeDecodeError:
                        return "parse_error"
            except OSError:
                return "file_error"
        else:
            return "success"

    def update_global_strings(self, bibfile=None):
        global_strings = {}
        for strings in self.string_files.values():
            global_strings = {**strings, **global_strings}
        self.global_strings = global_strings

        # update files
        if bibfile:
            bibfiles = [bibfile]
        else:
            bibfiles = self.bibfiles.values()
        for file in bibfiles:
            file.database.strings = {**self.global_strings, **file.local_strings}

    def update_file_strings(self, name, strings):
        file = self.bibfiles[name]
        file.local_strings = strings
        file.database.strings = {**self.global_strings, **file.local_strings}

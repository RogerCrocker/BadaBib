# session_manager.py
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


from .config_manager import get_remember_strings
from .config_manager import get_window_geom
from .config_manager import set_window_geom
from .config_manager import get_new_file_name
from .config_manager import get_open_files
from .config_manager import set_open_files
from .config_manager import get_open_tab
from .config_manager import set_open_tab
from .config_manager import get_string_imports
from .config_manager import set_string_imports

from .dialogs import WarningDialog

NEW_FILE_NAME = get_new_file_name()


class SessionManager:
    def __init__(self, window, main_widget):
        self.window = window
        self.main_widget = main_widget

    def restore(self):
        self.restore_window_geom()
        self.window.show_all()
        if get_remember_strings():
            self.restore_string_imports()
        self.restore_open_files()

    def save(self):
        self.save_window_geom()
        self.save_string_imports()
        self.save_open_files()
        self.save_open_tab()

    def restore_window_geom(self):
        window_geom = get_window_geom()
        self.window.set_default_size(window_geom[0], window_geom[1])
        self.main_widget.set_position(window_geom[2])

    def save_window_geom(self):
        width, height = self.window.get_size()
        position = self.main_widget.get_position()
        set_window_geom([width, height, position])

    def restore_open_files(self):
        open_files = get_open_files()
        open_tab = get_open_tab()
        if open_files:
            files = list(open_files.keys())
            states = list(open_files.values())
            self.main_widget.open_files(files, states, open_tab)
        else:
            self.main_widget.new_file()

    def save_open_files(self):
        open_files = {}
        n_pages = self.main_widget.notebook.get_n_pages()
        for n in range(n_pages):
            try:
                itemlist = self.main_widget.notebook.get_nth_page(n).get_child().get_child()
                if itemlist.bibfile.name != NEW_FILE_NAME:
                    open_files[itemlist.bibfile.name] = itemlist.state_to_string()
            except AttributeError:
                pass
        set_open_files(open_files)

    def save_open_tab(self):
        current_file = self.main_widget.get_current_file()
        set_open_tab(current_file.name)

    def restore_string_imports(self):
        string_imports = get_string_imports()
        return_values = [self.window.store.import_strings(filename) for filename in string_imports]
        for filename, return_value in zip(string_imports,  return_values):
            if return_value == "failure":
                message = "Importing strings failed: Cannot read file '{}'.".format(filename)
                WarningDialog(message, window=self.window)
            elif return_value == "empty":
                message = "Importing strings failed: File '{}' does not contain string definitions.".format(filename)
                WarningDialog(message, window=self.window)

    def save_string_imports(self):
        set_string_imports(self.window.store.string_files)

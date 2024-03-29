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
from .config_manager import get_open_files
from .config_manager import set_open_files
from .config_manager import get_open_tab
from .config_manager import set_open_tab
from .config_manager import get_string_imports
from .config_manager import set_string_imports

from .dialogs import WarningDialog


class SessionManager:
    def __init__(self, main_widget):
        self.main_widget = main_widget

    def restore(self, arg_files=None):
        self.restore_window_geom()
        self.main_widget.get_root().show()
        if get_remember_strings():
            self.restore_string_imports()
        if arg_files is None:
            arg_files = []
        self.restore_open_files(arg_files)

    def save(self):
        self.save_window_geom()
        self.save_string_imports()
        self.save_open_files()
        self.save_open_tab()

    def restore_window_geom(self):
        window_geom = get_window_geom()
        self.main_widget.get_root().set_default_size(window_geom[0], window_geom[1])
        self.main_widget.set_position(window_geom[2])

    def save_window_geom(self):
        width = self.main_widget.get_root().get_width()
        height = self.main_widget.get_root().get_height()
        position = self.main_widget.get_position()
        set_window_geom([width, height, position])

    def restore_open_files(self, arg_files):
        saved_files = get_open_files()
        open_files = saved_files | arg_files
        open_files.update(saved_files)

        if arg_files:
            open_tab = list(arg_files.keys())[0]
        else:
            open_tab = get_open_tab()

        if open_files:
            names = list(open_files.keys())
            states = list(open_files.values())
            self.main_widget.open_files(names, states, open_tab=open_tab)
        else:
            self.main_widget.new_file()

    def save_open_files(self):
        open_files = {}
        tabview_pages = self.main_widget.tabbox.tabview.get_pages()
        for tabview_page in tabview_pages:
            itemlist = tabview_page.get_child().itemlist
            if itemlist and not itemlist.bibfile.created:
                open_files[itemlist.bibfile.name] = itemlist.state_to_string()
        set_open_files(open_files)

    def save_open_tab(self):
        itemlist = self.main_widget.get_current_itemlist()
        if itemlist:
            set_open_tab(itemlist.bibfile.name)
        else:
            set_open_tab("")

    def restore_string_imports(self):
        string_imports = get_string_imports()
        statuses = [self.main_widget.store.import_strings(filename) for filename in string_imports]
        for filename, status in zip(string_imports, statuses):
            if status in ("file_error", "parse_error"):
                message = f"Importing strings failed: Cannot read file '{filename}'."
                WarningDialog(message, window=self.main_widget.get_root())
            elif status == "empty":
                message = f"Importing strings failed: File '{filename}' does not contain string definitions."
                WarningDialog(message, window=self.main_widget.get_root())

    def save_string_imports(self):
        set_string_imports(self.main_widget.store.string_files)

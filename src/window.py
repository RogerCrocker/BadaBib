# window.py
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

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, GLib

from .config_manager import get_recent_files
from .config_manager import set_recent_files

from .dialogs import FileChooser
from .dialogs import MenuPopover
from .dialogs import RecentModel

from .store import BadaBibStore

from .main_widget import MainWidget

from .session_manager import SessionManager


class BadaBibWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "BadabibWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.application = kwargs["application"]
        self.set_title("Bada Bib! - BibTeX Editor")

        self.monitor = None
        self.store = BadaBibStore()
        self.main_widget = MainWidget(self.store)
        self.set_child(self.main_widget)

        self.recent_button = Gtk.MenuButton()
        self.recent_button.set_tooltip_text("Recently opened files")

        self.assemble_headerbar()
        self.update_recent_file_menu()

        self.session_manager = SessionManager(self.main_widget)
        GLib.idle_add(self.session_manager.restore, self.application.arg_files)


    def update_recent_file_menu(self):
        recent_files = get_recent_files()
        self.recent_button.set_menu_model(RecentModel(recent_files))

    def clear_recent_file_menu(self):
        set_recent_files({})
        self.recent_button.set_menu_model(RecentModel({}))

    def assemble_headerbar(self, *args, **kwargs):
        headerbar = Gtk.HeaderBar(*args, **kwargs)

        open_button = Gtk.Button.new_with_label("Open")
        open_button.set_tooltip_text("Open file")
        open_button.connect("clicked", self.on_open_clicked)

        open_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        open_box.get_style_context().add_class("linked")
        open_box.append(open_button)
        open_box.append(self.recent_button)
        headerbar.pack_start(open_box)

        new_button = Gtk.Button.new_from_icon_name("document-new-symbolic")
        new_button.set_tooltip_text("New file")
        new_button.connect("clicked", self.on_new_clicked)
        headerbar.pack_start(new_button)

        undo_button = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        undo_button.set_tooltip_text("Undo change")
        undo_button.connect("clicked", self.on_undo_clicked)

        redo_button = Gtk.Button.new_from_icon_name("edit-redo-symbolic")
        redo_button.set_tooltip_text("Redo change")
        redo_button.connect("clicked", self.on_redo_clicked)

        undo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        undo_box.get_style_context().add_class("linked")
        undo_box.append(undo_button)
        undo_box.append(redo_button)
        undo_box.set_margin_start(30)
        headerbar.pack_start(undo_box)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_popover(MenuPopover())
        headerbar.pack_end(menu_button)

        save_button = Gtk.Button.new_with_label("Save")
        save_button.set_tooltip_text("Save current file")
        save_button.connect("clicked", self.on_save_clicked)

        save_as_button = Gtk.Button.new_from_icon_name("document-save-as-symbolic")
        save_as_button.set_tooltip_text("Save current file as...")
        save_as_button.connect("clicked", self.on_save_as_clicked)

        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        save_box.get_style_context().add_class("linked")
        save_box.append(save_button)
        save_box.append(save_as_button)
        headerbar.pack_end(save_box)

        self.set_titlebar(headerbar)

    def do_close_request(self, window=None):
        """invoked by window close button"""
        files = list(self.store.bibfiles.keys())
        self.main_widget.close_files(files, close_app=True)
        return True

    def on_open_clicked(self, _button=None):
        dialog = FileChooser(self)
        dialog.connect("response", self.on_open_response)
        dialog.show()

    def on_open_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            files = dialog.get_files()
            self.main_widget.open_files([file.get_path() for file in files])
        dialog.destroy()

    def on_save_as_clicked(self, _button=None):
        self.main_widget.save_file_as()

    def on_save_clicked(self, _button=None):
        self.main_widget.save_file()

    def on_save_all_clicked(self, _button=None):
        self.main_widget.save_all_files()

    def on_new_clicked(self, _button=None):
        self.main_widget.new_file()

    def on_undo_clicked(self, _button=None):
        itemlist = self.main_widget.get_current_itemlist()
        itemlist.change_buffer.undo_change()

    def on_redo_clicked(self, _button=None):
        itemlist = self.main_widget.get_current_itemlist()
        itemlist.change_buffer.redo_change()

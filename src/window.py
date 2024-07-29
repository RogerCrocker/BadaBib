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


from gi.repository import Adw, GLib, Gtk

from .config_manager import get_recent_files
from .config_manager import set_recent_files
from .dialogs import FileChooser
from .main_widget import MainWidget
from .menus import MainMenu
from .menus import RecentFilesMenu
from .session_manager import SessionManager
from .store import BadaBibStore


class Spacer(Gtk.Separator):
    def __init__(self):
        super().__init__()
        self.get_style_context().add_class("spacer")


class BadaBibWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = kwargs["application"]
        self.set_title("Bada Bib! - BibTeX Editor")

        self.store = BadaBibStore()
        self.main_widget = MainWidget(self.store)
        self.header_bar = self.assemble_header_bar()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(self.header_bar)
        content_box.append(self.main_widget)
        self.set_content(content_box)

        self.session_manager = SessionManager(self.main_widget)
        self.session_manager.restore(self.app.arg_files)

    def update_recent_file_menu(self):
        recent_files = get_recent_files()
        self.app.lookup_action("clear_recent").set_enabled(True)
        self.open_button.set_menu_model(RecentFilesMenu(recent_files))

    def clear_recent_file_menu(self):
        set_recent_files({})
        self.app.lookup_action("clear_recent").set_enabled(False)
        self.open_button.set_menu_model(RecentFilesMenu({}))

    def assemble_header_bar(self):
        header_bar = Adw.HeaderBar()

        self.open_button = Adw.SplitButton()
        self.open_button.set_label("Open")
        self.open_button.set_tooltip_text("Open file")
        self.open_button.connect("clicked", self.on_open_clicked)
        self.update_recent_file_menu()

        new_button = Gtk.Button.new_from_icon_name("tab-new-symbolic")
        new_button.set_tooltip_text("New file")
        new_button.connect("clicked", self.on_new_clicked)

        redo_button = Gtk.Button.new_from_icon_name("edit-redo-symbolic")
        redo_button.set_tooltip_text("Redo change")
        redo_button.connect("clicked", self.on_redo_clicked)

        undo_button = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        undo_button.set_tooltip_text("Undo change")
        undo_button.connect("clicked", self.on_undo_clicked)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_popover(MainMenu())

        save_button = Gtk.Button.new_from_icon_name("document-save-symbolic")
        save_button.set_tooltip_text("Save current file")
        save_button.connect("clicked", self.on_save_clicked)

        save_as_button = Gtk.Button.new_from_icon_name("document-save-as-symbolic")
        save_as_button.set_tooltip_text("Save current file as...")
        save_as_button.connect("clicked", self.on_save_as_clicked)

        header_bar.pack_start(self.open_button)
        header_bar.pack_start(new_button)
        header_bar.pack_start(Spacer())
        header_bar.pack_start(undo_button)
        header_bar.pack_start(redo_button)

        header_bar.pack_end(menu_button)
        header_bar.pack_end(Spacer())
        header_bar.pack_end(save_as_button)
        header_bar.pack_end(save_button)

        return header_bar

    def do_close_request(self, window=None):
        """invoked by window close button"""
        bibfiles = list(self.store.bibfiles.values())
        if bibfiles:
            self.main_widget.close_files(bibfiles, close_app=True)
            return True
        return False

    def on_open(self, action=None, data=None):
        self.on_open_clicked()

    def on_open_clicked(self, _button=None):
        """
        Have user select one or multiple files.

        Parameters
        ----------
        _button: Adw.SplitButton | None
            Button clicked by user, None if keyboard shortcut was used. Unused.
        """
        dialog = FileChooser()
        dialog.open_multiple(self, None, self.on_open_response)

    def on_open_response(self, dialog, task):
        """
        Open selected files.

        Parameters
        ----------
        dialog: Gtk.FileDialog
            File dialog the user interacted with
        task: Gio.AsyncResult
            User selection
        """
        try:
            gfiles = dialog.open_multiple_finish(task)
        except GLib.GError:
            return None
        if gfiles:
            files = [gfile.get_path() for gfile in gfiles]
            self.main_widget.open_files(files)

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
        if itemlist:
            itemlist.change_buffer.undo_change()

    def on_redo_clicked(self, _button=None):
        itemlist = self.main_widget.get_current_itemlist()
        if itemlist:
            itemlist.change_buffer.redo_change()

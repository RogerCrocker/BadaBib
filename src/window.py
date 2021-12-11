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
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from .config_manager import get_window_geom
from .config_manager import set_window_geom
from .config_manager import get_open_files
from .config_manager import reset_open_files
from .config_manager import get_recent_files
from .config_manager import set_recent_files

from .dialogs import FileChooser
from .dialogs import MenuPopover
from .dialogs import RecentModel

from .store import BadaBibStore

from .main_widget import MainWidget


class BadaBibWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "BadabibWindow"

    def __init__(self, **kwargs):
        Gtk.ApplicationWindow.__init__(self, **kwargs)
        self.application = kwargs["application"]

        self.store = BadaBibStore()
        self.main_widget = MainWidget(self, self.store)
        self.add(self.main_widget)

        self.recent_button = Gtk.MenuButton()
        self.recent_button.set_use_popover(False)
        self.recent_button.set_tooltip_text("Recently opened files")

        self.assemble_headerbar()
        self.update_recent_file_menu()
        self.restore_window_geom()
        self.show_all()
        self.restore_open_files()

    def restore_window_geom(self):
        window_geom = get_window_geom()
        self.set_default_size(window_geom[0], window_geom[1])

    def restore_open_files(self):
        open_files = get_open_files()
        if open_files:
            for file, state in open_files.items():
                self.main_widget.open_file_show_loading(file, state, True)
            reset_open_files()
        else:
            self.main_widget.new_file()

    def update_recent_file_menu(self):
        recent_files = get_recent_files()
        self.recent_button.set_menu_model(RecentModel(recent_files))

    def clear_recent_file_menu(self):
        set_recent_files({})
        self.recent_button.set_menu_model(RecentModel({}))

    def assemble_headerbar(self, *args, **kwargs):
        headerbar = Gtk.HeaderBar(*args, **kwargs)
        headerbar.set_show_close_button(True)
        headerbar.props.title = "Bada Bib! - BibTeX Editor"

        open_button = Gtk.Button.new_with_label("Open")
        open_button.set_tooltip_text("Open file")
        open_button.connect("clicked", self.on_open_clicked)

        open_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        open_box.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)
        open_box.pack_start(open_button, True, True, 0)
        open_box.pack_start(self.recent_button, True, True, 0)
        headerbar.pack_start(open_box)

        new_button = Gtk.Button.new_from_icon_name("document-new-symbolic", Gtk.IconSize.BUTTON)
        new_button.set_tooltip_text("New file")
        new_button.connect("clicked", self.on_new_clicked)
        headerbar.pack_start(new_button)

        undo_button = Gtk.Button.new_from_icon_name("edit-undo-symbolic", Gtk.IconSize.BUTTON)
        undo_button.set_tooltip_text("Undo change")
        undo_button.connect("clicked", self.on_undo_clicked)

        redo_button = Gtk.Button.new_from_icon_name("edit-redo-symbolic", Gtk.IconSize.BUTTON)
        redo_button.set_tooltip_text("Redo change")
        redo_button.connect("clicked", self.on_redo_clicked)

        undo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        undo_box.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)
        undo_box.pack_start(undo_button, True, True, 0)
        undo_box.pack_start(redo_button, True, True, 0)
        undo_box.set_margin_start(30)
        headerbar.pack_start(undo_box)

        menu_button = Gtk.MenuButton()
        menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
        menu_button.add(menu_icon)
        menu_button.set_popover(MenuPopover())
        headerbar.pack_end(menu_button)

        save_button = Gtk.Button.new_with_label("Save")
        save_button.set_tooltip_text("Save current file")
        save_button.connect("clicked", self.on_save_clicked)

        save_as_button = Gtk.Button.new_from_icon_name("document-save-as-symbolic", Gtk.IconSize.BUTTON)
        save_as_button.set_tooltip_text("Save current file as...")
        save_as_button.connect("clicked", self.on_save_as_clicked)

        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        save_box.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)
        save_box.pack_start(save_button, True, True, 0)
        save_box.pack_start(save_as_button, True, True, 0)
        headerbar.pack_end(save_box)

        self.set_titlebar(headerbar)

    def on_application_shutdown(self, _widget=None):
        """invoked by app.quit action"""
        width, height = self.get_size()
        position = self.main_widget.get_position()
        set_window_geom([width, height, position])
        self.destroy()

    def do_delete_event(self, window=None):
        """invoked by window close button"""
        close = self.main_widget.close_all_files(close_app=True)
        if close:
            self.on_application_shutdown()
        return True

    def on_open_clicked(self, _button=None):
        dialog = FileChooser(self)
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            self.main_widget.open_file_show_loading(filename)
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

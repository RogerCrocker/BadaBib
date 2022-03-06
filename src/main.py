# main.py
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

from gi.repository import GLib, Gtk, Gio

from sys import argv

from .customization import capitalize
from .customization import protect
from .customization import convert_to_unicode
from .customization import convert_to_latex
from .customization import correct_hyphen

from .window import BadaBibWindow

from .layout_manager import LayoutManagerWindow

from .string_manager import StringManagerWindow

from .preferences import PreferencesWindow

from .dialogs import AboutDialog


class Application(Gtk.Application):
    def __init__(self, version):
        GLib.set_application_name("Bada Bib!")
        GLib.set_prgname('badabib')
        super().__init__(
            application_id="com.github.rogercrocker.badabib",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            )
        self.window = None
        self.version = version
        self.arg_files = {}

        self.connect("open", self.on_open_arg_files)


    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = BadaBibWindow(application=self)
        self.window.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.add_global_accelerators()

    def on_open_arg_files(self, application, files, hint, _):
        if not self.props.active_window:
            self.arg_files = {file.get_path() : None for file in files}
            self.do_activate()
        else:
            self.window.main_widget.open_files([file.get_path() for file in files])

    def add_global_accelerators(self):
        # Files
        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self.on_open)
        self.set_accels_for_action("app.open", ["<Control>o"])
        self.add_action(open_action)

        open_file_action = Gio.SimpleAction.new("open_file", GLib.VariantType("s"))
        open_file_action.connect("activate", self.on_open_file)
        self.add_action(open_file_action)

        new_file_action = Gio.SimpleAction.new("new_file", None)
        new_file_action.connect("activate", self.on_new_file)
        self.set_accels_for_action("app.new_file", ["<Control>t"])
        self.add_action(new_file_action)

        save_action = Gio.SimpleAction.new("save", None)
        save_action.connect("activate", self.on_save)
        self.set_accels_for_action("app.save", ["<Control>s"])
        self.add_action(save_action)

        save_as_action = Gio.SimpleAction.new("save_as", None)
        save_as_action.connect("activate", self.on_save_as)
        self.set_accels_for_action("app.save_as", ["<Control><Shift>s"])
        self.add_action(save_as_action)

        save_all_action = Gio.SimpleAction.new("save_all", None)
        save_all_action.connect("activate", self.on_save_all)
        self.set_accels_for_action("app.save_all", ["<Control><Alt>s"])
        self.add_action(save_all_action)

        close_action = Gio.SimpleAction.new("close", None)
        close_action.connect("activate", self.on_close)
        self.set_accels_for_action("app.close", ["<Control>w"])
        self.add_action(close_action)

        clear_recent_action = Gio.SimpleAction.new("clear_recent", None)
        clear_recent_action.connect("activate", self.on_clear_recent)
        self.add_action(clear_recent_action)

        # Entries
        new_entry_action = Gio.SimpleAction.new("new_entry", None)
        new_entry_action.connect("activate", self.on_new_entry)
        self.set_accels_for_action("app.new_entry", ["<Control>n"])
        self.add_action(new_entry_action)

        find_action = Gio.SimpleAction.new("find", None)
        find_action.connect("activate", self.on_find)
        self.set_accels_for_action("app.find", ["<Control>f"])
        self.add_action(find_action)

        # Fields
        cap_action = Gio.SimpleAction.new("cap", None)
        cap_action.connect("activate", self.do_capitalize)
        self.set_accels_for_action("app.cap", ["<Alt>u"])
        self.add_action(cap_action)

        protect_caps_action = Gio.SimpleAction.new("protect_caps", None)
        protect_caps_action.connect("activate", self.do_protect)
        self.set_accels_for_action("app.protect_caps", ["<Alt>p"])
        self.add_action(protect_caps_action)

        unicode_action = Gio.SimpleAction.new("unicode", None)
        unicode_action.connect("activate", self.do_to_unicode)
        self.set_accels_for_action("app.unicode", ["<Alt>o"])
        self.add_action(unicode_action)

        latex_action = Gio.SimpleAction.new("latex", None)
        latex_action.connect("activate", self.do_to_latex)
        self.set_accels_for_action("app.latex", ["<Alt>l"])
        self.add_action(latex_action)

        key_action = Gio.SimpleAction.new("key", None)
        key_action.connect("activate", self.do_generate_key)
        self.set_accels_for_action("app.key", ["<Alt>k"])
        self.add_action(key_action)

        correct_hyphen_action = Gio.SimpleAction.new("correct_hyphen", None)
        correct_hyphen_action.connect("activate", self.do_correct_hyphen)
        self.set_accels_for_action("app.correct_hyphen", ["<Alt>h"])
        self.add_action(correct_hyphen_action)

        # Window
        undo_action = Gio.SimpleAction.new("undo", None)
        undo_action.connect("activate", self.on_undo)
        self.set_accels_for_action("app.undo", ["<Control>z"])
        self.add_action(undo_action)

        redo_action = Gio.SimpleAction.new("redo", None)
        redo_action.connect("activate", self.on_redo)
        self.set_accels_for_action("app.redo", ["<Control><Shift>z"])
        self.add_action(redo_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.add_action(quit_action)

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self.do_show_shortcuts)
        self.set_accels_for_action("app.shortcuts", ["<Control>question"])
        self.add_action(shortcuts_action)

        custom_editor_action = Gio.SimpleAction.new("custom_editor", None)
        custom_editor_action.connect("activate", self.do_show_editor_configurator)
        self.set_accels_for_action("app.custom_editor", ["<Control><Alt>c"])
        self.add_action(custom_editor_action)

        next_tab_action = Gio.SimpleAction.new("next_tab", None)
        next_tab_action.connect("activate", self.do_next_tab)
        self.set_accels_for_action("app.next_tab", ["<Control>Tab"])
        self.add_action(next_tab_action)

        prev_tab_action = Gio.SimpleAction.new("prev_tab", None)
        prev_tab_action.connect("activate", self.do_prev_tab)
        self.set_accels_for_action("app.prev_tab", ["<Control><shift>Tab"])
        self.add_action(prev_tab_action)

        copy_action = Gio.SimpleAction.new("copy", None)
        copy_action.connect("activate", self.on_copy_entry)
        self.set_accels_for_action("app.copy", ["<Control><Shift>c"])
        self.add_action(copy_action)

        cut_action = Gio.SimpleAction.new("cut", None)
        cut_action.connect("activate", self.on_cut_entry)
        self.set_accels_for_action("app.cut", ["<Control><Shift>x"])
        self.add_action(cut_action)

        paste_action = Gio.SimpleAction.new("paste", None)
        paste_action.connect("activate", self.on_paste_entry)
        self.set_accels_for_action("app.paste", ["<Control><Shift>v"])
        self.add_action(paste_action)

        string_manager_action = Gio.SimpleAction.new("manage_strings", None)
        string_manager_action.connect("activate", self.do_show_string_manager)
        self.set_accels_for_action("app.manage_strings", ["<Control><Alt>m"])
        self.add_action(string_manager_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.do_show_preferences)
        self.set_accels_for_action("app.preferences", ["<Control>comma"])
        self.add_action(preferences_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.do_show_about)
        self.add_action(about_action)

        dummy_action = Gio.SimpleAction.new("dummy", None)
        dummy_action.set_enabled(False)
        self.add_action(dummy_action)

    def on_clear_recent(self, action=None, data=None):
        self.window.clear_recent_file_menu()

    def on_open(self, action=None, data=None):
        self.window.on_open_clicked()

    def on_open_file(self, _action, glib_filename):
        self.window.main_widget.open_files(glib_filename.unpack())

    def on_new_file(self, action=None, data=None):
        self.window.main_widget.new_file()

    def on_save(self, action=None, data=None):
        self.window.main_widget.save_file()

    def on_save_as(self, action=None, data=None):
        self.window.main_widget.save_file_as()

    def on_save_all(self, action=None, data=None):
        self.window.main_widget.save_all_files()

    def on_close(self, action=None, data=None):
        self.window.main_widget.on_tab_closed()

    def on_new_entry(self, action=None, data=None):
        self.window.main_widget.add_items()

    def on_find(self, action=None, data=None):
        self.window.main_widget.search_itemlist()

    def on_goto(self, action=None, data=None):
        self.window.main_widget.on_goto_clicked()

    def on_copy_entry(self, action=None, data=None):
        items = self.window.main_widget.get_selected_items()
        self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]

    def on_cut_entry(self, action=None, data=None):
        items = self.window.main_widget.get_selected_items()
        self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]
        self.window.main_widget.delete_items(items)

    def on_paste_entry(self, action=None, data=None):
        entries = self.window.main_widget.copy_paste_buffer
        self.window.main_widget.add_items(None, entries)

    def do_show_editor_configurator(self, action=None, data=None):
        LayoutManagerWindow(self.window)

    def do_show_string_manager(self, action=None, data=None):
        StringManagerWindow(self.window)

    def do_show_about(self, action=None, data=None):
        dialog = AboutDialog(self.window)
        dialog.show()

    def do_next_tab(self, action=None, data=None):
        self.window.main_widget.get_current_itemlist().grab_focus()
        self.window.main_widget.notebook.next_page(1)

    def do_prev_tab(self, action=None, data=None):
        self.window.main_widget.get_current_itemlist().grab_focus()
        self.window.main_widget.notebook.next_page(-1)

    def do_capitalize(self, action=None, data=None):
        form = self.window.get_focus().get_parent()
        try:
            form.apply(capitalize, 4)
        except AttributeError:
            pass

    def do_protect(self, action=None, data=None):
        form = self.window.get_focus().get_parent()
        try:
            form.apply(protect)
        except AttributeError:
            pass

    def do_correct_hyphen(self, action=None, data=None):
        form = self.window.get_focus().get_parent()
        try:
            form.apply(correct_hyphen)
        except AttributeError:
            pass

    def do_to_unicode(self, action=None, data=None):
        form = self.window.get_focus().get_parent()
        try:
            form.apply(convert_to_unicode)
        except AttributeError:
            pass

    def do_to_latex(self, action=None, data=None):
        form = self.window.get_focus().get_parent()
        try:
            form.apply(convert_to_latex)
        except AttributeError:
            pass

    def do_generate_key(self, action=None, data=None):
        self.window.main_widget.generate_key()

    def do_double_hyphen(self, action=None, data=None):
        self.window.main_widget.generate_key()

    def on_undo(self, action=None, data=None):
        self.window.on_undo_clicked()

    def on_redo(self, action=None, data=None):
        self.window.on_redo_clicked()

    def on_quit(self, action=None, data=None):
        self.window.do_close_request()

    def do_show_shortcuts(self, action=None, data=None):
        builder = Gtk.Builder.new_from_resource("/com/github/rogercrocker/badabib/shortcuts.ui")
        shortcuts_overview = builder.get_object("shortcuts_overview")
        shortcuts_overview.set_transient_for(self.window)
        shortcuts_overview.show()

    def do_show_preferences(self, action=None, data=None):
        PreferencesWindow(self.window)


def main(version):
    app = Application(version)
    return app.run(argv)

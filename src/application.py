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
gi.require_version("Adw", "1")
gi.require_version("GtkSource", "5")

from gi.repository import GLib, Gtk, Gio, Adw

from sys import argv

from .config_manager import get_color_scheme

from .customization import title_case
from .customization import upper_case
from .customization import lower_case
from .customization import protect_caps
from .customization import convert_to_unicode
from .customization import convert_to_latex
from .customization import sanitize_range

from .window import BadaBibWindow

from .layout_manager import LayoutManagerWindow

from .string_manager import StringManagerWindow

from .preferences import PreferencesWindow

from .dialogs import AboutDialog

from .forms import SingleLine
from .forms import MultiLine
from .forms import SourceView


menu_actions = [
    "title_case",
    "upper_case",
    "lower_case",
    "protect_caps",
    "to_latex",
    "to_unicode",
    ]


class Application(Adw.Application):
    def __init__(self, version):
        super().__init__(
            application_id="com.github.rogercrocker.badabib",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            )
        self.window = None
        self.version = version
        self.menu_actions_active = True
        self.arg_files = {}

        GLib.set_application_name("Bada Bib!")
        GLib.set_prgname('badabib')

    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = BadaBibWindow(application=self)
        self.set_color_scheme()
        self.window.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.install_actions()
        self.connect("open", self.on_open_arg_files)

    def on_open_arg_files(self, application, files, hint, _):
        if not self.props.active_window:
            self.arg_files = {file.get_path() : None for file in files}
            self.do_activate()
        else:
            self.window.main_widget.open_files([file.get_path() for file in files])

    def set_color_scheme(self):
        # set application wide scheme
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(get_color_scheme())

        # manually set scheme for Gtk.SourceViews
        self.window.main_widget.source_view.form.set_color_scheme()

        for editor in self.window.main_widget.editors.values():
            for name, form in editor.forms.items():
                if name == "abstract":
                    form.set_color_scheme()

    def get_actions(self):
        actions = [
            ("quit",            None,                   self.on_quit,           "<Control>q"),
            ("undo",            None,                   self.on_undo,           "<Control>z"),
            ("redo",            None,                   self.on_redo,           "<Control><Shift>z"),
            ("show_shortcuts",  None,                   self.on_show_shortcuts, "<Control>question"),
            ("show_prefs",      None,                   self.on_show_prefs,     "<Control>comma"),
            ("show_about",      None,                   self.on_show_about,     None),
            ("custom_editor",   None,                   self.on_custom_editor,  "<Control><Alt>c"),
            ("manage_strings",  None,                   self.on_manage_strings, "<Control><Alt>m"),
            ("open",            None,                   self.on_open,           "<Control>o"),
            ("open_file",       GLib.VariantType("s"),  self.on_open_file,      None),
            ("new_file",        None,                   self.on_new_file,       "<Control>t"),
            ("save",            None,                   self.on_save,           "<Control>s"),
            ("save_as",         None,                   self.on_save_as,        "<Control><Shift>s"),
            ("save_all",        None,                   self.on_save_all,       "<Control><Alt>s"),
            ("close",           None,                   self.on_close,          "<Control>w"),
            ("clear_recent",    None,                   self.on_clear_recent,   None),
            ("new_entry",       None,                   self.on_new_entry,      "<Control>n"),
            ("copy",            None,                   self.on_copy,           "<Control><Shift>c"),
            ("cut",             None,                   self.on_cut,            "<Control><Shift>x"),
            ("paste",           None,                   self.on_paste,          "<Control><Shift>v"),
            ("find",            None,                   self.on_find,           "<Control>f"),
            ("next_tab",        None,                   self.on_next_tab,       "<Control>Tab"),
            ("prev_tab",        None,                   self.on_prev_tab,       "<Control><Shift>Tab"),
            ("update_bibtex",   None,                   self.on_update_bibtex,  "<Control>Return"),
            ("change_case",     None,                   self.on_change_case,    "<Alt>c"),
            ("title_case",      None,                   self.on_title_case,     None),
            ("upper_case",      None,                   self.on_upper_case,     None),
            ("lower_case",      None,                   self.on_lower_case,     None),
            ("protect_caps",    None,                   self.on_protect_caps,   "<Alt>p"),
            ("sanitize_range",  None,                   self.on_sanitize_range, "<Alt>r"),
            ("to_unicode",      None,                   self.on_to_unicode,     "<Alt>o"),
            ("to_latex",        None,                   self.on_to_latex,       "<Alt>l"),
            ("generate_key",    None,                   self.on_generate_key,   "<Alt>k"),
        ]
        return actions

    def install_actions(self):
        actions = self.get_actions()
        for name, param, func, accel in actions:
            action = Gio.SimpleAction.new(name, param)
            action.connect("activate", func)
            self.set_accels_for_action(f"app.{name}", [accel])
            self.add_action(action)

    def enable_menu_actions(self, state):
        if self.menu_actions_active != state:
            self.menu_actions_active = state
            for name in menu_actions:
                self.lookup_action(name).set_enabled(state)

    # Window

    def on_quit(self, action=None, data=None):
        self.window.do_close_request()

    def on_undo(self, action=None, data=None):
        self.window.on_undo_clicked()

    def on_redo(self, action=None, data=None):
        self.window.on_redo_clicked()

    # Dialogs

    def on_show_shortcuts(self, action=None, data=None):
        builder = Gtk.Builder.new_from_resource("/com/github/rogercrocker/badabib/shortcuts.ui")
        shortcuts_overview = builder.get_object("shortcuts_overview")
        shortcuts_overview.set_transient_for(self.window)
        shortcuts_overview.show()

    def on_show_prefs(self, action=None, data=None):
        PreferencesWindow(self.window)

    def on_show_about(self, action=None, data=None):
        dialog = AboutDialog(self.window)
        dialog.show()

    def on_custom_editor(self, action=None, data=None):
        LayoutManagerWindow(self.window)

    def on_manage_strings(self, action=None, data=None):
        StringManagerWindow(self.window)

    # Files

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
        page_num = self.window.main_widget.notebook.get_current_page()
        page = self.window.main_widget.notebook.get_nth_page(page_num)
        if page.itemlist:
            self.window.main_widget.close_files(page.itemlist.bibfile)
        else:
            self.window.main_widget.notebook.remove_page(page_num)

    def on_clear_recent(self, action=None, data=None):
        self.window.clear_recent_file_menu()

    # Entries

    def on_new_entry(self, action=None, data=None):
        self.window.main_widget.add_items()

    def on_copy(self, action=None, data=None):
        items = self.window.main_widget.get_selected_items()
        if items:
            self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]

    def on_cut(self, action=None, data=None):
        items = self.window.main_widget.get_selected_items()
        if items:
            self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]
            self.window.main_widget.delete_items(items)

    def on_paste(self, action=None, data=None):
        entries = self.window.main_widget.copy_paste_buffer
        if entries:
            self.window.main_widget.add_items(None, entries)

    def on_find(self, action=None, data=None):
        self.window.main_widget.search_itemlist()

    def on_goto(self, action=None, data=None):
        self.window.main_widget.on_goto_clicked()

    # Notebook

    def on_next_tab(self, action=None, data=None):
        self.window.main_widget.get_current_itemlist().grab_focus()
        self.window.main_widget.notebook.next_page(1)

    def on_prev_tab(self, action=None, data=None):
        self.window.main_widget.get_current_itemlist().grab_focus()
        self.window.main_widget.notebook.next_page(-1)

    # Customizations

    def get_active_form(self):
        # Check if action is invoked via shortcut
        # Do not grab focus in this case
        widget = self.window.get_focus()
        if isinstance(widget, Gtk.Text):
            form = widget.get_parent()
            # single line entry
            if isinstance(form, SingleLine):
                return form, False
            # combo box entry
            return None, False

        # multiline entry
        if isinstance(widget, MultiLine):
            return widget, False

        # Otherwise action was invoked using a right-click menu
        # We need to grab the focus in this case

        # source view
        widget = self.window.main_widget.outer_stack.get_visible_child()
        if isinstance(widget, SourceView):
            return widget.form, True

        # editor/catch all - returns None is no form is active
        editor = self.window.main_widget.get_current_editor()
        return editor.current_form, True

    def apply_customization(self, customization, n=0):
        form, grab_focus = self.get_active_form()
        if form:
            form.apply(customization, n)
            if grab_focus:
                form.grab_focus()

    def on_update_bibtex(self, action=None, data=None):
        self.window.main_widget.update_bibtex()

    def on_change_case(self, action=None, data=None):
        form, grab_focus = self.get_active_form()
        if form:
            counter = form.change_case_counter
            if counter == 0:
                form.apply(title_case, 4)
            elif counter == 1:
                form.apply(upper_case)
            elif counter == 2:
                form.apply(lower_case)
            if grab_focus:
                form.grab_focus()
            form.change_case_counter += 1
            form.change_case_counter %= 3

    def on_title_case(self, action=None, data=None):
        self.apply_customization(title_case)

    def on_upper_case(self, action=None, data=None):
        self.apply_customization(upper_case)

    def on_lower_case(self, action=None, data=None):
        self.apply_customization(lower_case)

    def on_protect_caps(self, action=None, data=None):
        self.apply_customization(protect_caps)

    def on_sanitize_range(self, action=None, data=None):
        self.apply_customization(sanitize_range)

    def on_to_unicode(self, action=None, data=None):
        self.apply_customization(convert_to_unicode)

    def on_to_latex(self, action=None, data=None):
        self.apply_customization(convert_to_latex)

    def on_generate_key(self, action=None, data=None):
        self.window.main_widget.generate_key()


def main(version):
    app = Application(version)
    return app.run(argv)

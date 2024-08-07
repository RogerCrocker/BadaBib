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

import badabib.customization
import badabib.forms

from gi.repository import Adw, Gio, GLib, Gtk
from sys import argv

from .layout_manager import LayoutManagerWindow
from .preferences import PreferencesWindow
from .string_manager import StringManagerWindow
from .window import BadaBibWindow


# Names of actions to customize fields
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
        """
        Create new application instance.

        Parameters
        ----------
        version: str
            Version string
        """
        super().__init__(
            application_id="com.github.rogercrocker.badabib",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            )
        self.window = None
        self.version = version

        # Switch to turn customization menu on/off
        self.menu_actions_active = True

        # Files passed via the command line or file browser
        self.arg_files = {}

        GLib.set_application_name("Bada Bib!")
        GLib.set_prgname('badabib')

    def do_startup(self):
        """
        Sets up the application when it first starts, calls either activate or
        open.
        """
        Adw.Application.do_startup(self)

        # Listen to style changes
        Adw.StyleManager.get_default().connect("notify::dark", self.on_color_scheme_changed)

        # Install custom actions
        self.install_actions()

    def do_activate(self):
        """
        Shows the default first window of the application (like a new document).
        This corresponds to the application being launched by the desktop environment.
        """
        # Redirect to open without files
        self.do_open([])

    def do_open(self, gfiles, _n_files=None, _hint=""):
        """
        Opens files and shows them in a new window. This corresponds to someone
        trying to open a document (or documents) using the application from the
        file browser, or similar.

        Parameters
        ----------
        gfiles: list of Gio.File
            Files to be opened
        _n_files: int
            Number of files. Unused
        _hint: str
            Intended to be used by applications that have multiple modes for
            opening files. Unused.
        """
        # Check if app is already running
        self.window = self.props.active_window

        # If not, create new window
        if not self.window:
            # Files have no internal states yet (state = None)
            self.arg_files = {file.get_path() : None for file in gfiles}
            self.window = BadaBibWindow(application=self)
            self.window.present()

        # Else, open files
        else:
            self.window.main_widget.open_files([file.get_path() for file in gfiles])

    def get_actions(self):
        """List of all custom actions with shortcuts."""
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
        """Install all custom actions defined in get_actions."""
        actions = self.get_actions()
        for name, param, func, accel in actions:
            action = Gio.SimpleAction.new(name, param)
            action.connect("activate", func)
            self.set_accels_for_action(f"app.{name}", [accel])
            self.add_action(action)

    def enable_menu_actions(self, state):
        """
        Turn menu with custom actions on/off.

        Parameters
        ----------
        state: bool
            True  -> enable menu
            False -> disable menu
        """
        if self.menu_actions_active != state:
            self.menu_actions_active = state
            for name in menu_actions:
                self.lookup_action(name).set_enabled(state)

    # Theme

    def on_color_scheme_changed(self, _style_manager, _gparam):
        """
        Manually set scheme for Gtk.SourceViews.

        Parameters
        ----------
        _style_manager: Adw.StyleManager
            Active StyleManager. Unused.
        _gparam: GParamBoolean
            Style parameter 'light'/'dark'. Unused.
        """
        self.window.main_widget.source_view.form.set_color_scheme()
        for editor in self.window.main_widget.editors.values():
            for name, form in editor.forms.items():
                # Abstract is the only SourceView form
                if name == "abstract":
                    form.set_color_scheme()

    # Window

    def on_quit(self, action=None, data=None):
        """
        Handle "quit" signal.

        Parameters
        ----------
        action: Gio.SimpleAction
            Invoked action. Unused
        data: None
            Action parameters. Unused.
        """
        self.window.do_close_request()

    def on_undo(self, action=None, data=None):
        """Handle "undo" signal. See on_quit for parameters."""
        self.window.on_undo_clicked()

    def on_redo(self, action=None, data=None):
        """Handle "redo" signal. See on_quit for parameters."""
        self.window.on_redo_clicked()

    # Dialogs

    def on_show_shortcuts(self, action=None, data=None):
        """Build and show shortcuts window. See on_quit for parameters"""
        builder = Gtk.Builder.new_from_resource("/com/github/rogercrocker/badabib/shortcuts.ui")
        shortcuts_overview = builder.get_object("shortcuts_overview")
        shortcuts_overview.set_transient_for(self.window)
        shortcuts_overview.show()

    def on_show_prefs(self, action=None, data=None):
        """Show preferences window. See on_quit for parameters."""
        PreferencesWindow(self.window)

    def on_show_about(self, action=None, data=None):
        """Show about dialog. See on_quit for parameters."""
        dialog = Adw.AboutDialog.new()
        dialog.set_application_icon("com.github.rogercrocker.badabib")
        dialog.set_application_name("Bada Bib!")
        dialog.set_version(self.version)
        dialog.set_website("https://github.com/RogerCrocker/BadaBib")
        dialog.set_issue_url("https://github.com/RogerCrocker/BadaBib/issues")
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.present()

    def on_custom_editor(self, action=None, data=None):
        """Show editor layout manager. See on_quit for parameters."""
        LayoutManagerWindow(self.window)

    def on_manage_strings(self, action=None, data=None):
        """Show string manager. See on_quit for parameters."""
        StringManagerWindow(self.window)

    # Files

    def on_open(self, action=None, data=None):
        """Handle open signal. See on_quit for parameters."""
        self.window.on_open_clicked()

    def on_open_file(self, _action, glib_filename):
        """Handle open_file signal.

        Parameters
        ----------
        _action: Gio.SimpleAction
            Invoked action. Unused
        glib_filename: GLib.Variant of str
            Name (path) of file.
        """
        self.window.main_widget.open_files(glib_filename.unpack())

    def on_new_file(self, action=None, data=None):
        """Handle new_file signal. See on_quit for parameters."""
        self.window.main_widget.new_file()

    def on_save(self, action=None, data=None):
        """Handle save signal. See on_quit for parameters."""
        self.window.main_widget.save_file()

    def on_save_as(self, action=None, data=None):
        """Handle save_as signal. See on_quit for parameters."""
        self.window.main_widget.save_file_as()

    def on_save_all(self, action=None, data=None):
        """Handle save_all signal. See on_quit for parameters."""
        self.window.main_widget.save_all_files()

    def on_close(self, action=None, data=None):
        """
        Handle close signal by closing currently selected tab.
        See on_quit for parameters.
        """
        tabview = self.window.main_widget.tabbox.tabview
        tabview.close_page(tabview.get_selected_page())

    def on_clear_recent(self, action=None, data=None):
        """Handle clear_recent signal. See on_quit for parameters."""
        self.window.clear_recent_file_menu()

    # Entries

    def on_new_entry(self, action=None, data=None):
        """Handle new_entry signal. See on_quit for parameters."""
        self.window.main_widget.add_items()

    def on_copy(self, action=None, data=None):
        """
        Handle copy signal by copying selected entries into copy/paste buffer.
        See on_quit for parameters.
        """
        items = self.window.main_widget.get_selected_items()
        if items:
            self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]

    def on_cut(self, action=None, data=None):
        """
        Handle cut signal by copying selected entries into copy/paste buffer
        and deleting items in file afterwards. See on_quit for parameters.
        """
        items = self.window.main_widget.get_selected_items()
        if items:
            self.window.main_widget.copy_paste_buffer = [item.entry.copy() for item in items]
            self.window.main_widget.delete_items(items)

    def on_paste(self, action=None, data=None):
        """
        Handle paste signal by pasting entries in copy/paste buffer to current
        file. See on_quit for parameters.
        """
        entries = self.window.main_widget.copy_paste_buffer
        if entries:
            self.window.main_widget.add_items(entries=[entry.copy() for entry in entries])

    def on_find(self, action=None, data=None):
        """Handle find signal. See on_quit for parameters."""
        self.window.main_widget.search_itemlist()

    def on_goto(self, action=None, data=None):
        """Handle goto signal. See on_quit for parameters."""
        self.window.main_widget.on_goto_clicked()

    # TabView - Can be removed in the future

    def on_next_tab(self, action=None, data=None):
        """Handle next_tab signal. See on_quit for parameters."""
        self.window.main_widget.tabbox.next_page(1)

    def on_prev_tab(self, action=None, data=None):
        """Handle prev_tab signal. See on_quit for parameters."""
        self.window.main_widget.tabbox.next_page(-1)

    # Customizations

    def get_active_form(self):
        """ Returns currenlty active form of editor."""
        # Get focused widget
        widget = self.window.get_focus()

        # Check if action is invoked via shortcut.
        # Do not grab focus in this case.
        if isinstance(widget, Gtk.Text):
            form = widget.get_parent()
            # single line entry
            if isinstance(form, badabib.forms.SingleLine):
                return form, False
            # combo box entry
            return None, False

        # multiline entry
        if isinstance(widget, badabib.forms.MultiLine):
            return widget, False

        # Otherwise action was invoked using a right-click menu.
        # We need to grab the focus in this case.

        # source view
        widget = self.window.main_widget.outer_stack.get_visible_child()
        if isinstance(widget, badabib.forms.SourceView):
            return widget.form, True

        # editor/catch all - returns None is no form is active
        editor = self.window.main_widget.get_current_editor()
        if editor:
            return editor.current_form, True
        return None, False

    def apply_customization(self, customization):
        """
        Apply customization function to text of form.

        Parameters
        ----------
        customization: function(str, dict, int)
            Customization function. See customization.py for examples.
        n: int
            Additional parameter used by some customizations.
        """
        form, grab_focus = self.get_active_form()
        if form:
            form.apply(customization)
            if grab_focus:
                form.grab_focus()

    def on_update_bibtex(self, action=None, data=None):
        """Handle update_bibtex signal. See on_quit for parameters."""
        self.window.main_widget.update_bibtex()

    def on_change_case(self, action=None, data=None):
        """Handle change_case signal. See on_quit for parameters."""
        form, grab_focus = self.get_active_form()
        if form:
            # Cycle through case types
            counter = form.change_case_counter
            if counter == 0:
                form.apply(badabib.customization.title_case)
            elif counter == 1:
                form.apply(badabib.customization.upper_case)
            elif counter == 2:
                form.apply(badabib.customization.lower_case)
            if grab_focus:
                form.grab_focus()
            form.change_case_counter += 1
            form.change_case_counter %= 3

    def on_title_case(self, action=None, data=None):
        """Handle title_case signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.title_case)

    def on_upper_case(self, action=None, data=None):
        """Handle upper_case signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.upper_case)

    def on_lower_case(self, action=None, data=None):
        """Handle lower_case signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.lower_case)

    def on_protect_caps(self, action=None, data=None):
        """Handle protect_caps signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.protect_caps)

    def on_sanitize_range(self, action=None, data=None):
        """Handle sanitize_range signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.sanitize_range)

    def on_to_unicode(self, action=None, data=None):
        """Handle to_unicode signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.convert_to_unicode)

    def on_to_latex(self, action=None, data=None):
        """Handle to_latex signal. See on_quit for parameters."""
        self.apply_customization(badabib.customization.convert_to_latex)

    def on_generate_key(self, action=None, data=None):
        """Handle generate_key signal. See on_quit for parameters."""
        self.window.main_widget.generate_key()


def main(version):
    """
    Run application

    Parameters
    ----------
    version: str
        App version. Passed from badabib.in, defined in meson.build
    """
    app = Application(version)
    return app.run(argv)

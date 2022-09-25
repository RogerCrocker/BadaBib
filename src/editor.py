# editor.py
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

import badabib.forms

from gi.repository import Gtk

from .config_manager import field_dict

from .change import Change


class Editor(Gtk.ScrolledWindow):
    """
    A grid of labeled Gtk.Entry instances (forms) to edit BibTeX fields. The
    layout can be configured by the user - see layout_manager.py for more
    details.
    """
    def __init__(self, layout, entrytype=None):
        """
        layout: list of list of str
            Layout specification of the editor. Each element of layout is a list
            that specifies a row of forms. For example,
            [['author', 'year'], ['journal', 'volume']]
            corresponds to an editor with two rows and two forms in each row.
        entrytype: str, optional
            Entry type of the editor. Each entry type has its own editor. None
            if editor is in preview mode. The default value is None.
        """
        super().__init__()
        self.set_vexpand(True)
        self.app = Gtk.Application.get_default()

        # Add grid
        self.grid = Gtk.Grid()
        self.set_child(self.grid)

        # Entry type of editor
        self.entrytype = entrytype

        # State of the editor. Forms are deactivated if editor is inactive.
        self.active = True

        # Set to "False" to change displayed values without editing the
        # corresponding BibTeX entry
        self.track_changes = True

        # Dict {name: form}, containing all forms of the editor
        self.forms = {}

        # Current item and form
        self.current_item = None
        self.current_form = None

        # Apply layout
        self.set_spacings()
        self.apply_layout(layout)

        # Unless editor is in preview mode, connect forms and deactivate (no
        # entry has been selected yet)
        if entrytype:
            self.connect_forms()
            self.set_active(False)

    def set_spacings(self):
        """Set spacings of grid."""
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(5)
        self.grid.set_margin_top(10)
        self.grid.set_margin_bottom(10)
        self.grid.set_margin_start(10)
        self.grid.set_margin_end(10)

    def apply_layout(self, layout):
        """
        Create editor with specified layout.

        Parameters
        ----------
        layout: list of list of str
            See __init__ method and layout_manager.py for details
        """
        # Maximum number of forms. Note that since each form has a label.
        # the maximum number of grid columns is 2 * max_width.
        max_width = max([len(fields) for fields in layout])

        # Add forms to grid row-wise
        left = top = 0
        for fields in layout:
            # Choose width of forms uniformly
            width = max_width // len(fields)

            # Convert fields to forms and add to grid
            forms = self.fields_to_forms(fields)
            for field, form in zip(fields, forms):

                # Separator (line) spans all columns and has no label
                if field == "separator":
                    self.grid.attach(form, left, top, 2 * max_width, 1)
                    break

                # All other forms come with a label (=name of field)
                # The label always occupies one column
                label = Gtk.Label(label=field_dict[field])
                self.grid.attach(label, left, top, 1, 1)
                self.grid.attach(form, left+1, top, 2*width-1, 1)

                # Add form to editor
                self.forms[field] = form

                # Update current colum (2 * width columns were used for form + label)
                left += 2 * width

            # Reset counters for next row
            top += 1
            left = 0

    def fields_to_forms(self, fields):
        """
        Create a list of forms from a given list of fields.

        Parameters
        ----------
        fields: list of str
            Fields to create forms for

        Returns
        -------
        forms: list of forms
        """
        forms = []
        for field in fields:
            if field == "separator":
                form = badabib.forms.Separator()
            elif field == "ENTRYTYPE":
                form = badabib.forms.EntrytypeBox(field, self)
            elif field == "month":
                form = badabib.forms.MonthBox(field, self)
            elif field == "abstract":
                form = badabib.forms.MultiLine(field, self)
            else:
                form = badabib.forms.SingleLine(field, self)
            forms.append(form)
        return forms

    def connect_forms(self):
        """
        Connect forms to signals.

        changed signal: user changed field
        enter signal: Focus entered form
        leave signal: focus left form

        Changed signal connects to Gtk.Entry or Gtk.TextBuffer, enter and leave
        signal connect to form itself.
        """
        for field, form in self.forms.items():
            # Form is Gtk.Entry
            if field in badabib.forms.IS_ENTRY:
                form.connect("changed", self.update_item, form)
            # Form has a Gtk.Entry child
            if field in badabib.forms.HAS_ENTRY:
                entry = form.get_child()
                entry.connect("changed", self.update_item, form)
            # Forms has a Gtk.TextBuffer
            if field in badabib.forms.HAS_BUFFER:
                buffer = form.get_buffer()
                buffer.connect("changed", self.update_item, form)
            form.event_controller_focus.connect("enter", self.on_enter, form)
            form.event_controller_focus.connect("leave", self.on_leave, form)

    def show_item(self, item):
        """
        Show given item. That is, clear forms and refill with values of the
        selected item.

        Parameters
        ----------
        item: BadaBibItem
        """
        # Update current item
        self.current_item = item
        # Update forms
        for form in self.forms.values():
            form.update(item)

    def clear(self):
        """
        Clear all fields and disable editor. Called when no item is selected.
        """
        # Ignore "changed" signal while clearing forms
        self.track_changes = False
        for form in self.forms.values():
            form.clear()
        self.track_changes = True

        # Deativate editor
        self.set_active(False)

    def set_active(self, state):
        """
        Activate or deactivate editor. That is, set all forms to sensitive/
        insensitive.

        Parameters
        ----------
        state: bool
            True: active, False: inactive
        """
        # If state changed, update forms and state
        if self.active != state:
            for form in self.forms.values():
                form.set_sensitive(state)
            self.active = state

    def update_item(self, _widget, form):
        """
        Update the field of an entry based on the value of the given form. This
        function is called whenver the user edits a form.

        Parameters
        ----------
        _widget: Gtk.Widget, unused
            Widget emitting the "changed" signal. Class differes between forms,
            use "form" parameter instead for a more consistent interface.
        form: BadaBib.Form
            Form corresponding to the widget emitting the signal. Provides more
            uniform interface than working with _widget directly.
        """
        # Ignore changes if tracking is off
        if self.track_changes:
            # Get current value of changed field from entry
            item = self.current_item
            if form.field in item.entry:
                old_value = item.entry[form.field]
            else:
                old_value = ""

            # Get new value of changed field from form
            new_value = form.get_text()

            # catch empty Gtk.Entry to work around strange combobox behavior
            empty_entry = form.field in badabib.forms.HAS_ENTRY and not new_value

            # If value changed, apply change
            if not empty_entry and old_value != new_value:
                change = Change.Edit(item, form, old_value, new_value)
                item.bibfile.itemlist.change_buffer.push_change(change)

    def on_enter(self, _event_controller_focus, current_form):
        """
        Called when focus enters form. Updates current form, enables/disables
        context menu, deselects non-active forms and propagates signal.

        Parameters
        ----------
        _event_controller_focus: Gtk.EventControllerFocus, unused
            Gtk.EventControllerFocus emitting the signal
        current_form: BadaBib form
            Form that received focus
        """
        # Update current form
        self.current_form = current_form

        # Disable context menu if no form is focussed
        self.app.enable_menu_actions(current_form.get_text() != "")

        # Deselect all but the current form (GTK does not deselect automatically
        # when a Gtk.Entry loses focus)
        for form in self.forms.values():
            if form != current_form:
                form.deselect()

        # Propage signal
        return False

    def on_leave(self, _event_controller_focus, current_form):
        """
        Called when focus leaves form. Clears current form variable and
        propagates signal.

        Parameters
        ----------
        _event_controller_focus: Gtk.EventControllerFocus, unused
            Gtk.EventControllerFocus emitting the signal
        current_form: BadaBib form
            Form that received focus
        """
        self.current_form = None
        return False

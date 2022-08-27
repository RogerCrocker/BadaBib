# change.py
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


from time import time

from .config_manager import get_undo_delay


# Changes that are of the same type and happen within a window of UNDO_DELAY
# seconds are grouped into a single change
UNDO_DELAY = get_undo_delay()


class Change:
    """
    Change a BibTeX entry in a reversible manner. This is a container class that
    is instantiated via its inner classes: Edit, Show, Hide and Replace. Each
    inner class is a subclass of the Generic class and must implement an 'apply'
    and a 'revert' function.
    """
    class Generic:
        """
        Helper class that defines shortcuts to some useful objects. You do not
        want to instantiate this class, but one of its subclasses: Edit, Show,
        Hide and Replace.
        """
        @property
        def main_widget(self):
            window = self.item.row.get_root()
            return window.main_widget

        @property
        def editor(self):
            entrytype = self.item.raw_field("ENTRYTYPE")
            return self.main_widget.get_editor(entrytype)

        @property
        def bibfile(self):
            return self.item.bibfile

        @property
        def source_view(self):
            return self.main_widget.source_view

    class Edit(Generic):
        """Reversibly change an entry by editing a field in the editor."""
        def __init__(self, item, form, old_value, new_value):
            """
            Initialize Edit.

            Parameters
            ----------
            item: BadaBibItem
                Item that was edited
            form: BadaBibForm
                Form used to make the change
            old_value, new_value: str
            """
            self.type = "edit"
            self.item = item
            self.form = form
            self.old_value = old_value
            self.new_value = new_value

        def apply(self, redo=False):
            """
            Apply change to entry.

            Parameters
            ----------
            redo: bool, optional
                True if change is applied via redo action. The default value
                is False.
            """
            # If the change is invoked via redo action, the corresponding form
            # might not be focused.
            if redo:
                self.form.grab_focus()
            self.item.update_field(self.form.field, self.new_value, True)
            self.update_display(redo)

        def revert(self):
            """Revert change. Should only be invoked via redo action."""
            self.form.grab_focus()
            self.item.update_field(self.form.field, self.old_value, True)
            self.update_display(redo=True)

        def update_display(self, redo=False):
            """
            Update editor and itemlist.

            Parameters
            ----------
            redo: bool, optional
                True if change is applied via redo action. The default value
                is False.
            """
            self.item.row.update_field(self.form.field)     # Itemlist row
            self.source_view.update(self.item)              # Source view
            self.form.update(self.item)                     # Editor form
            if redo:
                self.bibfile.itemlist.unselect_all()
                self.bibfile.itemlist.select_row(self.item.row)
                self.main_widget.focus_on_current_item()

    class Show(Generic):
        """
        Create new items or undelete items. Can be applied to multiple
        items at once.
        """
        def __init__(self, items):
            """
            Initialize Show.

            Parameters
            ----------
            items: list of BadaBibItem
            """
            self.type = "show"
            self.item = items[0]    # Item that is highlighted after undo action
            self.form = None
            self.items = items

        def apply(self, redo=False):
            """Apply change, see Edit class for details on redo parameter."""
            # Undelete items
            for item in self.items:
                item.deleted = False

            # Re-apply filter to show new/undeleted items
            self.bibfile.itemlist.invalidate_filter()

            # Select all new/undeleted items
            self.bibfile.itemlist.unselect_all()
            for item in self.items:
                self.bibfile.itemlist.select_row(item.row)
            self.main_widget.focus_on_current_item()

        def revert(self):
            """Delete/hide item"""
            # Mark item as deleted
            for item in self.items:
                item.deleted = True

            # Re-apply filter to hide deleted items
            self.bibfile.itemlist.invalidate_filter()

            # Select item next to deleted one, or clear editor and source view
            self.bibfile.itemlist.unselect_all()
            next_row = self.bibfile.itemlist.select_next_row(self.item.row)
            if next_row:
                self.main_widget.focus_on_current_item()
            else:
                self.editor.clear()
                self.source_view.set_status("empty")

    class Hide(Show):
        """More explicit alias for Show.revert"""
        def apply(self, redo=False):
            super().revert()

        def revert(self):
            super().apply()

    class Replace(Generic):
        """
        Reversibly replace entry with another one. Invoked by directly editing
        the BibTeX source of an entry.
        """
        def __init__(self, item, old_entry, new_entry):
            """
            Initialize Replace.

            Parameters
            ----------
            item: BadaBibItem
                Item wrapping the entry that is replaced
            old_entry, new_entry: dict
            """
            self.type = "replace"
            self.item = item
            self.old_entry = old_entry
            self.new_entry = new_entry
            self.form = None

        def apply(self, redo=False):
            """Apply change. See Edit class for details on redo parameter."""
            self.item.update_entry(self.new_entry, True)    # Update entry
            self.item.row.update()                          # Update itemlist row
            self.editor.show_item(self.item)                # Show new item in editor
            if redo:
                # Update source view (only needed on redo, otherwise edited by
                # user) and select changed entry in itemlist.
                self.source_view.update(self.item)
                self.bibfile.itemlist.unselect_all()
                self.bibfile.itemlist.select_row(self.item.row)
                self.main_widget.focus_on_current_item()

        def revert(self):
            """Restore the previous entry."""
            # Update entry, editor, source view, selection and focus
            self.item.update_entry(self.old_entry, True)
            self.item.row.update()
            self.editor.show_item(self.item)
            self.source_view.update(self.item)
            self.bibfile.itemlist.unselect_all()
            self.bibfile.itemlist.select_row(self.item.row)
            self.main_widget.focus_on_current_item()


class ChangeBuffer:
    """Store, apply and revert changes."""
    def __init__(self):
        """Initialize Buffer."""
        self.buffer = [None]        # Indicate bottom of stack by None
        self.index = 0              # Index of last change
        self.saved_index = 0        # Index of last saved change
        self.last_save = time()     # Time of last save

    def update_saved_state(self):
        """Make current change the last saved one."""
        self.saved_index = self.index

    def truncate(self):
        """
        Discard all changes after the current one. Applied when user goes back
        several changes in the buffer and then adds a new change.
        """
        # Number of changes to be discarded
        n = len(self.buffer) - 1 - self.index

        # Check if last saved change is among those being discarded
        if self.saved_index > self.index:
            self.saved_index = -1

        # Discard all changes after the current one
        for _ in range(n):
            self.buffer.pop()

    def add_change(self, change):
        """
        Add new change to buffer.

        Parameters
        ----------
        change: Change
        """
        self.truncate()
        self.buffer.append(change)
        self.index += 1

    def push_change(self, change):
        """
        Apply change and add it to buffer. Combine with prior change if types
        match and both happened with UNDO_DELAY seconds.

        Parameters
        ----------
        change: Change
        """
        previous_change = self.buffer[self.index]

        # Combine edit with previous edit, if possible
        if (
            previous_change
            and previous_change.type == change.type == "edit"
            and previous_change.form == change.form
            and previous_change.item == change.item
            and time() - self.last_save < UNDO_DELAY
        ):
            previous_change.new_value = change.new_value
        # Combine replace with previous replace, if possible
        elif (
            previous_change
            and previous_change.type == change.type == "replace"
            and time() - self.last_save < UNDO_DELAY
        ):
            previous_change.new_entry = change.new_entry
        # Otherwise, add new change to buffer
        else:
            self.add_change(change)

        # Apply change, log time and indicate that the file has been modified
        change.apply()
        self.last_save = time()
        change.bibfile.set_unsaved(True)

    def redo_change(self):
        """Reapply a change. This function is invoked by the redo action."""
        # Check if there is a change left to redo
        if self.index < len(self.buffer) - 1:
            self.index += 1
            change = self.buffer[self.index]
            change.apply(redo=True)
            # Check if applying the change brings us to a saved state
            change.bibfile.set_unsaved(self.index != self.saved_index)
            # Highlight form and grab focus
            if change.form:
                change.form.select()
                change.form.grab_focus()

    def undo_change(self):
        """Revert a change. This function is invoked by the undo action."""
        # Check if there is a change to revert
        change = self.buffer[self.index]
        if change:
            self.index -= 1
            change.revert()
            # Check if applying the change brings us to a saved state
            change.bibfile.set_unsaved(self.index != self.saved_index)
            # Highlight form and grab focus
            if change.form:
                change.form.select()
                change.form.grab_focus()

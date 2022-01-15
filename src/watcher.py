# watcher.py
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

from gi.repository import Gtk, GLib

from time import sleep

from watchgod import DefaultWatcher
from watchgod import Change

from .config_manager import get_watcher_sleep_time

from .dialogs import FileChanged
from .dialogs import WarningDialog


WATCHER_SLEEP_TIME = get_watcher_sleep_time()


class Watcher:
    def __init__(self, window, filename):
        self.active = True
        self.window = window
        self.filename = filename
        self.sleep_time = WATCHER_SLEEP_TIME/1000

    def stop(self):
        self.active = False

    def watch_file(self):
        watcher = DefaultWatcher(self.filename)
        while self.active:
            changes = watcher.check()
            for change in changes:
                if change == (Change.deleted, self.filename):
                    self.file_deleted_or_moved()
                    self.active = False
                if change == (Change.modified, self.filename):
                    self.file_changed()
                    self.active = False
            sleep(self.sleep_time)

    def file_changed(self):
        dialog = FileChanged(self.window, self.filename)
        response = dialog.run()
        dialog.destroy()
        sleep(0.3)  # give dialog time to close
        if response == Gtk.ResponseType.YES:
            GLib.idle_add(self.window.main_widget.declare_file_created, self.filename)
        else:
            GLib.idle_add(self.window.main_widget.reload_file, self.filename)

    def file_deleted_or_moved(self):
        title = "Bada Bib! - File Deleted or Moved on Disk"
        message = (
            "It seems like the file '{}' was deleted, renamed, or moved.".format(self.filename)
            + "\n\n"
            + "You are now editing an unsaved copy of this file."
        )
        WarningDialog(message, title, self.window)
        sleep(0.3)  # give dialog time to close
        GLib.idle_add(self.window.main_widget.declare_file_created, self.filename)

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
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, GLib

from time import sleep

from watchgod import DefaultWatcher
from watchgod import Change

from .config_manager import get_watcher_sleep_time


WATCHER_SLEEP_TIME = get_watcher_sleep_time()


class Watcher:
    def __init__(self, main_widget, filename):
        self.active = True
        self.main_widget = main_widget
        self.filename = filename
        self.sleep_time = WATCHER_SLEEP_TIME/1000

    def stop(self):
        self.active = False

    def watch_file(self):
        watcher = DefaultWatcher(self.filename)
        while self.active:
            changes = watcher.check()
            for change in changes:
                if change[1] == self.filename:
                    self.active = False
                    GLib.idle_add(self.main_widget.declare_file_created, self.filename)
                    page = self.main_widget.itemlists[self.filename].page
                    if change[0] == Change.modified:
                        page.changed_bar.show_text(True)
                        page.changed_bar.set_revealed(True)
                    elif change[0] == Change.deleted:
                        page.deleted_bar.show_text(True)
                        page.deleted_bar.set_revealed(True)

            sleep(self.sleep_time)

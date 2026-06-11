# main.py
#
# Copyright 2026 Lluciocc
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ruff: noqa: E402

import sys
import gi

from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import ShapeboundWindow
from .progress import clear_progress


class ShapeboundApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.Lluciocc.Shapebound',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/io/github/Lluciocc/Shapebound')
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action, ['F1'])
        self.create_action('shortcuts', self.on_shortcuts_action, ['<control>question'])
        self.create_action('clear-progress', self.on_clear_progress_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = ShapeboundWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Shapebound',
                                application_icon='io.github.Lluciocc.Shapebound',
                                developer_name='Lluciocc',
                                version='0.1.0',
                                # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
                                translator_credits = _('translator-credits'),
                                developers=['Lluciocc'],
                                copyright='© 2026 Lluciocc',
                                license_type=Gtk.License.GPL_3_0,
                                website='https://github.com/Lluciocc/Shapebound',
                                )
        about.present(self.props.active_window)

    def on_shortcuts_action(self, *args):
        builder = Gtk.Builder.new_from_resource(
            '/io/github/Lluciocc/Shapebound/shortcuts-dialog.ui'
        )

        dialog = builder.get_object('shortcuts_dialog')
        dialog.set_transient_for(self.props.active_window)
        dialog.set_modal(True)
        dialog.present()

    def on_clear_progress_action(self, *args):
        dialog = Adw.MessageDialog(
            transient_for=self.props.active_window,
            heading="Clear Progress?",
            body="This will permanently remove all saved progress."
        )

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("clear", "Clear Progress")

        dialog.set_response_appearance(
            "clear",
            Adw.ResponseAppearance.DESTRUCTIVE
        )

        dialog.connect("response", self._on_clear_progress_response)
        dialog.present()

    def _on_clear_progress_response(self, dialog, response):
        if response != "clear":
            return

        clear_progress()

        win = self.props.active_window

        if win:
            win.build_campaign_page()

        toast = Adw.Toast(title="Progress cleared")
        overlay = getattr(win, "toast_overlay", None)

        if overlay:
            overlay.add_toast(toast)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = ShapeboundApplication()
    return app.run(sys.argv)

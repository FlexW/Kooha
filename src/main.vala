/* main.vala
 *
 * Copyright 2021 SeaDve
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

namespace Kooha {
    class Application : Gtk.Application {
        public static Window? win = null;
        public static GLib.Settings settings;

        public Application () {
            Object (
                flags: ApplicationFlags.FLAGS_NONE,
                application_id: "io.github.seadve.Kooha"
            );
        }

        static construct {
            settings = new GLib.Settings ("io.github.seadve.Kooha");
        }

        protected override void activate () {
            Adw.init ();

            var css_provider = new Gtk.CssProvider ();
            css_provider.load_from_resource ("/io/github/seadve/Kooha/ui/style.css");
            Gtk.StyleContext.add_provider_for_display (
                (!) Gdk.Display.get_default (),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            );

            if (win == null) {
                win = new Window (this);
            }
            ((!) win).present ();
        }

        public static int main (string[] args) {
            var app = new Kooha.Application ();
            return app.run (args);
        }
    }
}

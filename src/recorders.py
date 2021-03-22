# recorders.py
#
# Copyright 2021 SeaDve
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

from os.path import splitext
from subprocess import PIPE, Popen

from gi.repository import GLib, Gio, Gst


class Encoder:
    @staticmethod
    def get_multiplexer(frmt):
        multiplexers = {".webm":"webmmux", ".mkv":"matroskamux", ".mp4":"mp4mux"}
        return multiplexers[frmt]

    @staticmethod
    def get_coders(frmt):
        if frmt in [".webm", ".mkv"]:
            video_encoder = "vp8enc min_quantizer=10 max_quantizer=10 cpu-used=3 cq_level=13 deadline=1 static-threshold=100 threads=3 ! queue !"
            video_decoder = "matroskademux ! vp8dec ! queue ! vp8enc min_quantizer=10 max_quantizer=10 cpu-used=16 cq_level=13 deadline=1 static-threshold=100 threads=3 ! queue ! mux."
        elif frmt == ".mp4":
            video_encoder = "x264enc qp-min=17 qp-max=17 speed-preset=1 threads=3 ! queue !"
            video_decoder = "qtdemux ! avdec_h264 ! queue ! x264enc qp-min=17 qp-max=17 speed-preset=1 threads=3 ! queue ! mux."
        audio_encoder = "opusenc ! webmmux !"
        audio_decoder = "matroskademux ! mux."
        return(video_encoder, video_decoder)


class AudioRecorder:
    def __init__(self, saving_location, record_audio, record_microphone):
        self.saving_location = saving_location.replace(" ", "\ ")
        self.record_audio = record_audio
        self.record_microphone = record_microphone

        self.default_audio_output, self.default_audio_input = self.get_default_audio_devices()
        print(f"Default sink: {self.default_audio_output} \nDefault source: {self.default_audio_input}")

    def start(self):
        if (self.record_audio and self.default_audio_output) or (self.record_microphone and self.default_audio_input):

            # For setting up the pipeline
            frmt = splitext(self.saving_location)[1]
            self.video_encoder, self.video_decoder = Encoder.get_coders(frmt)
            self.multiplexer = Encoder.get_multiplexer(frmt)

            if self.record_audio and self.default_audio_output:
                audio_pipeline = f'pulsesrc device="{self.default_audio_output}" ! audioconvert ! opusenc ! webmmux ! filesink location={self.get_tmp_dir("audio")}'

            elif self.record_microphone and self.default_audio_input:
                audio_pipeline = f'pulsesrc device="{self.default_audio_input}" ! audioconvert ! opusenc ! webmmux ! filesink location={self.get_tmp_dir("audio")}'

            if (self.record_audio and self.default_audio_output) and (self.record_microphone and self.default_audio_input):
                audio_pipeline = f'pulsesrc device="{self.default_audio_output}" ! audiomixer name=mix ! audioconvert ! opusenc ! webmmux ! filesink location={self.get_tmp_dir("audio")} pulsesrc device="{self.default_audio_input}" ! queue ! mix.'

            self.audio_gst = Gst.parse_launch(audio_pipeline)
            bus = self.audio_gst.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_audio_gst_message)
            self.audio_gst.set_state(Gst.State.PLAYING)

    def stop(self):
        if (self.record_audio and self.default_audio_output) or (self.record_microphone and self.default_audio_input):
            self.audio_gst.set_state(Gst.State.NULL)

            print(f'{self.multiplexer} name=mux ! filesink location={self.saving_location} filesrc location={self.get_tmp_dir("video")} ! {self.video_decoder} filesrc location={self.get_tmp_dir("audio")} ! matroskademux ! mux.')
            self.joiner_gst = Gst.parse_launch(f'{self.multiplexer} name=mux ! filesink location={self.saving_location} filesrc location={self.get_tmp_dir("video")} ! {self.video_decoder} filesrc location={self.get_tmp_dir("audio")} ! matroskademux ! mux.')
            bus = self.joiner_gst.get_bus()
            bus.add_signal_watch()
            bus.connect('message', self.on_joiner_gst_message)
            self.joiner_gst.set_state(Gst.State.PLAYING)

    def on_joiner_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.joiner_gst.set_state(Gst.State.NULL)
            print("Done Processing")
        elif t == Gst.MessageType.ERROR:
            self.joiner_gst.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)

    def on_audio_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.audio_gst.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            self.audio_gst.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("audio_gst Error: %s" % err, debug)

    def get_encoder(self):
        pass

    @staticmethod
    def get_default_audio_devices():
        pactl_output = Popen(f'pactl info | grep Default | tail -n +3 | cut -d" " -f3', shell=True, text=True, stdout=PIPE).stdout.read().rstrip()
        device_list = pactl_output.split("\n")
        default_sink = f"{device_list[0]}.monitor"
        default_source = device_list[1]
        if default_sink == default_source:
            return (default_sink, None)
        return (default_sink, default_source)

    @staticmethod
    def get_tmp_dir(media_type):
        if media_type == "audio":
            extension = ".ogg"
        elif media_type == "video":
            extension = ".mkv"
        directory = GLib.getenv('XDG_CACHE_HOME')
        if not directory:
            directory = ""
        return f"{directory}/tmp/tmp{media_type}{extension}"


class VideoRecorder:
    def __init__(self, stack, label):
        self.stack = stack
        self.fullscreen_mode_label = label

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.GNOMEScreencast = Gio.DBusProxy.new_sync(
                    bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    "org.gnome.Shell.Screencast",
                    "/org/gnome/Shell/Screencast",
                    "org.gnome.Shell.Screencast",
                    None)

        self.GNOMESelectArea = Gio.DBusProxy.new_sync(
                    bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    "org.gnome.Shell.Screenshot",
                    "/org/gnome/Shell/Screenshot",
                    "org.gnome.Shell.Screenshot",
                    None)


    def start(self, directory, framerate, show_pointer):
        self.directory = directory
        self.framerate = framerate
        self.show_pointer = show_pointer

        # For setting up the pipeline
        frmt = splitext(self.directory)[1]
        self.video_encoder, self.video_decoder = Encoder.get_coders(frmt)
        self.multiplexer = Encoder.get_multiplexer(frmt)
        self.pipeline = f"{self.video_encoder} {self.multiplexer}"

        if self.stack.get_visible_child() is self.fullscreen_mode_label:
            self.GNOMEScreencast.call_sync(
                        "Screencast",
                        GLib.Variant.new_tuple(
                            GLib.Variant.new_string(self.directory),
                            GLib.Variant("a{sv}",
                                {"framerate": GLib.Variant("i", self.framerate),
                                 "draw-cursor": GLib.Variant("b", self.show_pointer),
                                 "pipeline": GLib.Variant("s", self.pipeline)}
                            ),
                        ),
                        Gio.DBusProxyFlags.NONE,
                        -1,
                        None)

        elif self.stack.get_visible_child() is not self.fullscreen_mode_label:
            self.GNOMEScreencast.call_sync(
                    "ScreencastArea",
                    GLib.Variant.new_tuple(
                        GLib.Variant("i", self.coordinates[0]),
                        GLib.Variant("i", self.coordinates[1]),
                        GLib.Variant("i", self.coordinates[2]),
                        GLib.Variant("i", self.coordinates[3]),
                        GLib.Variant.new_string(self.directory),
                        GLib.Variant("a{sv}",
                            {"framerate": GLib.Variant("i", self.framerate),
                             "draw-cursor": GLib.Variant("b", self.show_pointer),
                             "pipeline": GLib.Variant("s", self.pipeline)}
                        ),
                    ),
                    Gio.DBusProxyFlags.NONE,
                    -1,
                    None)

    def stop(self):
        self.GNOMEScreencast.call_sync(
            "StopScreencast",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None)

    def get_coordinates(self):
        self.coordinates = self.GNOMESelectArea.call_sync("SelectArea", None, Gio.DBusProxyFlags.NONE, -1, None)

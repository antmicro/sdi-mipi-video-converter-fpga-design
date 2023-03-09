# Copyright 2023 Antmicro <www.antmicro.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from migen import *
from migen.fhdl import verilog
from migen.fhdl.module import Module

from aligner import Aligner
from detector import DetectTRS
from timing_gen import create_timing_generator
from common import UnsupportedVideoFormatException

__all__ = ["SDI2MIPI"]


class SDI2MIPI(Module):
    supported_video_formats = ["720p60", "1080p30", "1080p60"]

    def __init__(self, video_format="720p60", four_lanes=False, pattern_gen=False):
        if video_format not in self.supported_video_formats:
            raise UnsupportedVideoFormatException(self.supported_video_formats)

        self.vsync_i = Signal(name="vsync_i")
        self.hsync_i = Signal(name="hsync_i")
        self.data_o = Signal(16, name="data_o")
        self.fv_o = Signal(name="fv_o")
        self.lv_o = Signal(name="lv_o")

        self.ios = {
            self.vsync_i,
            self.hsync_i,
            self.data_o,
            self.fv_o,
            self.lv_o,
        }

        timing_generator = create_timing_generator(
            video_format, four_lanes, pattern_gen
        )
        self.submodules.timing_gen = timing_generator
        self.comb += [
            self.fv_o.eq(self.timing_gen.fv_o),
            self.lv_o.eq(self.timing_gen.lv_o),
        ]

        if pattern_gen:
            self.comb += self.data_o.eq(self.timing_gen.data_o)
        else:
            self.comb += [
                self.timing_gen.vsync_i.eq(self.vsync_i),
                self.timing_gen.hsync_i.eq(self.hsync_i),
            ]

        if video_format == "720p60" and not pattern_gen:
            n_align = Signal()
            detector_rst = Signal()

            self.submodules.detector = DetectTRS()
            self.comb += [
                self.detector.pix.clk.eq(ClockSignal()),
                self.detector.pix.rst.eq(ResetSignal()),
                self.detector.det.clk.eq(ClockSignal()),
                self.detector.det.rst.eq(detector_rst),
                self.detector.lv_i.eq(self.lv_o),
                n_align.eq(self.detector.n_align_o),
            ]

            self.submodules.aligner = Aligner()
            self.comb += [
                self.aligner.n_align_i.eq(n_align),
                detector_rst.eq(self.aligner.detector_rst_o),
            ]


if __name__ == "__main__":
    sdi_mipi = SDI2MIPI()
    print(verilog.convert(sdi_mipi, sdi_mipi.ios, name="sdi2mipi"))

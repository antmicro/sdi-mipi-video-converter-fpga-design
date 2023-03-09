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
from migen.fhdl.verilog import convert
from common import UnsupportedVideoFormatException


def create_timing_generator(video_format="720p60", four_lanes=False, pattern_gen=False):
    if pattern_gen:
        return PatternGenerator(video_format)

    if video_format == "720p60":
        if four_lanes:
            return TimingGenerator_720p60_4lanes()
        else:
            return TimingGenerator_720p60_2lanes()

    elif video_format == "1080p30":
        return TimingGenerator_1080p30()

    elif video_format == "1080p60":
        return TimingGenerator_1080p60()

    else:
        assert False


def get_timings(video_format):
    def calc_h_total(timings):
        return (
            timings["H_ACTIVE"]
            + timings["H_SYNC"]
            + timings["H_BACK_PORCH"]
            + timings["H_FRONT_PORCH"]
        )

    def calc_v_total(timings):
        return (
            timings["V_ACTIVE"]
            + timings["V_SYNC"]
            + timings["V_BACK_PORCH"]
            + timings["V_FRONT_PORCH"]
        )

    timings = {
        "720p60": {
            "H_ACTIVE": 1280,
            "H_BACK_PORCH": 220,
            "H_SYNC": 40,
            "H_FRONT_PORCH": 110,
            "V_ACTIVE": 720,
            "V_BACK_PORCH": 20,
            "V_SYNC": 5,
            "V_FRONT_PORCH": 5,
        },
        "1080p60": {
            "H_ACTIVE": 1920,
            "H_BACK_PORCH": 148,
            "H_SYNC": 44,
            "H_FRONT_PORCH": 88,
            "V_ACTIVE": 1080,
            "V_BACK_PORCH": 36,
            "V_SYNC": 5,
            "V_FRONT_PORCH": 4,
        },
        "1080p30": {
            "H_ACTIVE": 1920,
            "H_BACK_PORCH": 148,
            "H_SYNC": 44,
            "H_FRONT_PORCH": 88,
            "V_ACTIVE": 1080,
            "V_BACK_PORCH": 36,
            "V_SYNC": 5,
            "V_FRONT_PORCH": 4,
        },
    }

    if video_format not in timings.keys():
        raise UnsupportedVideoFormatException(timings.keys())

    ret = timings[video_format]
    ret.update({"H_TOTAL": calc_h_total(ret)})
    ret.update({"V_TOTAL": calc_v_total(ret)})

    return ret


class TimingGenerator(Module):
    """
    Common interface and logic for all different variants of timing
    generators.
    """

    def __init__(self, timings, V_SYNC_DELAY=0):
        # VESA timing parameters
        self.H_ACTIVE       = timings["H_ACTIVE"]
        self.H_TOTAL        = timings["H_TOTAL"]
        self.V_ACTIVE       = timings["V_ACTIVE"]
        self.V_TOTAL        = timings["V_TOTAL"]
        self.H_SYNC         = timings["H_SYNC"]
        self.H_BACK_PORCH   = timings["H_BACK_PORCH"]
        self.H_FRONT_PORCH  = timings["H_FRONT_PORCH"]
        self.V_SYNC         = timings["V_SYNC"]
        self.V_BACK_PORCH   = timings["V_BACK_PORCH"]
        self.V_FRONT_PORCH  = timings["V_FRONT_PORCH"]

        self.H_BLANKING = self.H_BACK_PORCH + self.H_FRONT_PORCH + self.H_SYNC
        self.V_SYNC_START = self.V_ACTIVE + self.V_FRONT_PORCH + V_SYNC_DELAY

        # Inputs
        self.vsync_i = Signal()
        self.hsync_i = Signal()

        # Outputs
        self.fv_o = Signal()
        self.lv_o = Signal()

        # Input/Output list for correct module generation
        self.ios = {
            self.vsync_i,
            self.hsync_i,
            self.fv_o,
            self.lv_o,
        }

        self.vsync_r = Signal()
        self.vsync_rr = Signal()
        self.hsync_r = Signal()
        self.hsync_rr = Signal()
        self.fv_c = Signal()
        self.lv_c = Signal()
        self.lv_r = Signal()
        self.pixcnt_c = Signal(12)
        self.pixcnt_r = Signal(12)
        self.linecnt_c = Signal(12)
        self.linecnt_r = Signal(12)

        self.sync += [
            self.vsync_r.eq(self.vsync_i),
            self.vsync_rr.eq(self.vsync_r),
            self.hsync_r.eq(self.hsync_i),
            self.hsync_rr.eq(self.hsync_r),
            self.pixcnt_r.eq(self.pixcnt_c),
            self.linecnt_r.eq(self.linecnt_c),
        ]

        # Line_valid generation
        self.comb += self.lv_c.eq(
            (self.pixcnt_r > 0) & (self.pixcnt_r <= self.H_ACTIVE)
        )

        # Line counter
        self.comb += [
            If(self.vsync_r & ~self.vsync_rr,
                self.linecnt_c.eq(self.V_SYNC_START)
            ).Elif((self.linecnt_r < self.V_TOTAL) & (self.pixcnt_r == 1),
                self.linecnt_c.eq(self.linecnt_r + 1),
            ).Elif((self.linecnt_r == self.V_TOTAL) & (self.pixcnt_r == 1),
                self.linecnt_c.eq(1)
            ).Else(
                self.linecnt_c.eq(self.linecnt_r)
            )
        ]


class TimingGenerator_720p60(TimingGenerator):
    """
    Common interface and logic for all different variants of timing
    generators.
    """

    def __init__(self, V_SYNC_DELAY=0, H_SYNC_DELAY=0):
        timings = get_timings("720p60")
        super().__init__(timings, V_SYNC_DELAY)
        self.fv_extend_cnt_c = Signal(10)
        self.fv_extend_cnt_r = Signal(10)

        # Helper variables
        H_SYNC_START = self.H_ACTIVE + self.H_FRONT_PORCH + H_SYNC_DELAY + 1

        # Signals controled in pixel clock domain
        self.sync += [
            self.fv_o.eq(self.fv_c),
            self.lv_r.eq(self.lv_c),
            self.fv_extend_cnt_r.eq(self.fv_extend_cnt_c),
        ]

        # Pixel counter
        self.comb += [
            If(self.hsync_r & ~self.hsync_rr,
                self.pixcnt_c.eq(H_SYNC_START),
            ).Else(
                If(self.pixcnt_r < self.H_TOTAL,
                    self.pixcnt_c.eq(self.pixcnt_r + 1)
                ).Else(
                    self.pixcnt_c.eq(1)
                )
            )
        ]

        # Extend frame_valid signal by one horizontal blanking period
        self.comb += [
            If((self.linecnt_r == self.V_TOTAL) & (self.pixcnt_r >= self.H_ACTIVE),
                self.fv_extend_cnt_c.eq(self.fv_extend_cnt_r + 1),
            ).Else(
                self.fv_extend_cnt_c.eq(0)
            )
        ]


class TimingGenerator_720p60_2lanes(TimingGenerator_720p60):
    """
    A module responsible for generating VESA-compliant video timings
    for 720p60 resolution in 2 lanes mode
    """

    def __init__(self):
        super().__init__(V_SYNC_DELAY=1)

        # Signals controled in pixel clock domain
        self.sync += self.lv_o.eq((self.lv_r) & self.fv_o)

        # Frame_valid generation
        self.comb += self.fv_c.eq(
            (self.linecnt_r > 0) & (self.linecnt_r <= self.V_ACTIVE)
            | ((self.fv_extend_cnt_r > 0))
        )


class TimingGenerator_720p60_4lanes(TimingGenerator_720p60):
    """
    A module responsible for generating VESA-compliant video timings
    for 720p60 resolution in 4 lanes mode
    """

    def __init__(self):
        super().__init__(V_SYNC_DELAY=0, H_SYNC_DELAY=5)

        self.fv_r = Signal()

        # Signals controled in pixel clock domain
        self.sync += [
            self.fv_r.eq(self.fv_c),
            self.lv_o.eq((self.lv_r) & self.fv_r),
        ]

        # Frame_valid generation
        self.comb += self.fv_c.eq(
            (
                (self.linecnt_r > 0)
                & (self.linecnt_r <= self.V_ACTIVE)
                & ~((self.linecnt_r == self.V_ACTIVE) & (self.pixcnt_r == 1))
            )
            | (self.fv_extend_cnt_r > 0)
        )


class TimingGenerator_1080p60(TimingGenerator):
    """
    A module responsible for generating VESA-compliant video timings
    for 1080p60 resolutions
    """

    def __init__(self):
        timings = get_timings("1080p60")
        super().__init__(timings)

        # Pixel clock cycles lost due to 3 levels of synchronous logic
        HSYNC_DELAY = 3
        # Pixel clock cycles to align video lines horizontally
        HSYNC_ALIGN = 4
        # Helper variables
        H_SYNC_START = self.H_ACTIVE + self.H_FRONT_PORCH + HSYNC_DELAY
        H_SYNC_START_ALIGNED = H_SYNC_START + HSYNC_ALIGN

        self.fv_r = Signal()

        # Signals controled in pixel clock domain
        self.sync += [
            self.fv_r.eq(self.fv_c),
            self.fv_o.eq(self.fv_r),
            self.lv_r.eq(self.lv_c),
            self.lv_o.eq((self.lv_r) & self.fv_r),
        ]

        # Pixel counter
        self.comb += [
            If(self.hsync_r & ~self.hsync_rr,
                self.pixcnt_c.eq(H_SYNC_START_ALIGNED),
            ).Else(
                If(self.pixcnt_r < self.H_TOTAL,
                    self.pixcnt_c.eq(self.pixcnt_r + 1)
                ).Else(
                    self.pixcnt_c.eq(1)
                )
            )
        ]

        # Frame_valid generation
        self.comb += self.fv_c.eq(
            (
                (self.linecnt_r > 0)
                & (self.linecnt_r <= self.V_ACTIVE)
                & ~((self.linecnt_r == self.V_ACTIVE) & (self.pixcnt_r > H_SYNC_START))
                & ~((self.linecnt_r == self.V_ACTIVE) & (self.pixcnt_r == 1))
            )
            | (
                (self.linecnt_r == self.V_TOTAL)
                & ((self.pixcnt_r > H_SYNC_START) | (self.pixcnt_r == 1))
            )
        )


class TimingGenerator_1080p30(TimingGenerator):
    """
    A module responsible for generating VESA-compliant video timings
    for 1080p30 resolutions
    """

    def __init__(self):
        timings = get_timings("1080p30")
        super().__init__(timings, V_SYNC_DELAY=1)

        self.fv_extend_cnt_c = Signal(10)
        self.fv_extend_cnt_r = Signal(10)

        # Signals controled in pixel clock domain
        self.sync += [
            self.fv_o.eq(self.fv_c),
            self.lv_r.eq(self.lv_c),
            self.lv_o.eq((self.lv_r) & self.fv_o),
            self.fv_extend_cnt_r.eq(self.fv_extend_cnt_c),
        ]

        # Pixel counter
        self.comb += [
            If(self.hsync_r & ~self.hsync_rr,
                self.pixcnt_c.eq(self.H_ACTIVE + self.H_FRONT_PORCH + 1),
            ).Else(
                If(self.pixcnt_r < self.H_TOTAL,
                    self.pixcnt_c.eq(self.pixcnt_r + 1)
                ).Else(
                    self.pixcnt_c.eq(1)
                )
            )
        ]

        # Frame_valid generation
        self.comb += self.fv_c.eq(
            (self.linecnt_r > 0) & (self.linecnt_r <= self.V_ACTIVE)
            | ((self.fv_extend_cnt_r > 0))
        )

        # Extend frame_valid signal by one horizontal blanking period
        self.comb += [
            If((self.linecnt_r == self.V_TOTAL) & (self.pixcnt_r >= self.H_ACTIVE),
                self.fv_extend_cnt_c.eq(self.fv_extend_cnt_r + 1),
            ).Else(
                self.fv_extend_cnt_c.eq(0)
            )
        ]


class PatternGenerator(Module):
    """
    Pattern generator that produces 6 vertical stripes in different colors.
    """

    def __init__(self, video_format="1080p60"):
        # VESA timing parameters
        timings = get_timings(video_format)
        # fmt: off
        self.H_ACTIVE       = timings["H_ACTIVE"]
        self.H_TOTAL        = timings["H_TOTAL"]
        self.V_ACTIVE       = timings["V_ACTIVE"]
        self.V_TOTAL        = timings["V_TOTAL"]
        self.H_SYNC         = timings["H_SYNC"]
        self.H_BACK_PORCH   = timings["H_BACK_PORCH"]
        self.H_FRONT_PORCH  = timings["H_FRONT_PORCH"]
        self.V_SYNC         = timings["V_SYNC"]
        self.V_BACK_PORCH   = timings["V_BACK_PORCH"]
        self.V_FRONT_PORCH  = timings["V_FRONT_PORCH"]
        # fmt: on

        # Outputs
        self.fv_o = Signal()
        self.lv_o = Signal()
        self.data_o = Signal(16)
        self.pixcnt = Signal(12)
        self.linecnt = Signal(12)

        # Input/Output list for correct module generation
        self.ios = {
            self.fv_o,
            self.lv_o,
            self.data_o,
            self.linecnt,
            self.pixcnt,
        }

        fv = Signal()
        lv = Signal()
        self.yuv_cnt_d = Signal(3)
        self.linecnt_d = Signal(12)

        self.sync += self.linecnt_d.eq(self.linecnt)
        self.sync += [
            self.fv_o.eq(fv),
            self.lv_o.eq(lv),
        ]

        # Count all lines in a frame
        # fmt: off
        self.sync += [
            If(self.linecnt == self.V_TOTAL,
                self.linecnt.eq(0),
            ).Elif(self.pixcnt == self.H_TOTAL,
                self.linecnt.eq(self.linecnt + 1),
            )
        ]

        # Count all cycles in a line
        self.sync += [
            If(self.pixcnt == self.H_TOTAL,
                self.pixcnt.eq(1),
            ).Else(
                self.pixcnt.eq(self.pixcnt + 1),
            )
        ]

        # Frame valid
        self.comb += [
            If((self.linecnt >= (self.V_SYNC + self.V_BACK_PORCH))
             & (self.linecnt < (self.V_TOTAL - self.V_FRONT_PORCH)),
                fv.eq(1)
            ).Else(
                fv.eq(0)
            )
        ]
        # fmt: on

        # Line valid
        self.comb += lv.eq(
            fv
            & (self.pixcnt >= (self.H_SYNC + self.H_BACK_PORCH))
            & (self.pixcnt < (self.H_TOTAL - self.H_FRONT_PORCH))
        )

        # Colors in YUV422 8-bit format
        # fmt: off
        #
        #          _-----------------------------> White
        #         /     _------------------------> Yellow
        #        |     /     _-------------------> Cyan
        #        |    |     /     _--------------> Red
        #        |    |    |     /     _---------> Blue
        #        |    |    |    |     /     _----> Black
        #        |    |    |    |    |     /
        #        |    |    |    |    |    |
        Y_VAL = [255, 219, 188, 76,  32,  0  ]
        U_VAL = [128, 0,   154, 84,  255, 128]
        V_VAL = [128, 138, 0,   255, 118, 128]
        # fmt: on
        Y = Signal(8)
        U = Signal(8)
        V = Signal(8)
        colors_len = len(Y_VAL)

        segment = self.H_ACTIVE // colors_len
        color_cnt_r = Signal(max=segment)
        color_r = Signal(max=colors_len)
        # fmt: off
        self.sync += [
            If(~lv,
                color_r.eq(0),
                color_cnt_r.eq(0),
            ).Else(
                color_cnt_r.eq(color_cnt_r + 1),
                If(color_cnt_r == segment - 1,
                    color_r.eq(color_r + 1),
                    color_cnt_r.eq(0),
                ),
            ),
        ]

        # Color iterator
        self.comb += [
            If(color_r == 0,
                Y.eq(Y_VAL[0]),
                U.eq(U_VAL[0]),
                V.eq(V_VAL[0]),
            ).Elif(color_r == 1,
                Y.eq(Y_VAL[1]),
                U.eq(U_VAL[1]),
                V.eq(V_VAL[1]),
            ).Elif(color_r == 2,
                Y.eq(Y_VAL[2]),
                U.eq(U_VAL[2]),
                V.eq(V_VAL[2]),
            ).Elif(color_r == 3,
                Y.eq(Y_VAL[3]),
                U.eq(U_VAL[3]),
                V.eq(V_VAL[3]),
            ).Elif(color_r == 4,
                Y.eq(Y_VAL[4]),
                U.eq(U_VAL[4]),
                V.eq(V_VAL[4]),
            ).Elif(color_r == 5,
                Y.eq(Y_VAL[5]),
                U.eq(U_VAL[5]),
                V.eq(V_VAL[5]),
            ),
        ]

        self.sync += [
            If (~lv,
                self.data_o.eq(0),
            ).Else(
                If(self.pixcnt & 1,
                    self.data_o.eq(Cat(V, Y)),
                ).Else(
                    self.data_o.eq(Cat(U, Y)),
                ),
            ),
        ]
        # fmt: on


if __name__ == "__main__":
    timing_gen = create_timing_generator()
    print(convert(timing_gen, timing_gen.ios, name="timings_gen"))

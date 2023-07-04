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


hv_timings = {
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
    "1080p50": {
        "H_ACTIVE": 1920,
        "H_BACK_PORCH": 148,
        "H_SYNC": 44,
        "H_FRONT_PORCH": 528,
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
    "1080p25": {
        "H_ACTIVE": 1920,
        "H_BACK_PORCH": 148,
        "H_SYNC": 44,
        "H_FRONT_PORCH": 528,
        "V_ACTIVE": 1080,
        "V_BACK_PORCH": 36,
        "V_SYNC": 5,
        "V_FRONT_PORCH": 4,
    },
}


class PatternGenerator(Module):
    """
    Pattern generator that produces 6 vertical stripes in different colors.
    """

    def __init__(self, video_format="1080p60"):
        # VESA timing parameters
        timings = hv_timings[video_format]
        self.H_ACTIVE       = timings["H_ACTIVE"]
        self.V_ACTIVE       = timings["V_ACTIVE"]
        self.H_SYNC         = timings["H_SYNC"]
        self.H_BACK_PORCH   = timings["H_BACK_PORCH"]
        self.H_FRONT_PORCH  = timings["H_FRONT_PORCH"]
        self.V_SYNC         = timings["V_SYNC"]
        self.V_BACK_PORCH   = timings["V_BACK_PORCH"]
        self.V_FRONT_PORCH  = timings["V_FRONT_PORCH"]
        self.H_TOTAL        = self.H_ACTIVE + self.H_SYNC + self.H_BACK_PORCH + self.H_FRONT_PORCH
        self.V_TOTAL        = self.V_ACTIVE + self.V_SYNC + self.V_BACK_PORCH + self.V_FRONT_PORCH

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

        # Line valid
        self.comb += lv.eq(
            fv
            & (self.pixcnt >= (self.H_SYNC + self.H_BACK_PORCH))
            & (self.pixcnt < (self.H_TOTAL - self.H_FRONT_PORCH))
        )

        # Colors in YUV422 8-bit format
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
        Y = Signal(8)
        U = Signal(8)
        V = Signal(8)
        colors_len = len(Y_VAL)

        segment = self.H_ACTIVE // colors_len
        color_cnt_r = Signal(max=segment)
        color_r = Signal(max=colors_len)
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


if __name__ == "__main__":
    pattern_gen = PatternGenerator()
    print(convert(pattern_gen, pattern_gen.ios, name="pattern_gen"))

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

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, ReadOnly
from cocotb.regression import TestFactory
from common import *
from common import reset_module

hv_timings = {
    "H_ACTIVE": 1920,
    "H_BLANK": 280,
    "V_ACTIVE": 1080,
    "V_BLANK": 45,
}

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
LINE_WIDTH = hv_timings["H_ACTIVE"]
FRAME_HEIGHT = hv_timings["V_ACTIVE"]
COLORS_LEN = len(Y_VAL)
COLOR_WIDTH = LINE_WIDTH // COLORS_LEN


async def check_single_line(dut):
    await ReadOnly()
    for i in range(LINE_WIDTH):
        assert dut.lv_o.value == 1, "Line valid is low during active time"
        golden_Y = Y_VAL[i // COLOR_WIDTH]
        golden_U = U_VAL[i // COLOR_WIDTH]
        golden_V = V_VAL[i // COLOR_WIDTH]

        await ReadOnly()
        if i % 2 == 0:
            assert dut.data_o.value == (golden_Y  << 8) | golden_U, "Pixel #{0} value is not correct".format(i)
        else:
            assert dut.data_o.value == (golden_Y  << 8) | golden_V, "Pixel #{0} value is not correct".format(i)
        await RisingEdge(dut.sys_clk)


async def measure_hblank(dut):
    for _ in range(hv_timings["H_BLANK"]):
        await ReadOnly()
        assert dut.lv_o.value == 0, "Line valid is high during blanking time"
        await RisingEdge(dut.sys_clk)


async def measure_vblank(dut):
    await FallingEdge(dut.fv_o)
    for _ in range(hv_timings["V_BLANK"] * (LINE_WIDTH + hv_timings["H_BLANK"])):
        await ReadOnly()
        assert dut.fv_o.value == 0, "Frame valid is high during blanking time"
        await RisingEdge(dut.sys_clk)

    await ReadOnly()
    assert dut.fv_o.value == 1, "Frame valid is low during active time"


async def test_pattern_gen(dut, clock_period):
    clk = dut.sys_clk
    dut_clk = Clock(clk, clock_period, "ps")
    cocotb.start_soon(dut_clk.start())
    await reset_module([dut.sys_rst], clk)

    # In the beginning of the frame delays are not important so just
    # wait for rising edge of fv and lv
    await RisingEdge(dut.fv_o)
    await RisingEdge(dut.lv_o)

    # Execute checks for a whole frame
    for _ in range(FRAME_HEIGHT):
        # Once lines are being generated, check pixel colors
        await check_single_line(dut)

        # Measure blanking time between lines
        await measure_hblank(dut)

    # Measure blanking time between frames
    await measure_vblank(dut)

    # Add delay to separate tests on waveforms
    await ClockCycles(dut.sys_clk, 100)


tf = TestFactory(test_function=test_pattern_gen)
tf.add_option(name="clock_period", optionlist=[PIX_CLK_74_25MHZ, PIX_CLK_148_5MHZ])
tf.generate_tests()

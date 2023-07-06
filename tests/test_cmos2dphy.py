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
from cocotb.triggers import ReadOnly, RisingEdge, ClockCycles
from cocotb.regression import TestFactory
from common import *
from common import reset_module

VC=0
DT=0x1e
WC=3840

def set_initial_values(dut):
    dut.fv_i.value = 0
    dut.lv_i.value = 0
    dut.pix_data0_i.value = 0
    dut.pix_data1_i.value = 0
    dut.vc_i.value = VC
    dut.dt_i.value = DT
    dut.wc_i.value = WC

async def lv_signal(lv, pix_clk, line_width):
    lv.value = 1
    for _ in range(line_width):
        await RisingEdge(pix_clk)
    lv.value = 0


async def check_short_packet(dut, dt):
    await RisingEdge(dut.txfr_req_o)
    await ReadOnly()
    assert dut.dphy_ready_o.value == 1, "HS mode requested when D-PHY is not ready"

    await RisingEdge(dut.d_hs_rdy_o)
    await RisingEdge(dut.byte_clk)
    await ReadOnly()
    assert dut.sp_en_o.value == 1, "Lack of short packet request while D-PHY is ready"
    assert dut.dt_o.value == dt, "Short packet - wrong data type"
    assert dut.wc_o.value == 0, "Short packet - wrong word count"

    await RisingEdge(dut.byte_clk)
    await ReadOnly()
    assert dut.sp_en_o.value == 0, "Short packet requested when D-PHY is not ready"

    await RisingEdge(dut.phdr_xfr_done_o)


async def frame_start(dut):
    dut.fv_i.value = 1
    dut.lv_i.value = 0
    dut.pix_data0_i.value = 0
    dut.pix_data1_i.value = 0
    await check_short_packet(dut, dt=0)


async def frame_end(dut):
    dut.fv_i.value = 0
    dut.lv_i.value = 0
    dut.pix_data0_i.value = 0
    dut.pix_data1_i.value = 0
    await check_short_packet(dut, dt=1)


async def do_xfr_line(dut, clock_period):
    lv_state = lv_signal(dut.lv_i, dut.sys_clk, WC // 2)
    cocotb.start_soon(lv_state)

    dut.pix_data0_i.value = 0xef
    dut.pix_data1_i.value = 0xbe
    await RisingEdge(dut.txfr_req_o)
    assert dut.dphy_ready_o.value == 1, "HS mode requested when D-PHY is not ready"

    await RisingEdge(dut.d_hs_rdy_o)
    await RisingEdge(dut.byte_clk)
    await ReadOnly()
    assert dut.lp_en_o.value == 1, "Lack of long packet request while D-PHY is ready"
    assert dut.dt_o.value == DT, "Long packet - wrong data type"
    assert dut.wc_o.value == WC, "Long packet - wrong word count"

    await RisingEdge(dut.byte_clk)
    await ReadOnly()
    assert dut.lp_en_o.value == 0, "Long packet requested when D-PHY is not ready"

    await RisingEdge(dut.phdr_xfr_done_o)


async def test_cmos2dphy(dut, clock_period, lines):
    pix_clk = dut.sys_clk
    pix_rst = dut.sys_rst
    byte_clk = dut.byte_clk
    byte_rst = dut.byte_rst
    dut_pix_clk = Clock(pix_clk, clock_period[0], "ps")
    dut_byte_clk = Clock(byte_clk, clock_period[1], "ps")
    cocotb.start_soon(dut_pix_clk.start())
    cocotb.start_soon(dut_byte_clk.start())

    set_initial_values(dut)
    await reset_module([pix_rst, byte_rst], pix_clk)

    # Wait for D-PHY to be ready
    await RisingEdge(dut.tinit_done_o)

    # Omit first few frames due to deserializer timing characteristics
    for _ in range(6):
        dut.fv_i.value = 1
        await ClockCycles(pix_clk, 5)
        dut.fv_i.value = 0
        await ClockCycles(pix_clk, 5)

    # Initiate frame transfer with a short packet
    await frame_start(dut)

    # Transmit full frame
    await ClockCycles(pix_clk, 280)
    for _ in range(lines):
        await do_xfr_line(dut, clock_period[0])
        await ClockCycles(pix_clk, 280)

    # Finish frame transfer
    await frame_end(dut)

    # Add a delay at the end
    await ClockCycles(pix_clk, 50)


tf = TestFactory(test_function=test_cmos2dphy)
tf.add_option(name="clock_period", optionlist=[
    (PIX_CLK_74_25MHZ, BYTE_CLK_74_25MHZ),
    (PIX_CLK_148_5MHZ, BYTE_CLK_148_5MHZ),
])
tf.add_option(name="lines", optionlist=[1, 1080])
tf.generate_tests()

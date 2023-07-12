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
from common import *
from common import bbb_line, bbb_line_crc, bbb_line_crc_trail
from common import reset_module, int2list, list2int, gen_ecc, HS_INIT_SEQ
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory


# Helper simulation functions -------------------------------------------------
async def check_packet_header(dut, dt, wc, vc=0):
    clk = dut.sys_clk

    # Test virtual channel 0 only
    dut.vc_i.value = vc
    # Short packets are always 0 words
    dut.wc_i.value = wc
    # Data type should be set for a whole time
    dut.dt_i.value = dt

    # Data should be set to init sequence at the next rising edge
    await RisingEdge(clk)
    dut.sp_en_i.value = 0
    dut.lp_en_i.value = 0
    assert dut.data_o.value == (HS_INIT_SEQ << 16) | HS_INIT_SEQ, "Initialization sequence error"

    # 1st word after init is dt and wc
    await RisingEdge(clk)
    ecc = gen_ecc((wc << 8) | dt)
    header = (ecc << 24) | ((wc >> 8) & 0xff) << 16 | (((wc & 0xff) << 8) | (dt & 0xff)) & 0xffff
    assert dut.data_o.value == header, "Packet header error"


async def check_eot(dut, last_word):
    clk = dut.sys_clk
    await RisingEdge(clk)

    lw = int2list(last_word)
    trail = []
    trail.append([(1 if ~lw[7] else 0) for _ in range(8)])
    trail.append([(1 if ~lw[15] else 0) for _ in range(8)])
    trail.append([(1 if ~lw[23] else 0) for _ in range(8)])
    trail.append([(1 if ~lw[-1] else 0) for _ in range(8)])
    trail = list2int(trail[0]) + (list2int(trail[1]) << 8) \
            | (list2int(trail[2]) << 16) | (list2int(trail[3]) << 24)

    assert dut.data_o.value == trail, "Wrong HS-Trail value"


# Tests -----------------------------------------------------------------------
async def test_short_packet(dut, dt, clock_period):
    clk = dut.sys_clk
    dut_clk = Clock(clk, clock_period, "ps")
    cocotb.start_soon(dut_clk.start())
    await reset_module([dut.sys_rst], clk)

    # Request short packet transfer
    dut.sp_en_i.value = 1

    ecc = gen_ecc(dt)
    last_word = (ecc << 24) | (dt & 0xff) & 0xffff
    await check_packet_header(dut, dt, 0)
    await check_eot(dut, last_word)

    # Inititate init sequence
    await RisingEdge(clk)


async def test_long_packet(dut, dt, clock_period, line_test_case):
    clk = dut.sys_clk
    dut_clk = Clock(clk, clock_period, "ps")
    cocotb.start_soon(dut_clk.start())
    await reset_module([dut.sys_rst], clk)
    wc = 3840

    if line_test_case == "bbb_1":
        test_case = (bbb_line, bbb_line_crc, bbb_line_crc_trail)
    data = test_case[0]
    crc = test_case[1]
    trail = test_case[2]

    # Request long packet transfer
    dut.lp_en_i.value = 1

    await check_packet_header(dut, dt, wc)
    for i in range(wc // 4):
        dut.byte_data_i.value = data[i]
        await RisingEdge(clk)

    dut.crc_i.value = crc
    await RisingEdge(clk)
    assert dut.data_o.value == crc | (0xffff << 16), "Packet footer error (CRC)"
    await check_eot(dut, crc | (0xffff << 16))


tf_sp = TestFactory(test_function=test_short_packet)
tf_sp.add_option(name="clock_period", optionlist=[BYTE_CLK_74_25MHZ, BYTE_CLK_37_125MHZ])
tf_sp.add_option(name="dt", optionlist=[0, 1])
tf_sp.generate_tests()

tf_lp = TestFactory(test_function=test_long_packet)
tf_lp.add_option(name="clock_period", optionlist=[BYTE_CLK_74_25MHZ, BYTE_CLK_37_125MHZ])
tf_lp.add_option(name="dt", optionlist=[0x1e])
tf_lp.add_option(name="line_test_case", optionlist=["bbb_1"])
tf_lp.generate_tests()

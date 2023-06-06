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
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles
from cocotb.regression import TestFactory
from common import *
from common import reset_module


def set_initial_values(dut):
    dut.byte_rst.value = 0
    dut.byte_or_pkt_data_en_i.value = 0
    dut.byte_or_pkt_data_i.value = 0

def assert_stop_state(dut):
    assert dut.dphy_ready_o.value == 1
    assert dut.d_hs_rdy_o.value == 0
    assert dut.lp_tx_data_en_o.value == 1
    assert dut.lp_tx_data_p_o.value == 0b11
    assert dut.lp_tx_data_n_o.value == 0b11
    assert dut.lp_tx_clk_p_o.value == 1
    assert dut.lp_tx_clk_n_o.value == 1


async def request_hs_mode(dut):
    clk = dut.byte_clk
    dut.d_hs_en_i.value = 1
    await RisingEdge(clk)
    dut.d_hs_en_i.value = 0
    await RisingEdge(clk)
    assert dut.dphy_ready_o.value == 0


async def clock_lp_to_hs(dut):
    await RisingEdge(dut.hs_clk_en_o)
    assert dut.dphy_ready_o.value == 0
    assert dut.lp_tx_clk_p_o.value == 0
    assert dut.lp_tx_clk_n_o.value == 1


async def data_lp_to_hs(dut):
    await RisingEdge(dut.hs_tx_en_o)
    assert dut.lp_tx_data_en_o.value == 0
    assert dut.lp_tx_data_p_o.value == 0b00
    assert dut.lp_tx_data_n_o.value == 0b11

    # HS mode enabled when d_hs_rdy_o is HIGH
    await RisingEdge(dut.d_hs_rdy_o)


async def do_xfr_data(dut):
    clk = dut.byte_clk
    dut.byte_or_pkt_data_en_i.value = 1
    dut.byte_or_pkt_data_i.value = 0xbeef
    await ClockCycles(clk, 1920)
    dut.byte_or_pkt_data_en_i.value = 0
    dut.byte_or_pkt_data_i.value = 0
    await FallingEdge(dut.byte_or_pkt_data_en_i)


async def tx_hs_to_lp(dut):
    await FallingEdge(dut.d_hs_rdy_o)
    assert dut.dphy_ready_o.value == 0
    assert dut.hs_tx_en_o.value == 1
    assert dut.hs_clk_en_o.value == 1
    assert dut.lp_tx_data_en_o.value == 0

    # Wait for HS disable to complete
    await RisingEdge(dut.dphy_ready_o)


async def test_mipi_dphy(dut, clock_period):
    clk = dut.byte_clk
    rst = dut.byte_rst
    dut_clk = Clock(clk, clock_period, "ps")
    cocotb.start_soon(dut_clk.start())

    await reset_module([rst], clk)

    # Initial values
    set_initial_values(dut)

    # Wait for initialization
    await RisingEdge(dut.tinit_done_o)
    await RisingEdge(clk)

    # Ensure D-PHY starts in Stop State
    assert_stop_state(dut)

    # Request HS mode and check if D-PHY received the request
    await request_hs_mode(dut)

    # Wait for clock to switch to HS mode and check its lanes states
    await clock_lp_to_hs(dut)

    # Wait for data lanes to initiate HS mode
    await data_lp_to_hs(dut)

    # Do a full line transfer
    await do_xfr_data(dut)

    # Initiate HS mode disable
    await tx_hs_to_lp(dut)

    # Ensure D-PHY is back in Stop State
    assert_stop_state(dut)


tf = TestFactory(test_function=test_mipi_dphy)
tf.add_option(name="clock_period", optionlist=[BYTE_CLK_74_25MHZ, BYTE_CLK_148_5MHZ])
tf.generate_tests()

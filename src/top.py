#!/usr/bin/env python3
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
from cmos2dphy import CMOS2DPHY

from pattern_gen import PatternGenerator


class Top(Module):
    def __init__(
        self, video_format="1080p60", four_lanes=False, sim=False, pattern_gen=False
    ):
        if video_format == "720p60":
            WC = 2560
        else:
            WC = 3840

        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_hfc = ClockDomain("hfc", reset_less=True)

        # IOs
        user_led_o = Signal(name="user_led_o")
        cdone_led_o = Signal(name="cdone_led_o")
        mipi_dphy_ios = {
            "mipi_clk_n_o": Signal(name="mipi_dphy_clk_n_o"),
            "mipi_clk_p_o": Signal(name="mipi_dphy_clk_p_o"),
            "mipi_d0_n_io": Signal(name="mipi_dphy_d0_n_o"),
            "mipi_d0_p_io": Signal(name="mipi_dphy_d0_p_o"),
            "mipi_d1_n_o": Signal(name="mipi_dphy_d1_n_o"),
            "mipi_d1_p_o": Signal(name="mipi_dphy_d1_p_o"),
        }
        deserializer_ios = {
            "des_reset_n_i": Signal(name="deserializer_reset_n_i"),
            "des_data_2to9_o": Signal(8, name="deserializer_data_2to9_o"),
            "des_data_12to19_o": Signal(8, name="deserializer_data_12to19_o"),
            "des_pix_clk_o": Signal(name="deserializer_pix_clk_o"),
            "des_pll_lock_o": Signal(name="deserializer_pll_lock_o"),
            "des_vblank_o": Signal(name="deserializer_vblank_o"),
            "des_hblank_o": Signal(name="deserializer_hblank_o"),
            "des_smpte_bypass_n_i": Signal(name="deserializer_smpte_bypass_n_i"),
            "des_ioproc_en_dis_i": Signal(name="deserializer_ioproc_en_dis_i"),
            "des_jtag_host_i": Signal(name="deserializer_jtag_host_i"),
            "des_rc_byp_n_i": Signal(name="deserializer_rc_byp_n_i"),
            "des_tim_861_i": Signal(name="deserializer_tim_861_i"),
            "des_sdo_en_dis_i": Signal(name="deserializer_sdo_en_dis_i"),
            "des_sw_en_i": Signal(name="deserializer_sw_en_i"),
            "des_sdin_tdi_i": Signal(name="deserializer_sdin_tdi_i"),
            "des_sdout_tdo_o": Signal(name="deserializer_sdout_tdo_o"),
            "des_cs_tms_n_i": Signal(name="deserializer_cs_tms_n_i"),
            "des_dvb_asi_i": Signal(name="deserializer_dvb_asi_i"),
        }
        if four_lanes:
            mipi_dphy_ios = {
                **mipi_dphy_ios,
                "mipi_d2_n_o": Signal(name="mipi_dphy_d2_n_o"),
                "mipi_d2_p_o": Signal(name="mipi_dphy_d2_p_o"),
                "mipi_d3_n_o": Signal(name="mipi_dphy_d3_n_o"),
                "mipi_d3_p_o": Signal(name="mipi_dphy_d3_p_o"),
            }
        self.ios = set(
            dict(
                user_led_o=user_led_o,
                cdone_led_o=cdone_led_o,
                **mipi_dphy_ios,
                **deserializer_ios
            ).values()
        )

        # Deserializer setup
        self.comb += [
            deserializer_ios["des_smpte_bypass_n_i"].eq(1),
            deserializer_ios["des_ioproc_en_dis_i"].eq(1),
            deserializer_ios["des_jtag_host_i"].eq(0),
            deserializer_ios["des_rc_byp_n_i"].eq(0),
            deserializer_ios["des_tim_861_i"].eq(0),
            deserializer_ios["des_sdo_en_dis_i"].eq(1),
            deserializer_ios["des_sw_en_i"].eq(0),
            deserializer_ios["des_dvb_asi_i"].eq(0),
        ]

        des_pix_clk = deserializer_ios["des_pix_clk_o"]
        des_reset_n = deserializer_ios["des_reset_n_i"]
        des_pll_lock = deserializer_ios["des_pll_lock_o"]

        # Logic - clk & rst
        hfclkout = Signal(name="hfclkout")
        reset_n = Signal(name="reset_n")
        reset_n_d = Signal(name="reset_n_d", reset_less=True)
        sys_reset_n = Signal(name="sys_reset_n", reset_less=True)

        ## Synchronize CDC reset and connect clk & rst signals
        self.sync += [
            reset_n_d.eq(reset_n),
            sys_reset_n.eq(reset_n_d)
        ]
        self.comb += [
            self.cd_sys.clk.eq(des_pix_clk),
            self.cd_sys.rst.eq(~sys_reset_n | ~des_pll_lock),
            self.cd_hfc.clk.eq(hfclkout),
        ]

        # Logic - Generate timings and MIPI D-PHY
        self.submodules.cmos2dphy = CMOS2DPHY(mipi_dphy_ios, video_format, four_lanes)

        if pattern_gen:
            self.submodules.pattern_gen = PatternGenerator(video_format)
            self.comb += [
                self.cmos2dphy.pix_data0_i.eq(self.pattern_gen.data_o[:8]),
                self.cmos2dphy.pix_data1_i.eq(self.pattern_gen.data_o[8:]),
                self.cmos2dphy.fv_i.eq(self.pattern_gen.fv_o),
                self.cmos2dphy.lv_i.eq(self.pattern_gen.lv_o),
            ]
        else:
            des_pix_data_UV = deserializer_ios["des_data_2to9_o"]
            des_pix_data_Y = deserializer_ios["des_data_12to19_o"]
            vblank = deserializer_ios["des_vblank_o"]
            hblank = deserializer_ios["des_hblank_o"]

            self.comb += [
                self.cmos2dphy.pix_data0_i.eq(des_pix_data_UV),
                self.cmos2dphy.pix_data1_i.eq(des_pix_data_Y),
                self.cmos2dphy.fv_i.eq(~vblank),
                self.cmos2dphy.lv_i.eq(~hblank & ~vblank),
            ]


        self.comb += [
            self.cmos2dphy.vc_i.eq(0),    # Virtual channel 0
            self.cmos2dphy.dt_i.eq(0x1e), # YUV422 8-bit
            self.cmos2dphy.wc_i.eq(WC),   # pixels * 2, 16-bit each
            user_led_o.eq(self.cmos2dphy.tx_dphy.txgo.tinit_done_o),
        ]

        # Internal oscillator set to 225 MHz
        self.specials += Instance(
            "OSCA",
            p_HF_CLK_DIV = "1",
            p_HF_OSC_EN = "ENABLED",
            i_HFOUTEN = 1,
            o_HFCLKOUT = hfclkout,
        )

        if sim:
            self.sync.hfc += [
                des_reset_n.eq(1),
                reset_n.eq(1),
            ]
        else:
            COUNTER_1s = 225000000
            COUNTER_100us = COUNTER_1s // 1000000
            counter = Signal(max=COUNTER_1s)

            self.sync.hfc += [
                counter.eq(counter + 1),
                If((counter > COUNTER_100us) & (~des_reset_n),
                    des_reset_n.eq(1),
                ),
                If((counter > COUNTER_1s),
                    cdone_led_o.eq(~cdone_led_o),
                    counter.eq(0),
                    If(~reset_n,
                        reset_n.eq(1),
                    ),
                ),
            ]


if __name__ == "__main__":
    top = Top(video_format="1080p60")
    print(convert(top, top.ios, name="top"))

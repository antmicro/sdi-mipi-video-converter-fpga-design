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
from migen.fhdl.module import Module
from migen.genlib.fifo import AsyncFIFO

__all__ = ["CMOS2DPHY"]


class CMOS2DPHY(Module):
    def __init__(self, mipi_dphy_ios, four_lanes=False, dphy_loc=1):
        assert dphy_loc in [0, 1]
        assert four_lanes in [True, False]

        self.clock_domains.cd_byte = ClockDomain("byte", reset_less=True)

        # Inputs
        self.fv_i = Signal()
        self.lv_i = Signal()
        self.pix_data0_i = Signal(8)
        self.pix_data1_i = Signal(8)

        mipi_dphy_clk_n_io = mipi_dphy_ios["mipi_clk_n_o"]
        mipi_dphy_clk_p_io = mipi_dphy_ios["mipi_clk_p_o"]
        mipi_dphy_d0_n_io = mipi_dphy_ios["mipi_d0_n_io"]
        mipi_dphy_d0_p_io = mipi_dphy_ios["mipi_d0_p_io"]
        mipi_dphy_d1_n_o = mipi_dphy_ios["mipi_d1_n_o"]
        mipi_dphy_d1_p_o = mipi_dphy_ios["mipi_d1_p_o"]

        if not four_lanes:
            mipi_dphy_data_n = Cat(mipi_dphy_d0_n_io, mipi_dphy_d1_n_o)
            mipi_dphy_data_p = Cat(mipi_dphy_d0_p_io, mipi_dphy_d1_p_o)
        else:
            mipi_dphy_d2_n_o = mipi_dphy_ios["mipi_d2_n_o"]
            mipi_dphy_d2_p_o = mipi_dphy_ios["mipi_d2_p_o"]
            mipi_dphy_d3_n_o = mipi_dphy_ios["mipi_d3_n_o"]
            mipi_dphy_d3_p_o = mipi_dphy_ios["mipi_d3_p_o"]
            mipi_dphy_data_n = Cat(
                mipi_dphy_d0_n_io, mipi_dphy_d1_n_o, mipi_dphy_d2_n_o, mipi_dphy_d3_n_o
            )
            mipi_dphy_data_p = Cat(
                mipi_dphy_d0_p_io, mipi_dphy_d1_p_o, mipi_dphy_d2_p_o, mipi_dphy_d3_p_o
            )

        # Outputs
        self.tinit_done_o = Signal()

        self.ios = {
            self.fv_i,
            self.lv_i,
            self.pix_data0_i,
            self.pix_data1_i,
        }
        self.ios.update(mipi_dphy_ios.values())

        # Internal logic
        self.submodules.fifo = fifo = ResetInserter(["sys", "byte"])(
            ClockDomainsRenamer({"write": "sys", "read": "byte"})(
                AsyncFIFO(width=16, depth=128)
            )
        )
        self.submodules.fsm = fsm = ClockDomainsRenamer("byte")(
            FSM(reset_state="WAIT_FV_START")
        )

        d_hs_rdy = Signal()
        fv_d = Signal()
        lv_d = Signal()
        dphy_ready = Signal()
        w_byte_data = Signal(16)
        w_byte_data_en = Signal()
        dt = Signal(6)
        wc = Signal(16)
        txfr_req = Signal()
        txfr_en = Signal()
        c2d_ready = Signal()
        c2d_ready = Signal()
        phdr_xfr_done = Signal()
        phdr_xfr_done_d = [Signal() for _ in range(2)]
        ld_pyld = Signal()
        ld_pyld_d = [Signal() for _ in range(2)]

        sp_en = Signal()
        lp_en = Signal()

        byte_data_en = Signal()
        hs_req = Signal()

        fv_start = Signal()
        fv_start = Signal()
        fv_end = Signal()
        lv_start = Signal()
        lv_end = Signal()
        lv_start = Signal()
        lv_end = Signal()

        # fmt: off
        self.sync += [
            fv_d.eq(self.fv_i),
            lv_d.eq(self.lv_i),

            If(self.fv_i & ~fv_d,
                fv_start.eq(1)
            ).Elif(fv_d & ~self.fv_i,
                fv_end.eq(1)
            ).Else(
                fv_start.eq(0),
                fv_end.eq(0)
            ),

            If(self.lv_i & ~lv_d,
                lv_start.eq(1)
            ).Elif(lv_d & ~self.lv_i,
                lv_end.eq(1)
            ).Else(
                lv_start.eq(0),
                lv_end.eq(0)
            ),
        ]

        fsm.act("WAIT_FV_START",
            If(fv_start,
                NextState("FV_START"),
            ),
        )
        fsm.act("FV_START",
            dt.eq(0),
            wc.eq(0),
            If(d_hs_rdy,
                NextValue(sp_en, 1),
                NextState("WAIT_FV_START_DONE")
            ),
        )
        fsm.act("WAIT_FV_START_DONE",
            NextValue(sp_en, 0),
            If(phdr_xfr_done_d[0] & ~phdr_xfr_done_d[1],
                If(lv_start,
                    NextState("LV_START"),
                ).Elif(self.lv_i,
                    dt.eq(0x1e),
                    wc.eq(3840),
                    NextValue(lp_en, 1),
                    NextState("LP_XFR"),
                ).Else(
                    NextState("WAIT_LV_START"),
                ),
            ),
        )
        fsm.act("WAIT_LV_START",
            If(lv_start,
                NextState("LV_START"),
            ),
        )
        fsm.act("LV_START",
            If(d_hs_rdy,
                dt.eq(0x1e),
                wc.eq(3840),
                NextValue(lp_en, 1),
                NextState("WAIT_FOR_PHDR"),
            ),
        )
        fsm.act("WAIT_FOR_PHDR",
            NextValue(lp_en, 0),
            dt.eq(0x1e),
            wc.eq(3840),
            If((~ld_pyld & ~ld_pyld_d[0] & ld_pyld_d[1]),
                NextState("LP_XFR"),
            ),
        )
        fsm.act("LP_XFR",
            NextValue(lp_en, 0),
            dt.eq(0x1e),
            wc.eq(3840),
            If(fifo.readable,
                fifo.re.eq(1),
                w_byte_data_en.eq(1),
            ),
            If(phdr_xfr_done_d[0] & ~phdr_xfr_done_d[1],
                NextState("LV_END"),
            ),
        )
        fsm.act("LV_END",
            If(~self.fv_i & c2d_ready,
                hs_req.eq(1),
                NextState("FV_END"),
            ).Elif(lv_start,
                NextState("LV_START"),
            )
        )
        fsm.act("FV_END",
            hs_req.eq(0),
            dt.eq(1),
            wc.eq(0),
            If(d_hs_rdy,
                NextValue(sp_en, 1),
                NextState("WAIT_FV_END_DONE"),
            ),
        )
        fsm.act("WAIT_FV_END_DONE",
            NextValue(sp_en, 0),
            dt.eq(1),
            wc.eq(0),
            If(phdr_xfr_done_d[0] & ~phdr_xfr_done_d[1],
                NextState("WAIT_FV_START"),
            ),
        )

        self.comb += [
            fifo.reset_sys.eq(~self.fv_i),
            fifo.reset_byte.eq(~self.fv_i),
            w_byte_data.eq(fifo.dout),
            txfr_req.eq(c2d_ready & (fv_start | fv_end | lv_start | hs_req)),
            byte_data_en.eq(self.fv_i & self.lv_i),
        ]

        self.sync += [
            If(byte_data_en & fifo.writable,
                fifo.we.eq(1),
                fifo.din.eq(Cat(self.pix_data0_i, self.pix_data1_i)),
            ).Else(
                fifo.we.eq(0),
                fifo.din.eq(0),
            ),
        ]

        self.sync.byte += [
            ld_pyld_d[0].eq(ld_pyld),
            ld_pyld_d[1].eq(ld_pyld_d[0]),
            phdr_xfr_done_d[0].eq(phdr_xfr_done),
            phdr_xfr_done_d[1].eq(phdr_xfr_done_d[0]),
        ]

        self.specials += Instance("byte2dphy_instance",
            i_reset_n_i             = ~ResetSignal(),
            i_ref_clk_i             = ClockSignal(),
            i_usrstdby_i            = ResetSignal(),
            i_pd_dphy_i             = 0,
            i_byte_or_pkt_data_i    = w_byte_data,
            i_byte_or_pkt_data_en_i = w_byte_data_en,
            o_ready_o               = dphy_ready,
            i_vc_i                  = 0,
            i_dt_i                  = dt,
            i_wc_i                  = wc,
            i_clk_hs_en_i           = txfr_req,
            i_d_hs_en_i             = txfr_req,
            o_tinit_done_o          = self.tinit_done_o,
            o_d_hs_rdy_o            = d_hs_rdy,
            o_byte_clk_o            = ClockSignal("byte"),
            o_c2d_ready_o           = c2d_ready,
            o_phdr_xfr_done_o       = phdr_xfr_done,
            o_ld_pyld_o             = ld_pyld,
            i_clk_p_io              = mipi_dphy_clk_p_io,
            i_clk_n_io              = mipi_dphy_clk_n_io,
            i_d_p_io                = mipi_dphy_data_p,
            i_d_n_io                = mipi_dphy_data_n,
            i_sp_en_i               = sp_en,
            i_lp_en_i               = lp_en,
            synthesis_directive     = "loc=\"DPHY%s\"" % dphy_loc,
        )
        # fmt: on


if __name__ == "__main__":
    mipi_dphy_ios = {
        "mipi_clk_n_o": Signal(name="mipi_dphy_clk_n_o"),
        "mipi_clk_p_o": Signal(name="mipi_dphy_clk_p_o"),
        "mipi_d0_n_io": Signal(name="mipi_dphy_d0_n_o"),
        "mipi_d0_p_io": Signal(name="mipi_dphy_d0_p_o"),
        "mipi_d1_n_o": Signal(name="mipi_dphy_d1_n_o"),
        "mipi_d1_p_o": Signal(name="mipi_dphy_d1_p_o"),
    }
    cmos2dphy = CMOS2DPHY(mipi_dphy_ios, four_lanes=False, dphy_loc=0)
    print(convert(cmos2dphy, cmos2dphy.ios, name="cmos2dphy"))

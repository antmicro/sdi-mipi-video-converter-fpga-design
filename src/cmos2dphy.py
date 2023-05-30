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
from packet_formatter import PacketFormatter
from mipi_dphy import TXDPHY

__all__ = ["CMOS2DPHY"]


class CMOS2DPHY(Module):
    def __init__(self, mipi_dphy_ios, four_lanes=False, sim=False):
        assert four_lanes in [True, False]
        assert sim in [True, False]

        self.clock_domains.cd_byte = ClockDomain("byte")

        # Inputs
        self.fv_i = Signal()
        self.lv_i = Signal()
        self.pix_data0_i = Signal(8)
        self.pix_data1_i = Signal(8)
        self.vc_i = Signal(2)
        self.dt_i = Signal(6)
        self.wc_i = Signal(16)

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
        self.dphy_ready_o = dphy_ready = Signal()
        self.sp_en_o = sp_en = Signal()
        self.lp_en_o = lp_en = Signal()
        self.txfr_req_o = txfr_req = Signal()
        self.d_hs_rdy_o = d_hs_rdy = Signal()
        self.phdr_xfr_done_o = phdr_xfr_done = Signal()
        self.dt_o = dt = Signal(6)
        self.wc_o = wc = Signal(16)

        self.ios = {
            self.cd_byte.clk,
            self.cd_byte.rst,
            self.fv_i,
            self.lv_i,
            self.pix_data0_i,
            self.pix_data1_i,
            self.vc_i,
            self.dt_i,
            self.wc_i,
        }
        self.ios.update(mipi_dphy_ios.values())

        if sim:
            self.ios.update((
                self.tinit_done_o,
                self.dphy_ready_o,
                self.sp_en_o,
                self.lp_en_o,
                self.txfr_req_o,
                self.d_hs_rdy_o,
                self.phdr_xfr_done_o,
                self.dt_o,
                self.wc_o,
            ))

        # FIFO between pixel clock and byte clock domains
        self.submodules.fifo = fifo = ResetInserter(["sys", "byte"])(
            ClockDomainsRenamer({"write": "sys", "read": "byte"})(
                AsyncFIFO(width=16, depth=512)
            )
        )

        # FSM to control CSI-2 protocol
        self.submodules.fsm = fsm = ClockDomainsRenamer("byte")(
            FSM(reset_state="WAIT_FV_START")
        )

        # Packet Formatter - Low Level Protocol
        self.submodules.packet_formatter = packet_formatter = \
            ClockDomainsRenamer("byte")(PacketFormatter())

        # Hardened TX D-PHY with TX Global Operations
        self.submodules.tx_dphy = tx_dphy = TXDPHY(sim=sim)
        txgo = tx_dphy.txgo

        # Internal signals
        pixdata = Cat(self.pix_data0_i, self.pix_data1_i)
        pixdata_d = Signal().like(pixdata)

        fv_d = Signal()
        lv_d = Signal()
        w_byte_data = Signal(16)
        w_byte_data_en = Signal()
        phdr_xfr_done_d = [Signal() for _ in range(2)]
        ld_pyld = Signal()
        ld_pyld_d = [Signal() for _ in range(2)]

        byte_data_en = Signal()
        hs_req = Signal()

        fv_start = Signal()
        fv_start_d = Signal()
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

            pixdata_d.eq(pixdata),
            fv_start_d.eq(fv_start),
        ]

        fsm.act("WAIT_FV_START",
            fifo.reset_sys.eq(1),
            fifo.reset_byte.eq(1),
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
            If(~phdr_xfr_done,
                w_byte_data.eq(packet_formatter.data_o),
                w_byte_data_en.eq(1),
            ).Else(
                If(lv_start,
                    NextState("LV_START"),
                ).Elif(self.lv_i,
                    NextState("HS_REQ"),
                ).Else(
                    NextState("WAIT_LV_START"),
                ),
            ),
        )
        fsm.act("HS_REQ",
            If(dphy_ready,
                hs_req.eq(1),
                NextState("LV_START"),
            ),
        )
        fsm.act("WAIT_LV_START",
            If(lv_start,
                NextState("LV_START"),
            ),
        )
        fsm.act("LV_START",
            If(d_hs_rdy,
                dt.eq(self.dt_i),
                wc.eq(self.wc_i),
                NextValue(lp_en, 1),
                NextState("WAIT_FOR_PHDR"),
            ),
        )
        fsm.act("WAIT_FOR_PHDR",
            NextValue(lp_en, 0),
            dt.eq(self.dt_i),
            wc.eq(self.wc_i),
            w_byte_data.eq(packet_formatter.data_o),
            w_byte_data_en.eq(1),
            If((~ld_pyld & ld_pyld_d[0]),
                NextState("LP_XFR"),
            ),
        )
        fsm.act("LP_XFR",
            NextValue(lp_en, 0),
            dt.eq(self.dt_i),
            wc.eq(self.wc_i),
            w_byte_data_en.eq(1),
            If(fifo.readable,
                fifo.re.eq(1),
                w_byte_data.eq(fifo.dout),
            ).Else(
                w_byte_data.eq(packet_formatter.data_o),
                If(phdr_xfr_done,
                    NextState("LV_END"),
                ),
            ),
        )
        fsm.act("LV_END",
            If(~self.fv_i & dphy_ready,
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
            If(~phdr_xfr_done,
                w_byte_data.eq(packet_formatter.data_o),
                w_byte_data_en.eq(1),
            ).Else(
                NextState("WAIT_FV_START"),
            ),
        )

        self.comb += [
            txfr_req.eq(dphy_ready & (fv_start_d | fv_start | fv_end | lv_start | hs_req)),
            byte_data_en.eq(fv_d & lv_d),

            If(byte_data_en & fifo.writable,
                fifo.we.eq(1),
                fifo.din.eq(pixdata_d),
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

        # Connect Pixel to D-PHY and Packet Formatter
        self.comb += [
            packet_formatter.byte_data_i.eq(fifo.dout),
            packet_formatter.vc_i.eq(self.vc_i),
            packet_formatter.wc_i.eq(wc),
            packet_formatter.dt_i.eq(dt),
            packet_formatter.sp_en_i.eq(sp_en),
            packet_formatter.lp_en_i.eq(lp_en),
            phdr_xfr_done.eq(packet_formatter.phdr_xfr_done_o),
            ld_pyld.eq(packet_formatter.ld_pyld_o),
        ]

        # Connect Pixel to D-PHY and TX D-PHY
        self.comb += [
            tx_dphy.byte_or_pkt_data_i.eq(w_byte_data),
            tx_dphy.byte_or_pkt_data_en_i.eq(w_byte_data_en),
            tx_dphy.d_hs_en_i.eq(txfr_req),
            mipi_dphy_clk_p_io.eq(tx_dphy.clk_p_io),
            mipi_dphy_clk_n_io.eq(tx_dphy.clk_n_io),
            mipi_dphy_data_p.eq(tx_dphy.data_p_io),
            mipi_dphy_data_n.eq(tx_dphy.data_n_io),
            d_hs_rdy.eq(txgo.d_hs_rdy_o),
            dphy_ready.eq(txgo.dphy_ready_o),
            self.tinit_done_o.eq(txgo.tinit_done_o)
        ]


if __name__ == "__main__":
    mipi_dphy_ios = {
        "mipi_clk_n_o": Signal(name="mipi_dphy_clk_n_o"),
        "mipi_clk_p_o": Signal(name="mipi_dphy_clk_p_o"),
        "mipi_d0_n_io": Signal(name="mipi_dphy_d0_n_o"),
        "mipi_d0_p_io": Signal(name="mipi_dphy_d0_p_o"),
        "mipi_d1_n_o": Signal(name="mipi_dphy_d1_n_o"),
        "mipi_d1_p_o": Signal(name="mipi_dphy_d1_p_o"),
    }
    cmos2dphy = CMOS2DPHY(mipi_dphy_ios, four_lanes=False, sim=True)
    print(convert(cmos2dphy, cmos2dphy.ios, name="cmos2dphy"))

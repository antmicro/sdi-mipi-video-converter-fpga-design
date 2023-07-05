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
from common import dphy_timings


class TXGlobalOperations(Module):
    """MIPI D-PHY control module, switches clock and data lanes between HS and LP
    modes on demand.

    Parameters
    ----------
    timings : dict
        D-PHY timing parameters.
    four_lanes : bool
        If true, modules will be generated in 4 lanes variant, otherwise it will
        be generated for 2 lanes.

    Attributes
    ----------
    byte_or_pkt_data_i : Signal(16)
        Byte data containing either converted pixel or packet data.
    d_hs_en_i : Signal(1)
        Request signal to enable HS mode.

    dphy_ready_o : Signal()
        D-PHY ready status, high when D-PHY can initiate LP to HS switch.
    d_hs_rdy_o : Signal()
        HS ready status, high when LP to HS switch is finished.
    tinit_done_o : Signal()
        D-PHY iniit status, high after stop state is asserted for a specified time.
    hs_clk_en_o : Signal()
        Enable HS mode on clock lanes.
    hs_tx_en_o : Signal()
        Enable HS mode on data lanes.
    lp_tx_data_en_o : Signal()
        Enable LP mode on data lanes. This signal takes precedence over hs_tx_en_o.
    lp_tx_clk_p_o, lp_tx_clk_n_o : Signal()
        LP state on clock lanes.
    lp_tx_data_p_o, lp_tx_data_n_o : Signal(LANES)
        LP state on data lanes.
    """
    def __init__(self, timings, four_lanes=False):
        assert four_lanes in [True, False]
        LANES = 4 if four_lanes else 2

        # Miscellanous signals
        self.dphy_ready_o = Signal()
        self.d_hs_rdy_o = Signal()
        self.tinit_done_o = Signal()

        # CSI-2 HS control signals
        self.byte_or_pkt_data_en_i = Signal()
        self.d_hs_en_i = Signal()
        self.hs_clk_en_o = Signal()
        self.hs_tx_en_o = Signal()

        # CSI-2 LP control signals
        self.lp_tx_data_en_o = Signal()
        self.lp_tx_clk_p_o = Signal()
        self.lp_tx_clk_n_o = Signal()
        self.lp_tx_data_p_o = Signal(LANES)
        self.lp_tx_data_n_o = Signal(LANES)

        self.ios = {
            self.dphy_ready_o,
            self.d_hs_rdy_o,
            self.tinit_done_o,
            self.byte_or_pkt_data_en_i,
            self.d_hs_en_i,
            self.hs_clk_en_o,
            self.hs_tx_en_o,
            self.lp_tx_data_en_o,
            self.lp_tx_clk_p_o,
            self.lp_tx_clk_n_o,
            self.lp_tx_data_p_o,
            self.lp_tx_data_n_o,
        }

        byte_or_pkt_data_en_r = Signal()
        self.sync += byte_or_pkt_data_en_r.eq(self.byte_or_pkt_data_en_i)

        self.submodules.fsm = fsm = FSM(reset_state="TX_STOP")

        counter = Signal(14)
        tinit_counter = Signal(14)

        self.sync += [
            If(~self.tinit_done_o,
                tinit_counter.eq(tinit_counter + 1),
            ),
            If(tinit_counter > timings["TINIT_VALUE"],
                self.tinit_done_o.eq(1),
            ).Else(
                self.tinit_done_o.eq(0),
            ),
        ]

        fsm.act("TX_STOP",
            NextValue(self.lp_tx_data_en_o, 1),
            NextValue(self.d_hs_rdy_o, 0),

            # Keep Stop State - LP-11
            NextValue(self.lp_tx_clk_p_o, 1),
            NextValue(self.lp_tx_clk_n_o, 1),
            NextValue(self.lp_tx_data_p_o, Replicate(1, LANES)),
            NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),

            # D-PHY is ready in Stop State
            NextValue(self.dphy_ready_o, 1),

            If(self.d_hs_en_i & self.tinit_done_o,
                NextValue(counter, 0),
                NextValue(self.dphy_ready_o, 0),
                NextValue(self.lp_tx_clk_p_o, 0),
                NextValue(self.lp_tx_clk_n_o, 1),
                NextState("TX_CLK_ENABLE"),
            ),
        )
        fsm.act("TX_CLK_ENABLE",
            NextValue(counter, counter + 1),
            NextValue(self.dphy_ready_o, 0),
            # Keep data in Stop State while enabling clock lane
            NextValue(self.lp_tx_data_p_o, Replicate(1, LANES)),
            NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),
            NextValue(self.lp_tx_data_en_o, 1),

            If(counter <= timings["T_LPX"],
                # HS Request
                NextValue(self.lp_tx_clk_p_o, 0),
                NextValue(self.lp_tx_clk_n_o, 1),
            ).Elif(counter <= (timings["T_LPX"] + timings["T_CLKPREP"]),
                # HS Prepare
                NextValue(self.lp_tx_clk_p_o, 0),
                NextValue(self.lp_tx_clk_n_o, 0),
            ).Elif(counter <= (timings["T_LPX"] + timings["T_CLKPREP"] + timings["T_CLK_HSZERO"]),
                # HS Go
                NextValue(self.lp_tx_clk_p_o, 0),
                NextValue(self.lp_tx_clk_n_o, 1),
            ).Else(
                NextValue(counter, 0),
                NextState("TX_DATA_ENABLE"),
            ),
        )
        fsm.act("TX_DATA_ENABLE",
            NextValue(counter, counter + 1),
            NextValue(self.dphy_ready_o, 0),
            NextValue(self.hs_clk_en_o, 1),

            If(counter <= timings["T_CLKPREP"],
                # TX Stop
                NextValue(self.lp_tx_data_p_o, Replicate(1, LANES)),
                NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),
            ).Elif(counter <= (timings["T_CLKPREP"] + timings["T_LPX"]),
                # HS Request
                NextValue(self.lp_tx_data_p_o, Replicate(0, LANES)),
                NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),
            ).Elif(counter <= (timings["T_CLKPREP"] + timings["T_LPX"] + timings["T_DATPREP"]),
                # HS Prepare
                NextValue(self.lp_tx_data_p_o, Replicate(0, LANES)),
                NextValue(self.lp_tx_data_n_o, Replicate(0, LANES)),
            ).Elif(counter <= (timings["T_CLKPREP"] + timings["T_LPX"] + timings["T_DATPREP"] + timings["T_DAT_HSZERO"]),
                # HS Go
                NextValue(self.lp_tx_data_en_o, 0),
                NextValue(self.hs_tx_en_o, 1),
                NextValue(self.lp_tx_data_p_o, Replicate(0, LANES)),
                NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),
            ).Else(
                # HS Enabled
                NextValue(self.lp_tx_data_en_o, 0),
                NextValue(self.d_hs_rdy_o, 1),
                NextValue(self.hs_tx_en_o, 1),
                If(~self.byte_or_pkt_data_en_i & byte_or_pkt_data_en_r,
                    NextValue(counter, 0),
                    NextState("TX_HS_DISABLE"),
                ),
            ),
        )
        fsm.act("TX_HS_DISABLE",
            NextValue(counter, counter + 1),
            NextValue(self.dphy_ready_o, 0),
            NextValue(self.hs_tx_en_o, 0),
            NextValue(self.d_hs_rdy_o, 0),
            NextValue(self.lp_tx_data_p_o, Replicate(1, LANES)),
            NextValue(self.lp_tx_data_n_o, Replicate(1, LANES)),

            If(counter <= (timings["T_CLKPOST"]),
                NextValue(self.hs_clk_en_o, 1),
                NextValue(self.lp_tx_data_en_o, 1),
            ).Elif(counter <= (timings["T_CLKPOST"] + timings["T_CLKTRAIL"]),
                NextValue(self.hs_clk_en_o, 0),
                NextValue(self.lp_tx_data_en_o, 1),
                NextValue(self.lp_tx_clk_p_o, 0),
                NextValue(self.lp_tx_clk_n_o, 1),
            ).Else(
                NextValue(self.hs_clk_en_o, 0),
                NextValue(self.lp_tx_data_en_o, 1),
                NextValue(self.lp_tx_clk_p_o, 1),
                NextValue(self.lp_tx_clk_n_o, 1),
                NextState("TX_STOP"),
            ),
        )


class TXDPHY(Module):
    """Wrapper module for hardened D-PHY and TX Global Operations.

    Parameters
    ----------
    video_format : str
        Video format string, used to choose correct D-PHY timings.
    four_lanes : bool
        If true, modules will be generated in 4 lanes variant, otherwise it will
        be generated for 2 lanes.
    sim : bool
        Omit generating D-PHY module if simulation mode is True.

    Attributes
    ----------
    txgo : TXGlobalOperations
        Child module used to control D-PHY states, switched between LP and HS modes.
        See class specific documentation for more information.

    byte_or_pkt_data_i : Signal(16)
        Byte data containing either converted pixel or packet data.
    byte_or_pkt_data_en_i : Signal(1)
        Validation signal for byte data.
    d_hs_en_i : Signal(1)
        Request signal to enable HS mode.

    clk_n_io, clk_p_io : Signal(1)
        D-PHY clock lane output pins.
    data_n_io, data_p_io : Signal(LANES)
        D-PHY data lane output pins. Its width depends on the four_lanes
        parameter.
    pll_lock_o : Signal(1)
        Internal D-PHY PLL lock status.

    """
    def __init__(self, video_format="1080p60", four_lanes=False, sim=False):
        assert four_lanes in [True, False]
        assert sim in [True, False]
        LANES = 4 if four_lanes else 2
        LANES_STR = "FOUR_LANES" if four_lanes else "TWO_LANES"
        timings = dphy_timings[video_format]

        self.clock_domains.cd_byte = ClockDomain("byte")

        self.submodules.txgo = txgo = ClockDomainsRenamer("byte")(
            TXGlobalOperations(timings, four_lanes))

        # PLL IOs
        self.pll_lock_o = Signal()

        # Data flow control
        self.byte_or_pkt_data_i = Signal(16)
        self.byte_or_pkt_data_en_i = Signal()
        self.d_hs_en_i = Signal()

        # D-PHY IOs
        self.clk_n_io = Signal()
        self.clk_p_io = Signal()
        self.data_n_io = Signal(LANES)
        self.data_p_io = Signal(LANES)

        # TX Global Operations IOs
        self.lp_tx_data_en_i = Signal().like(txgo.lp_tx_data_en_o)
        self.lp_tx_clk_p_i = Signal().like(txgo.lp_tx_clk_p_o)
        self.lp_tx_clk_n_i = Signal().like(txgo.lp_tx_clk_n_o)
        self.lp_tx_data_p_i = Signal().like(txgo.lp_tx_data_p_o)
        self.lp_tx_data_n_i = Signal().like(txgo.lp_tx_data_n_o)
        self.hs_clk_en_i = Signal().like(txgo.hs_clk_en_o)
        self.hs_tx_en_i = Signal().like(txgo.hs_tx_en_o)

        self.ios = {
            self.cd_byte.clk,
            self.cd_byte.rst,
            self.pll_lock_o,
            self.byte_or_pkt_data_i,
            self.byte_or_pkt_data_en_i,
            self.d_hs_en_i,
            self.clk_n_io,
            self.clk_p_io,
            self.data_n_io,
            self.data_p_io,
            self.lp_tx_data_en_i,
            self.lp_tx_clk_p_i,
            self.lp_tx_clk_n_i,
            self.lp_tx_data_p_i,
            self.lp_tx_data_n_i,
            self.hs_clk_en_i,
            self.hs_tx_en_i,
        }

        self.comb += [
            txgo.d_hs_en_i.eq(self.d_hs_en_i),
            txgo.byte_or_pkt_data_en_i.eq(self.byte_or_pkt_data_en_i),
            self.lp_tx_data_en_i.eq(txgo.lp_tx_data_en_o),
            self.lp_tx_clk_p_i.eq(txgo.lp_tx_clk_p_o),
            self.lp_tx_clk_n_i.eq(txgo.lp_tx_clk_n_o),
            self.lp_tx_data_p_i.eq(txgo.lp_tx_data_p_o),
            self.lp_tx_data_n_i.eq(txgo.lp_tx_data_n_o),
            self.hs_clk_en_i.eq(txgo.hs_clk_en_o),
            self.hs_tx_en_i.eq(txgo.hs_tx_en_o),
        ]

        if not sim:
            LANES_STR = "FOUR_LANES" if four_lanes else "TWO_LANES"
            self.specials += Instance("DPHY",
                p_GSR="DISABLED",
                p_AUTO_PD_EN="POWERED_UP",
                p_CFG_NUM_LANES=LANES_STR,
                p_CM=timings["CM"],
                p_CN=timings["CN"],
                p_CO=timings["CO"],
                p_CONT_CLK_MODE="DISABLED",
                p_DESKEW_EN="DISABLED",
                p_DSI_CSI="CSI2_APP",
                p_EN_CIL="CIL_BYPASSED",
                p_HSEL="DISABLED",
                p_LANE0_SEL="LANE_0",
                p_LOCK_BYP="GATE_TXBYTECLKHS",
                p_MASTER_SLAVE="MASTER",
                p_PLLCLKBYPASS="REGISTERED",
                p_TXDATAWIDTHHS="0b00", # Gear: 8 - "0b00", 16 - "0b01"
                # Clock and reset
                i_BITCKEXT=1, #(((DPHY_PLL == "REGISTERED") ? 1'd1 : pll_clkop_i)), # Maybe Bit clock external.
                i_CLKREF=ClockSignal(), # Reference clock to PLL.
                i_PDDPHY=0, # Power down DPHY.
                i_PDPLL=ResetSignal(),  # Power down PLL.
                # Scan mode
                i_SCCLKIN=1, # Scan clock in.
                # HS_TX enable ports
                i_UCENCK=self.hs_clk_en_i,  # Clock  HS_TX enable.
                i_UED0THEN=self.hs_tx_en_i,  # Lane 0 HS_TX enable.
                i_U1ENTHEN=self.hs_tx_en_i,  # Lane 1 HS_TX enable.
                # i_U2END2=self.hs_tx_en_i,  # lane 2 HS_TX enable.
                # i_U3END3=self.hs_tx_en_i,  # lane 3 HS_TX enable.
                # HS_TX ports
                i_UTXDHS=Cat(self.byte_or_pkt_data_i[:8], Replicate(0, 24)),  # Lane 0 HS_TX data.
                i_U1TXDHS=Cat(self.byte_or_pkt_data_i[8:16], Replicate(0, 24)),  # Lane 1 HS_TX data.
                # i_U2TXDHS=Cat(self.byte_or_pkt_data_i[16:24], Replicate(0, 24)),  # Lane 2 HS_TX data.
                # i_U3TXDHS=Cat(self.byte_or_pkt_data_i[24:32], Replicate(0, 24))  # Lane 3 HS_TX data.
                # HS_TX word valid ports
                i_UTXWVDHS=1,  # Lane 0 HS_TX word valid.
                i_U1TXWVHS=1,  # Lane 1 HS_TX word valid.
                # i_U2TXWVHS=1,  # Lane 2 HS_TX word valid.
                # i_U3TXWVHS=1,  # Lane 3 HS_TX word valid.
                # HS_TX power down ports
                i_U2TDE0D0=0,  # lane 0 HS_TX power down.
                i_U2TDE1D1=0,  # lane 1 HS_TX power down.
                # i_U2TDE2D2=0,  # lane 2 HS_TX power down.
                # i_U2TDE3D3=0,  # lane 3 HS_TX power down.
                # LP_TX enable ports
                ###/...... need to be updated for BTA
                i_UDE4CKTN=(~self.hs_clk_en_i),  #((CLK_MODE == "HS_ONLY")? 1'd0 : lp_tx_data_en_i),   # Clock  LP_TX enable.
                i_UDE0D0TN=self.lp_tx_data_en_i,  # Lane 0 LP_TX enable.
                i_UDE1D1TN=self.lp_tx_data_en_i,  # Lane 1 LP_TX enable.
                # i_UDE2D2TN=self.lp_tx_data_en_i,  # Lane 2 LP_TX enable.
                # i_UDE3D3TN=self.lp_tx_data_en_i,  # Lane 3 LP_TX enable.
                # LP_TX ports
                i_U3TXUPSX=self.lp_tx_clk_p_i,  # LP_TX positive clock.
                i_U3TXLPDT=self.lp_tx_clk_n_i,  # LP_TX negative clock.
                i_UTXMDTX=self.lp_tx_data_p_i[0],  # lane 0 LP_TX positive data.
                i_U1FTXST=self.lp_tx_data_n_i[0],  # lane 0 LP_TX negative data.
                i_U2FTXST=self.lp_tx_data_p_i[1],  # lane 1 LP_TX positive data.
                i_U3FTXST=self.lp_tx_data_n_i[1],  # lane 1 LP_TX negative data.
                # i_U3TDISD2=self.lp_tx_data_p[2],  # lane 2 LP_TX positive data.
                # i_U3TREQD2=self.lp_tx_data_n[2],  # lane 2 LP_TX negative data.
                # i_U3TXVD3=self.lp_tx_data_p[3],  # lane 3 LP_TX positive data.
                # i_U3TXULPS=self.lp_tx_data_n[3],  # lane 3 LP_TX negative data.
                # LP_TX down ports
                i_U2TDE4CK=0,  # clock  LP_TX power down.
                i_U2TDE5D0=0,  # lane 0 LP_TX power down.
                i_U2TDE6D1=0,  # lane 1 LP_TX power down.
                # i_U2TDE7D2=0,  # lane 2 LP_TX power down.
                # i_U3TDE0D3=0,  # lane 3 LP_TX power down.
                # Serializer enable
                i_UTRD0SEN=self.hs_tx_en_i,  # Lane 0 HS serializer enable.
                i_U1TXREQH=self.hs_tx_en_i,  # Lane 1 HS serializer enable.
                # i_U2TXREQH=self.hs_tx_en_i,  # Lane 2 HS serializer enable.
                # i_U3TXREQH=self.hs_tx_en_i,  # Lane 3 HS serializer enable.
                # Deserializer enable
                i_UTXENER=0,  # ENP_DESER(To override the Deserializer token detector and enable Deserializer Byte Clock and DATA. Only applicable in Test mode (default) 1'b0) in CIL BYPASSED
                i_UTXRD0EN=0,  # Lane 0 HS deserialaizer enable.
                i_U1TXREQ=0,  # lane 1 HS deserialaizer enable.
                i_U2TXREQ=0,  # Lane 2 HS deserialaizer enable.
                i_U3TXREQ=0,  # Lane 3 HS deserialaizer enable.
                #
                i_U3TDE5CK=ClockSignal(),  # HS_TX clock(CLK_DTXHS).
                i_U3TDE1D0=1,  # HS_TX data(D0_DTXHS).
                i_U3TDE2D1=1,  # HS_TX data(D1_DTXHS).
                # i_U3TDE3D2=1,  # HS_TX data(D2_DTXHS).
                # i_U3TDE4D3=1,  # HS_TX data(D3_DTXHS).
                #
                i_U1TDE6=0,  # CLK_CDEN.
                i_U1TDE2D0=0,  # D0_CDEN.
                i_U1TDE3D1=0,  # D1_CDEN.
                # i_U1TDE4D2=0,  # D2_CDEN.
                # i_U1TDE5D3=0,  # D3_CDEN.
                #Others
                i_UTXULPSE=0,  # Clock HS byte.
                i_U1TDE7=0,  # CLK_TXHSPD.
                i_U1TXLPD=0,  # LB_EN.(Dy_DTXHS => DPy/DNy , DPy/DNy => Dy_DRXHS)
                i_U3TDE6=0,  # MST_RV_EN.
                i_U3TDE7=0,  # SLV_RV_EN.
                i_UCTXREQH=0,  # clock hs gate.
                i_UCTXUPSX=0,  # PDCKG.
                # OUT
                # Byte clock
                o_UTWDCKHS=ClockSignal("byte"),
                # PLL lock
                o_LOCK=self.pll_lock_o,  # Lock
                # INOUT
                o_CKN=self.clk_n_io,  # Negative part of differential clock.
                o_CKP=self.clk_p_io,  # Positive part of differential clock.
                o_DN0=self.data_n_io[0],  # Negative part of differential data lane 0.
                o_DN1=self.data_n_io[1],  # Negative part of differential data lane 1.
                # o_DN2=self.data_n_io[2],  # Negative part of differential data lane 2.
                # o_DN3=self.data_n_io[3],  # Negative part of differential data lane 3.
                o_DP0=self.data_p_io[0],  # Positive part of differential data lane 0.
                o_DP1=self.data_p_io[1],  # Positive part of differential data lane 1.
                # o_DP2=self.data_p_io[2],  # Positive part of differential data lane 2.
                # o_DP3=self.data_p_io[3],  # Positive part of differential data lane 3.
                # Unused input ports(ports which used in CIL mode)
                o_URXCKINE=1,  # N/A
                o_UTXCKE=1,  # N/A
                o_UTRNREQ=1,  # N/A
                o_UFRXMODE=1,  # N/A
                o_UTDIS=1,  # N/A
                o_UTXTGE0=1,  # N/A
                o_UTXTGE1=1,  # N/A
                o_UTXTGE2=1,  # N/A
                o_UTXTGE3=1,  # N/A
                o_UTXUPSEX=1,  # N/A
                o_UTXVDE=1,  # N/A
                o_U1FRXMD=1,  # N/A
                o_U1TDIS=1,  # N/A
                o_U1TREQ=1,  # N/A
                o_U1TXTGE0=1,  # N/A
                o_U1TXTGE1=1,  # N/A
                o_U1TXTGE2=1,  # N/A
                o_U1TXTGE3=1,  # N/A
                o_U1TXUPSE=1,  # N/A
                o_U1TXUPSX=1,  # N/A
                o_U1TXVDE=1,  # N/A
                o_U2FRXMD=1,  # N/A
                o_U2TDIS=1,  # N/A
                o_U2TREQ=1,  # N/A
                o_U2TPDTE=1,  # N/A
                o_U2TXTGE0=1,  # N/A
                o_U2TXTGE1=1,  # N/A
                o_U2TXTGE2=1,  # N/A
                o_U2TXTGE3=1,  # N/A
                o_U2TXUPSE=1,  # N/A
                o_U2TXUPSX=1,  # N/A
                o_U2TXVDE=1,  # N/A
                o_U3FRXMD=1,  # N/A
                o_U3TXTGE0=1,  # N/A
                o_U3TXTGE1=1,  # N/A
                o_U3TXTGE2=1,  # N/A
                o_U3TXTGE3=1,  # N/A
            )

if __name__ == "__main__":
    txdphy = TXDPHY("1080p60", four_lanes=False, sim=True)
    print(convert(txdphy, txdphy.ios, name="mipi_dphy"))

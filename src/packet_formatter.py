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
from crc16 import CRC16
from common import dphy_timings

__all__ = ["PacketFormatter"]

# Maximum number of bytes in a single long packet payload (1920 * 2 = 3840)
MAX_WIDTH = 3840
# MIPI CSI-2 Initialization sequence
HS_INIT_SEQ = 0xb8


class PacketFormatter(Module):
    """Packet formatter for MIPI CSI-2 protocol. It generates short packets as well
    as header, footer and CRC for long packets.

    In order to initiate a packet generation, pulse high either sp_en_i or lp_en_i
    to generate short or long packet respectively. Virtual channel and data type
    should be asserted for at least 2 cycles after ld_pyld_o assertion. Word count
    should be asserted until the end of the packet generation which is indicated by
    asserting phdr_xfr_done_o.

    Output data is valid for 3 cycles (HS Init + header) since receiving sp_en_i or
    lp_en_i high pulse and when phdr_xfr_done_o is asserted (footer + HS Trail).

    Parameters
    ----------
    four_lanes : boolean
        Module operates on either 2 or 4 lanes variant depending on a value of
        this variable.

    Attributes
    ----------
    vc_i : Signal(2)
        Virtual channel for a current packet.
    dt_i : Signal(6)
        Data format for a current packet.
    wc_i : Signal(16)
        Number of bytes in a long packet's payload.
    sp_en_i : Signal(1)
        When this signal is pulsed, packet formatter starts a short packet transfer.
    lp_en_i : Signal(1)
        When this signal is pulsed, packet formatter starts a long packet transfer.
    byte_data_i : Signal(16)
        Bytes that are included in a long packet.

    phdr_xfr_done_o : Signal(1)
        Single pulse signal indicating that packet transfer is finished.
    ld_pyld_o : Signal(1)
        Single pulse signal indicating that long packet request is received.
    data_o : Signal(16)
        Data for generated header, footer or HS Trail state.
    """
    def __init__(self, video_format="1080p30", four_lanes=False):
        LANES = 4 if four_lanes else 2

        timings = dphy_timings[video_format]

        # Inputs
        self.vc_i = Signal(2)
        self.dt_i = Signal(6)
        self.wc_i = Signal(16)
        self.sp_en_i = Signal()
        self.lp_en_i = Signal()
        self.byte_data_i = Signal(16)

        # Outputs
        self.phdr_xfr_done_o = Signal()
        self.ld_pyld_o = Signal()
        self.data_o = Signal(16)

        # IOs
        self.ios = {
            self.vc_i,
            self.dt_i,
            self.wc_i,
            self.sp_en_i,
            self.lp_en_i,
            self.byte_data_i,
            self.phdr_xfr_done_o,
            self.ld_pyld_o,
            self.data_o,
        }

        # Internal signals
        di = Signal(8)
        ecc = Signal(8)
        long_xfr = Signal()
        hs_init_seq = Signal(16)
        payload_cnt = Signal(max=MAX_WIDTH)
        crc = Signal(16)
        last_data = Signal(16)

        # CRC Generator
        self.submodules.crc_gen = crc_gen = CRC16()
        self.comb += [
            crc_gen.crc_i.eq(crc),
            crc_gen.data_i.eq(self.byte_data_i),
        ]

        # ECC Generator
        self.sync += [
            ecc[0].eq(di[0] ^ di[1] ^ di[2] ^ di[4] ^ di[5] ^ di[7] ^ self.wc_i[2] ^
                      self.wc_i[3] ^ self.wc_i[5] ^ self.wc_i[8] ^ self.wc_i[12] ^
                      self.wc_i[13] ^ self.wc_i[14] ^ self.wc_i[15]),

            ecc[1].eq(di[0] ^ di[1] ^ di[3] ^ di[4] ^ di[6] ^ self.wc_i[0] ^
                      self.wc_i[2] ^ self.wc_i[4] ^ self.wc_i[6] ^ self.wc_i[9] ^
                      self.wc_i[12] ^ self.wc_i[13] ^ self.wc_i[14] ^ self.wc_i[15]),

            ecc[2].eq(di[0] ^ di[2] ^ di[3] ^ di[5] ^ di[6] ^ self.wc_i[1] ^
                      self.wc_i[3] ^ self.wc_i[4] ^ self.wc_i[7] ^ self.wc_i[10] ^
                      self.wc_i[12] ^ self.wc_i[13] ^ self.wc_i[14]),

            ecc[3].eq(di[1] ^ di[2] ^ di[3] ^ di[7] ^ self.wc_i[0] ^ self.wc_i[1] ^
                      self.wc_i[5] ^ self.wc_i[6] ^ self.wc_i[7] ^ self.wc_i[11] ^
                      self.wc_i[12] ^ self.wc_i[13] ^ self.wc_i[15]),

            ecc[4].eq(di[4] ^ di[5] ^ di[6] ^ di[7] ^ self.wc_i[0] ^ self.wc_i[1] ^
                      self.wc_i[8] ^ self.wc_i[9] ^ self.wc_i[10] ^ self.wc_i[11] ^
                      self.wc_i[12] ^ self.wc_i[14] ^ self.wc_i[15]),

            ecc[5].eq(self.wc_i[2] ^ self.wc_i[3] ^ self.wc_i[4] ^ self.wc_i[5] ^
                      self.wc_i[6] ^ self.wc_i[7] ^ self.wc_i[8] ^ self.wc_i[9] ^
                      self.wc_i[10] ^ self.wc_i[11] ^ self.wc_i[13] ^ self.wc_i[14] ^
                      self.wc_i[15]),
        ]

        self.compute_crc = Signal()
        # Indicate which - long or short packet is transferred
        self.sync += [
            If(self.lp_en_i,
                long_xfr.eq(1),
            ).Elif(self.sp_en_i | self.phdr_xfr_done_o,
                long_xfr.eq(0),
            ).Else(
                long_xfr.eq(long_xfr),
            ),
        ]

        self.sync += [
            last_data.eq(self.data_o),
            self.ld_pyld_o.eq(self.lp_en_i),
        ]

        self.comb += [
            di.eq(Cat(self.dt_i, self.vc_i)),
            hs_init_seq.eq(Replicate(HS_INIT_SEQ, LANES)),
        ]

        # Packet formatter state machine
        self.submodules.fsm = fsm = FSM(reset_state="WAIT_FOR_PACKET_REQ")

        # Wait for a sp_en_i or lp_en_i pulse to initiate packet formatter, then
        # drive HS Init sequence on data output
        fsm.act("WAIT_FOR_PACKET_REQ",
            NextValue(payload_cnt, 0),

            If(self.sp_en_i | self.lp_en_i,
                # Start of Transmission
                self.data_o.eq(hs_init_seq),
                NextState("GENERATE_HEADER"),
            ),
        )
        # Generate header on 2 clock cycles, then either restart CRC (set to 0xffff)
        # and proceed with long packet or generate End-of-Transmission if it's a short
        # packet
        fsm.act("GENERATE_HEADER",
            NextValue(payload_cnt, payload_cnt + 1),

            If(payload_cnt == 0,
                self.data_o.eq(Cat(self.dt_i, self.wc_i[:8])),
            ).Elif(payload_cnt == 1,
                self.data_o.eq(Cat(self.wc_i[8:], ecc)),
                NextValue(payload_cnt, 0),
                If(long_xfr,
                    NextValue(crc, 0xffff),
                    NextState("COMPUTE_CRC"),
                ).Else(
                    NextState("EoT"),
                ),
            ),
        )
        # Compute the payload checksum for word count cycles, then generate
        # End-of-Transmission
        fsm.act("COMPUTE_CRC",
            self.compute_crc.eq(1),
            NextValue(payload_cnt, payload_cnt + 1),
            NextValue(crc, crc_gen.crc_o),

            If(payload_cnt == ((self.wc_i >> 1) - 1),
                NextValue(payload_cnt, 0),
                NextState("EoT"),
            ),
        )
        # Send CRC to data output and generate the End-of-Transmission sequence
        # which consists of inverted last data MSB for time specified for HS Trail
        fsm.act("EoT",
            NextValue(payload_cnt, payload_cnt + 1),

            If(~long_xfr,
                If(payload_cnt == 0,
                    self.data_o.eq(Cat(Replicate(~last_data[7], 8), Replicate(~last_data[-1], 8))),
                ).Elif(payload_cnt != (timings["T_DATTRAIL"] - 1),
                    self.data_o.eq(last_data),
                ).Else(
                    self.data_o.eq(last_data),
                    self.phdr_xfr_done_o.eq(1),
                    NextState("WAIT_FOR_PACKET_REQ"),
                ),
            ).Else(
                If(payload_cnt == 0,
                    self.data_o.eq(crc_gen.crc_i),
                ).Elif(payload_cnt == 1,
                    self.data_o.eq(Cat(Replicate(~last_data[7], 8), Replicate(~last_data[-1], 8))),
                ).Elif(payload_cnt != timings["T_DATTRAIL"],
                    self.data_o.eq(last_data),
                ).Else(
                    self.data_o.eq(last_data),
                    self.phdr_xfr_done_o.eq(1),
                    NextState("WAIT_FOR_PACKET_REQ"),
                ),
            ),
        )


if __name__ == "__main__":
    packet_formatter = PacketFormatter()
    print(convert(packet_formatter, packet_formatter.ios, name="packet_formatter"))

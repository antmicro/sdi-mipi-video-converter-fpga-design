# SDI to MIPI CSI-2 Video Converter FPGA design

Copyright (c) 2023 [Antmicro](https://antmicro.com/)

## Introduction

This is the FPGA design for the [SDI to MIPI CSI-2 Video Converter](https://github.com/antmicro/sdi-mipi-video-converter) board.
The design is reproducing SDI MIPI Bridge implementation described in details in its [standalone documentation](https://antmicro.github.io/sdi-mipi-bridge/introduction.html).

## Content

The project consists of the following modules:
* [CSI-2 Finite State Machine](src/cmos2dphy.py) - FSM that controls MIPI CSI-2 protocol flow, assuming input signals `FVAL`/`LVAL` it transmits frames one by one.
Underlying modules are synchronized between each other in each FSM state to strictly follow MIPI CSI-2 protocol.

* [Packet Formatter](src/packet_formatter.py) (Low Level Protocol) - MIPI CSI-2 packet generator, it generates SoT (Start of Transmission), EoT (End of Transmission), header and footer for each packet.

* [Checksum generator](src/crc16.py) - combinatorial CRC16 checksum generator.

* [TX Global Operations](src/mipi_dphy.py#L22) - controls D-PHY interface lanes switching between Low Power (LP) and High Speed (HS) modes.

* [Hardened TX D-PHY](src/mipi_dphy.py#L321-L490) - the MIPI D-PHY interface provided by the FPGA fabric, configured to operate as a transmitter, controlled by TX Global Operations.

## Prerequisites

The dependencies required to build the FPGA design can be installed by running:
```bash
pip3 install -r requirements.txt
```
In order to generate a bitstream from the generated sources, the [nextpnr](https://github.com/YosysHQ/nextpnr) toolchain is required.

## Build the bitstream

Once required tools are installed, project can be built by invoking:
```bash
make all
```
There are few additional parameters that can be added in front of the above command.
See `make help` for more information.
Generated bitstream will be available in the `build/<variant>` directory and it is ready to be loaded onto FPGA device.

## Software

After successful programming, the Video Converter will synchronize to SDI signal and transfer converted MIPI CSI-2 on FFC2 interface.
Detailed instructions about software support is available in the [SDI MIPI Video Converter documentation](https://antmicro.github.io/sdi-mipi-video-converter/software.html).

## Simulation

In order to run tests with Verilator, run:
```
make tests
```
**Note:** Verilator tests do not cover the D-PHY module since there is no open source simulation model available.

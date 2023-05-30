# SDI to MIPI CSI-2 Video Converter FPGA design

Copyright 2023 [Antmicro](https://antmicro.com/)

## Introduction

This is the FPGA design for the [SDI to MIPI CSI-2 Video Converter](https://github.com/antmicro/sdi-mipi-video-converter) board.
The design is reproducing SDI MIPI Bridge implementation described in details in its [standalone documentation](https://antmicro.github.io/sdi-mipi-bridge/introduction.html).

## Content

The project consist of:

* [Serial to Parallel](src/sdi2mipi.py) - block written in Python with Migen to generate correct timings for the MIPI transmitter from synchronization signals acquired from the SDI deserializer.
Alternatively it is capable of generating artifficial timings and a video representing six separate vertical stripes, each in different color.

* [Pixel to D-PHY](src/pix2dphy.py) - Finite State Machine that controls MIPI D-PHY using interface exposed from Lattice MIPI/CSI-2 D-PHY Transmitter.

* [Lattice MIPI/CSI-2 D-PHY Transmitter](https://www.latticesemi.com/en/Products/DesignSoftwareAndIP/IntellectualProperty/IPCore/IPCores04/CSI2DSIDPHYTransmitter) - proprietary IP Core that generates MIPI packets, controls MIPI operations and distributes bytes between D-PHY lanes.

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

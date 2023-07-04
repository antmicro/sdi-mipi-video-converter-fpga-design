# Copyright 2023 Antmicro <www.antmicro.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SHELL=/bin/bash
DEVICE=LIFCL-40-9BG256C

# Build parameters
SYNTH_ARGS?=-flatten
YOSYS_ARGS?=-o $(PROJ)_syn.v
NEXTPNR_ARGS?=--placer-heap-timingweight 60
VIDEO_FORMAT?=1080p60
LANES?=2

ifneq ($(filter $(VIDEO_FORMAT), 1080p25 1080p30),)
CLK_FREQ = 74_25MHz
else ifneq ($(filter $(VIDEO_FORMAT), 1080p50 1080p60),)
CLK_FREQ = 148_5MHz
endif

# Tools binaries
YOSYS?=yosys
NEXTPNR?=nextpnr-nexus
PRJOXIDE?=prjoxide
ECPPROG?=ecpprog

ROOT=$(CURDIR)
PROJ=$(VIDEO_FORMAT)-$(LANES)lanes
BUILD_DIR=$(ROOT)/build/$(PROJ)
TEST_DIR=$(ROOT)/tests
VERILOG_TOP=$(BUILD_DIR)/top.v
PDC=$(ROOT)/constraints/video_converter_$(CLK_FREQ).pdc
TEST_MODULES = crc16 packet_formatter mipi_dphy cmos2dphy

ifeq ($(PATTERN_GEN),1)
PATTERN_GEN=--pattern-gen
else
PATTERN_GEN=
endif

ifeq ($(SIM),1)
SIM=--sim
else
SIM=
endif

all: $(PROJ).bit ## Generate verilog sources and build a bitstream

verilog: ## Generate verilog sources
	python3 $(ROOT)/generate.py --video-format $(VIDEO_FORMAT) --lanes $(LANES) $(PATTERN_GEN) $(SIM)

$(PROJ).json: verilog $(VERILOG_TOP) $(EXTRA_VERILOG) $(MEM_INIT_FILES)
	pushd $(BUILD_DIR) && $(YOSYS) $(YOSYS_ARGS) -ql $(PROJ)_syn.log -p "synth_nexus $(SYNTH_ARGS) -top top -json $(PROJ).json"  $(VERILOG_TOP) $(EXTRA_VERILOG) && popd

$(PROJ).fasm: $(PROJ).json $(PDC)
	pushd $(BUILD_DIR) && $(NEXTPNR) $(NEXTPNR_ARGS) -l $(BUILD_DIR)/$(PROJ)_nextpnr.log --device $(DEVICE) --pdc $(PDC) --json $(PROJ).json --fasm $(PROJ).fasm && popd

$(PROJ).bit: $(PROJ).fasm
	pushd $(BUILD_DIR) && $(PRJOXIDE) pack $(PROJ).fasm $(PROJ).bit && popd

prog: $(PROJ).bit ## Generate a bitstream and load it to the board's SRAM
	$(ECPPROG) -S $(PROJ).bit

prog-flash: $(PROJ).bit ## Generate a bitstream and load it to the board's flash
	$(ECPPROG) $(PROJ).bit

tests: ## Run all existing tests in cocotb + iverilog flow
	$(foreach TEST, $(TEST_MODULES), \
		TRACE=$(TRACE) TOP=$(TEST) $(MAKE) -C $(TEST_DIR) test; \
	)

clean: ## Remove all generated files for specific configuration
	rm -rf $(BUILD_DIR)

.SECONDARY:
.PHONY: tests help verilog prog prog-flash clean

.DEFAULT_GOAL := help
HELP_COLUMN_SPAN = 15
HELP_FORMAT_STRING = "\033[36m%-$(HELP_COLUMN_SPAN)s\033[0m %s\n"
help: ## Show this help message
	@echo List of available targets:
	@grep -hE '^[^#[:blank:]]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf $(HELP_FORMAT_STRING), $$1, $$2}'
	@echo
	@echo
	@echo List of available optional parameters:
	@echo
	@echo Build:
	@echo -e "\033[36mYOSYS\033[0m           Path to yosys binary (default: $(YOSYS))"
	@echo -e "\033[36mNEXTPNR\033[0m         Path to nextpnr binary (default: $(NEXTPNR))"
	@echo -e "\033[36mPRJOXIDE\033[0m        Path to prjoxide binary (default: $(PRJOXIDE))"
	@echo -e "\033[36mECPPROG\033[0m         Path to ecpprog binary (default: $(ECPPROG))"
	@echo -e "\033[36mYOSYS_ARGS\033[0m      Additional arguments for Yosys (default: $(YOSYS_ARGS))"
	@echo -e "\033[36mSYNTH_ARGS\033[0m      Additional arguments for Yosys 'synth_nexus' command (default: $(SYNTH_ARGS))"
	@echo -e "\033[36mNEXTPNR_ARGS\033[0m    Additional arguments for Nextpnr (default: $(NEXTPNR_ARGS))"
	@echo -e "\033[36mPATTERN_GEN\033[0m     Set to '1' if you want to generate design with embedded pattern generator (default: None)"
	@echo -e "\033[36mSIM\033[0m             Set to '1' if you want to generate verilog sources ready for simulation using Modelsim Lattice FPGA Edition (default: None)"
	@echo -e "\033[36mVIDEO_FORMAT\033[0m    Video format, one of 1080p25, 1080p30, 1080p50, 1080p60 (default: $(VIDEO_FORMAT))"
	@echo -e "\033[36mLANES\033[0m           D-PHY Lanes, must be either 2 or 4 (default: $(LANES))"
	@echo
	@echo Tests:
	@echo -e "\033[36mTRACE\033[0m           Set to '1' if you want to generate simulation waveforms (default: None)"

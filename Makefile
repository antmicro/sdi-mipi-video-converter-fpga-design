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
VIDEO_FORMAT?=1080p_3g
LANES?=2

ifneq ($(filter $(VIDEO_FORMAT), 720p_hd 720p25 720p30 720p50 720p60),)
    DATA_RATE = hd
    _VIDEO_FORMAT = 720p_hd
else ifneq ($(filter $(VIDEO_FORMAT), 1080p_hd 1080p25 1080p30),)
    DATA_RATE = hd
    _VIDEO_FORMAT = 1080p_hd
else ifneq ($(filter $(VIDEO_FORMAT), 1080p_3g 1080p50 1080p60),)
    DATA_RATE = 3g
    _VIDEO_FORMAT = 1080p_3g
else
    $(error Video format $(VIDEO_FORMAT) not supported)
endif

ifeq ($(PATTERN_GEN), 1)
    PATTERN_GEN=--pattern-gen
	_VIDEO_FORMAT = pattern_gen-$(VIDEO_FORMAT)
    ifneq ($(filter $(VIDEO_FORMAT), 720p25 720p30 720p50 720p60 1080p25 1080p30 1080p50 1080p60),)
    else
        $(error Video format $(VIDEO_FORMAT) not supported with pattern generator)
    endif
else
    PATTERN_GEN=
endif

# Tools binaries
YOSYS?=yosys
NEXTPNR?=nextpnr-nexus
PRJOXIDE?=prjoxide
ECPPROG?=ecpprog

ROOT=$(CURDIR)
PROJ=$(_VIDEO_FORMAT)-$(LANES)lanes
BUILD_DIR=$(ROOT)/build/$(PROJ)
TEST_DIR=$(ROOT)/tests
VERILOG_TOP=$(BUILD_DIR)/top.v
FASM=$(BUILD_DIR)/$(PROJ).fasm
JSON=$(BUILD_DIR)/$(PROJ).json
BITSTREAM=$(BUILD_DIR)/$(PROJ).bit
PDC=$(ROOT)/constraints/video_converter_$(DATA_RATE)-$(LANES)lanes.pdc
TEST_MODULES = crc16 packet_formatter_2lanes packet_formatter_4lanes \
				mipi_dphy cmos2dphy pattern_gen

ifeq ($(SIM),1)
    SIM=--sim
else
    SIM=
endif

all: $(BITSTREAM) ## Generate verilog sources and build a bitstream

verilog: $(VERILOG_TOP) ## Generate verilog sources

$(VERILOG_TOP):
	python3 $(ROOT)/generate.py --video-format $(VIDEO_FORMAT) --lanes $(LANES) $(PATTERN_GEN) $(SIM)

$(JSON): $(VERILOG_TOP) $(MEM_INIT_FILES)
	pushd $(BUILD_DIR) && $(YOSYS) $(YOSYS_ARGS) -ql $(PROJ)_syn.log -p "plugin -i systemverilog" -p "read_systemverilog $(VERILOG_TOP)" -p "synth_nexus -top top -json $(JSON)" && popd

$(FASM): $(JSON) $(PDC)
	pushd $(BUILD_DIR) && $(NEXTPNR) $(NEXTPNR_ARGS) -l $(BUILD_DIR)/$(PROJ)_nextpnr.log --device $(DEVICE) --pdc $(PDC) --json $(JSON) --fasm $(FASM) && popd

$(BITSTREAM): $(FASM)
	pushd $(BUILD_DIR) && $(PRJOXIDE) pack $(FASM) $(BITSTREAM) && popd

prog: $(BITSTREAM) ## Generate a bitstream and load it to the board's SRAM
	$(ECPPROG) -S $(BITSTREAM)

prog-flash: $(BITSTREAM) ## Generate a bitstream and load it to the board's flash
	$(ECPPROG) $(BITSTREAM)

tests: ## Run all existing tests in cocotb + iverilog flow
	$(foreach TEST, $(TEST_MODULES), \
		TRACE=$(TRACE) TOP=$(TEST) $(MAKE) -C $(TEST_DIR) test; \
	)

clean: ## Remove all generated files for specific configuration
	rm -rf $(BUILD_DIR)

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
	@echo -e "\033[36mVIDEO_FORMAT\033[0m    Video format, one of 720p_hd, 720p25, 720p30, 720p50, 720p60, 1080p_hd, 1080p25, 1080p30, 1080p_3g, 1080p50, 1080p60 (default: $(VIDEO_FORMAT))"
	@echo -e "\033[36mLANES\033[0m           D-PHY Lanes, must be either 2 or 4 (default: $(LANES))"
	@echo
	@echo Tests:
	@echo -e "\033[36mTRACE\033[0m           Set to '1' if you want to generate simulation waveforms (default: None)"

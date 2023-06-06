# Makefile

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOP ?= top
BUILD_DIR = $(CURDIR)/build/$(TOP)
SRC_DIR ?= $(CURDIR)/../src
VERILOG_SOURCES += $(BUILD_DIR)/$(TOP).v

# String to enable simulation waveforms
define COCOTB_SIM_WAVE_DUMP
`ifdef COCOTB_SIM\n\
initial begin\n\
\t$$dumpfile ("$(BUILD_DIR)/$(TOP).vcd");\n\
\t$$dumpvars (0, $(TOP));\n\
\t#1;\n\
end\n\
`endif
endef

# MODULE is the basename of the Python test file
MODULE = test_$(TOP)

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = $(TOP)

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

export COCOTB_SIM_WAVE_DUMP
test:
	mkdir -p $(BUILD_DIR)
	pushd $(BUILD_DIR) && python3 $(SRC_DIR)/$(TOP).py > $(TOP).v && popd
	sed -ie '/^);/a $(COCOTB_SIM_WAVE_DUMP)\n' $(BUILD_DIR)/$(TOP).v
	$(MAKE) sim

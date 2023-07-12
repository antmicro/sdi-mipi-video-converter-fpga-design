# Makefile
ifeq ($(TRACE), 1)
TRACE_ARGS="--trace --trace-structs"
IGNORE_DUMP_LOGS=| grep -v "^%Warning: previous dump at t=[0-9]*, requesting t=[0-9]*, dump call ignored$$"
endif

# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
TOP ?= top
BUILD_DIR = $(CURDIR)/build/$(TOP)
SRC_DIR ?= $(CURDIR)/../src
VERILOG_SOURCES += $(BUILD_DIR)/$(TOP).v
EXTRA_COMPILE_ARGS="--timing -Wno-COMBDLY -Wno-WIDTH -Wno-INITIALDLY -Wno-STMTDLY"
EXTRA_SIM_ARGS+=$(TRACE_ARGS)

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

# Test specific parameters
ifneq (,$(findstring lanes, $(TOP)))
    ifneq (,$(findstring 4lanes, $(TOP)))
        EXTRA_PARAMETERS = --lanes 4
        PYTHON_NAME = $(TOP:_4lanes=)
    else
        EXTRA_PARAMETERS = --lanes 2
        PYTHON_NAME = $(TOP:_2lanes=)
    endif
else
    PYTHON_NAME=$(TOP)
endif

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

export COCOTB_SIM_WAVE_DUMP
test:
	mkdir -p $(BUILD_DIR)
	pushd $(BUILD_DIR) && python3 $(SRC_DIR)/$(PYTHON_NAME).py $(EXTRA_PARAMETERS) > $(TOP).v && popd
	sed -i '/^);/a $(COCOTB_SIM_WAVE_DUMP)\n' $(BUILD_DIR)/$(TOP).v
	COMPILE_ARGS+=$(EXTRA_COMPILE_ARGS) EXTRA_ARGS+=$(EXTRA_SIM_ARGS) $(MAKE) sim $(IGNORE_DUMP_LOGS)

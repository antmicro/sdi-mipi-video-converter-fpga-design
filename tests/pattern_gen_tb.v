`timescale 1ps/1ps

module iver_tb;

	parameter integer H_ACTIVE = 1920;
	parameter integer H_SYNC = 44;
	parameter integer H_BACK_PORCH = 148;
	parameter integer H_FRONT_PORCH = 88;
	parameter integer V_ACTIVE = 1080;
	parameter integer V_SYNC = 5;
	parameter integer V_BACK_PORCH = 36;
	parameter integer V_FRONT_PORCH = 4;

	parameter integer FRAMES = 3;

	parameter integer V_TOTAL = V_ACTIVE + V_SYNC + V_BACK_PORCH + V_FRONT_PORCH;
	parameter integer H_TOTAL = H_ACTIVE + H_SYNC + H_BACK_PORCH + H_FRONT_PORCH;
	parameter integer FRAME_TOTAL = V_TOTAL * H_TOTAL;

	// Moreless 148.5 MHz
	integer CLK_PERIOD = 6734;
	integer i;
	integer k;
	integer j;

	reg reset = 1;
	wire fv;
	wire lv;
	wire [15:0] data;
	wire [11:0] linecnt;
	wire [11:0] pixcnt;

	initial begin
		$dumpfile("pattern_gen.vcd");
		$dumpvars(0, iver_tb);
		#5000
		#50 reset = 1;
		#50 reset = 0;
		#5000
		for (i = 0; i < FRAMES; i = i + 1) begin
			for (k = 0; k < FRAME_TOTAL; k = k + 1) begin
				#(CLK_PERIOD);
			end
		end
		#1 $finish;
	end

	reg clk = 0;
	always #(CLK_PERIOD/2) clk = !clk;

	pattern_gen UUT (
		.pix_clk(clk),
		.pix_rst(reset),
		.fv(fv),
		.lv(lv),
		.data(data),
		.linecnt(linecnt),
		.pixcnt(pixcnt)
	);
endmodule

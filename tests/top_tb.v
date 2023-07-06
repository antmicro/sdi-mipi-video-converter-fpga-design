`timescale 1ps/1ps

module iver_tb;

	parameter integer H_ACTIVE = 1920;
	parameter integer V_ACTIVE = 1080;
	parameter integer FRAMES = 10;

	// integer CLK_PERIOD = 13468; // 74.25 MHz
	integer CLK_PERIOD = 6734; // 148.5 MHz
	integer i;
	integer k;
	integer j;

	reg [15:0] image [1079:0][1919:0];

	reg locked = 0;
	reg fv = 0;
	reg lv = 0;
	reg [15:0] data;

	initial begin
		$dumpfile("top.vcd");
		$dumpvars(0, iver_tb);
		#(CLK_PERIOD * 10); locked = 1;
		// Wait for D-PHY tinit
		#(CLK_PERIOD * 16000 * (13468 / CLK_PERIOD));

		for (i = 0; i < FRAMES; i = i + 1) begin
			$readmemh("tests/bbb.txt", image);

			fv = 1;
			#(CLK_PERIOD * 280 * (13468 / CLK_PERIOD));
			for (j = 0; j < V_ACTIVE; j = j + 1) begin
				lv = 1;
				for (k = 0; k < H_ACTIVE; k = k + 1) begin
					data = image[j][k];
					#(CLK_PERIOD);
				end
				lv = 0;
				data = 0;
				#(CLK_PERIOD * 280 * (13468 / CLK_PERIOD));
			end
		end
		#1 $finish;
	end

	reg clk = 0;
	always #(CLK_PERIOD/2) clk = !clk;

	// GSR to satisfy Radiant & Modelsim
	GSR GSR_INST (
		.GSR_N(1),
		.CLK(clk)
	);

	top UUT (
		.deserializer_pix_clk_o(clk),
		.deserializer_pll_lock_o(locked),
		.deserializer_data_2to9_o(data[7:0]),
		.deserializer_data_12to19_o(data[15:8]),
		.deserializer_vblank_o(~fv),
		.deserializer_hblank_o(~lv)
	);
endmodule

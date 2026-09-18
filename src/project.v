/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_mohilkadakia_counter (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  reg [7:0] count;
  reg [7:0] uio_set;
  wire load;
  wire oe;
  wire [7:0] data_in;  

  assign load = ui_in[0];
  assign oe = ui_in[1];
  assign data_in = uio_in;
  assign uo_out  = count;
  assign uio_out = count;
  assign uio_oe  = uio_set;

  always @ (posedge clk or negedge rst_n) begin
    if(rst_n == 0)
      count <= 0;
    else if (load == 1)
      count <= data_in;
    else
      count <= count + 1;

  end

  always @(*) begin
    if(oe == 1)
      uio_set = 8'b11111111;
    else
      uio_set = 0;
  end

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:2], 1'b0};

endmodule

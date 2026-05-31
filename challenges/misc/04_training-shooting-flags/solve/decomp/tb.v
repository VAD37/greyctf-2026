`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg din = 0;
  wire o_cib25, o_cib39, o_pa11, o_pb13, o_pa15, o_tx20, o_tx22, o_tx9, o_tx2c, o_pc20;

  top dut(
    .G_HPBX0000(clk), .G_HPBX0100(clk), .G_HPBX0200(clk),
    .MIB_R0C15_PIOT0_JPADDIB_PIO(din),
    .CIB_R1C25_CIB_JD7(o_cib25),
    .CIB_R1C39_CIB_JD7(o_cib39),
    .MIB_R0C11_PIOT0_PADDOA_PIO(o_pa11),
    .MIB_R0C13_PIOT0_PADDOB_PIO(o_pb13),
    .MIB_R0C15_PIOT0_PADDOA_PIO(o_pa15),
    .MIB_R0C20_PIOT0_JTXDATA0B_SIOLOGIC(o_tx20),
    .MIB_R0C22_PIOT0_JTXDATA0A_SIOLOGIC(o_tx22),
    .MIB_R0C9_PIOT0_JTXDATA0B_SIOLOGIC(o_tx9),
    .MIB_R2C0_PICL0_JTXDATA4C_IOLOGIC(o_tx2c),
    .MIB_R2C0_PICL0_PADDOC_PIO(o_pc20)
  );

  integer i;
  initial begin
    // header: column order
    $display("# cyc cib25 cib39 pa11 pb13 pa15 tx20 tx22 tx9 tx2c pc20");
    for (i=0;i<4000;i=i+1) begin
      #5 clk=1; #5 clk=0;
      $display("%0d %b%b%b%b%b%b%b%b%b%b", i,
        o_cib25,o_cib39,o_pa11,o_pb13,o_pa15,o_tx20,o_tx22,o_tx9,o_tx2c,o_pc20);
    end
    $finish;
  end
endmodule

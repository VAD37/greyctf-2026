`timescale 1ns/1ps
module tb4;
  reg clk=0, din=1;
  wire o0,o1,o2,o3,o4,o5,o6,o7,o8,o9;
  top dut(
    .G_HPBX0000(clk), .G_HPBX0100(clk), .G_HPBX0200(clk),
    .MIB_R0C15_PIOT0_JPADDIB_PIO(din),
    .CIB_R1C25_CIB_JD7(o0), .CIB_R1C39_CIB_JD7(o1),
    .MIB_R0C11_PIOT0_PADDOA_PIO(o2), .MIB_R0C13_PIOT0_PADDOB_PIO(o3),
    .MIB_R0C15_PIOT0_PADDOA_PIO(o4),
    .MIB_R0C20_PIOT0_JTXDATA0B_SIOLOGIC(o5), .MIB_R0C22_PIOT0_JTXDATA0A_SIOLOGIC(o6),
    .MIB_R0C9_PIOT0_JTXDATA0B_SIOLOGIC(o7), .MIB_R2C0_PICL0_JTXDATA4C_IOLOGIC(o8),
    .MIB_R2C0_PICL0_PADDOC_PIO(o9)
  );
  wire p0 = dut.\R2C11_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p1 = dut.\R2C12_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p2 = dut.\R2C12_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p3 = dut.\R2C13_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p4 = dut.\R2C14_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p5 = dut.\R2C15_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p6 = dut.\R2C15_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p7 = dut.\R2C15_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p8 = dut.\R2C15_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p9 = dut.\R2C17_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p10 = dut.\R2C19_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p11 = dut.\R2C19_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p12 = dut.\R2C20_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p13 = dut.\R2C37_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p14 = dut.\R3C10_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p15 = dut.\R3C11_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p16 = dut.\R3C12_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p17 = dut.\R3C12_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p18 = dut.\R3C14_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p19 = dut.\R3C15_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p20 = dut.\R3C37_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p21 = dut.\R3C37_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p22 = dut.\R3C37_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p23 = dut.\R3C37_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p24 = dut.\R3C37_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p25 = dut.\R3C38_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p26 = dut.\R3C38_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p27 = dut.\R3C38_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p28 = dut.\R3C38_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p29 = dut.\R3C38_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p30 = dut.\R3C38_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p31 = dut.\R3C38_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p32 = dut.\R3C38_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p33 = dut.\R3C39_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p34 = dut.\R3C39_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p35 = dut.\R3C39_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p36 = dut.\R3C39_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p37 = dut.\R3C39_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p38 = dut.\R3C39_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p39 = dut.\R3C39_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p40 = dut.\R3C39_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p41 = dut.\R3C40_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p42 = dut.\R3C40_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p43 = dut.\R3C40_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p44 = dut.\R3C40_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p45 = dut.\R3C40_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p46 = dut.\R3C40_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p47 = dut.\R3C40_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p48 = dut.\R3C40_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p49 = dut.\R3C41_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p50 = dut.\R3C41_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p51 = dut.\R4C11_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p52 = dut.\R4C13_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p53 = dut.\R4C13_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p54 = dut.\R4C13_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p55 = dut.\R4C35_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p56 = dut.\R4C35_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p57 = dut.\R4C35_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p58 = dut.\R4C35_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p59 = dut.\R4C35_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p60 = dut.\R4C36_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p61 = dut.\R4C36_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p62 = dut.\R4C36_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p63 = dut.\R4C36_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p64 = dut.\R4C36_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p65 = dut.\R4C36_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p66 = dut.\R4C36_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p67 = dut.\R4C36_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p68 = dut.\R4C37_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p69 = dut.\R4C37_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p70 = dut.\R4C37_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p71 = dut.\R4C37_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p72 = dut.\R4C37_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p73 = dut.\R4C37_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p74 = dut.\R4C37_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p75 = dut.\R4C37_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p76 = dut.\R4C38_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p77 = dut.\R4C38_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p78 = dut.\R4C38_PLC2_inst.sliceB_inst.ff_0.Q ;
  wire p79 = dut.\R4C38_PLC2_inst.sliceB_inst.ff_1.Q ;
  wire p80 = dut.\R4C38_PLC2_inst.sliceC_inst.ff_0.Q ;
  wire p81 = dut.\R4C38_PLC2_inst.sliceC_inst.ff_1.Q ;
  wire p82 = dut.\R4C38_PLC2_inst.sliceD_inst.ff_0.Q ;
  wire p83 = dut.\R4C38_PLC2_inst.sliceD_inst.ff_1.Q ;
  wire p84 = dut.\R4C39_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p85 = dut.\R4C39_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p86 = dut.\R5C12_PLC2_inst.sliceA_inst.ff_0.Q ;
  wire p87 = dut.\R5C13_PLC2_inst.sliceA_inst.ff_1.Q ;
  wire p88 = dut.\R5C35_PLC2_inst.sliceC_inst.ff_0.Q ;
  integer i;
  initial begin
    $display("# FF order: \R2C11_PLC2_inst.sliceD_inst.ff_1.Q \R2C12_PLC2_inst.sliceC_inst.ff_1.Q \R2C12_PLC2_inst.sliceD_inst.ff_1.Q \R2C13_PLC2_inst.sliceC_inst.ff_0.Q \R2C14_PLC2_inst.sliceC_inst.ff_0.Q \R2C15_PLC2_inst.sliceB_inst.ff_0.Q \R2C15_PLC2_inst.sliceC_inst.ff_0.Q \R2C15_PLC2_inst.sliceC_inst.ff_1.Q \R2C15_PLC2_inst.sliceD_inst.ff_1.Q \R2C17_PLC2_inst.sliceA_inst.ff_0.Q \R2C19_PLC2_inst.sliceA_inst.ff_0.Q \R2C19_PLC2_inst.sliceA_inst.ff_1.Q \R2C20_PLC2_inst.sliceA_inst.ff_1.Q \R2C37_PLC2_inst.sliceA_inst.ff_0.Q \R3C10_PLC2_inst.sliceB_inst.ff_1.Q \R3C11_PLC2_inst.sliceB_inst.ff_0.Q \R3C12_PLC2_inst.sliceA_inst.ff_1.Q \R3C12_PLC2_inst.sliceC_inst.ff_0.Q \R3C14_PLC2_inst.sliceA_inst.ff_1.Q \R3C15_PLC2_inst.sliceD_inst.ff_1.Q \R3C37_PLC2_inst.sliceB_inst.ff_1.Q \R3C37_PLC2_inst.sliceC_inst.ff_0.Q \R3C37_PLC2_inst.sliceC_inst.ff_1.Q \R3C37_PLC2_inst.sliceD_inst.ff_0.Q \R3C37_PLC2_inst.sliceD_inst.ff_1.Q \R3C38_PLC2_inst.sliceA_inst.ff_0.Q \R3C38_PLC2_inst.sliceA_inst.ff_1.Q \R3C38_PLC2_inst.sliceB_inst.ff_0.Q \R3C38_PLC2_inst.sliceB_inst.ff_1.Q \R3C38_PLC2_inst.sliceC_inst.ff_0.Q \R3C38_PLC2_inst.sliceC_inst.ff_1.Q \R3C38_PLC2_inst.sliceD_inst.ff_0.Q \R3C38_PLC2_inst.sliceD_inst.ff_1.Q \R3C39_PLC2_inst.sliceA_inst.ff_0.Q \R3C39_PLC2_inst.sliceA_inst.ff_1.Q \R3C39_PLC2_inst.sliceB_inst.ff_0.Q \R3C39_PLC2_inst.sliceB_inst.ff_1.Q \R3C39_PLC2_inst.sliceC_inst.ff_0.Q \R3C39_PLC2_inst.sliceC_inst.ff_1.Q \R3C39_PLC2_inst.sliceD_inst.ff_0.Q \R3C39_PLC2_inst.sliceD_inst.ff_1.Q \R3C40_PLC2_inst.sliceA_inst.ff_0.Q \R3C40_PLC2_inst.sliceA_inst.ff_1.Q \R3C40_PLC2_inst.sliceB_inst.ff_0.Q \R3C40_PLC2_inst.sliceB_inst.ff_1.Q \R3C40_PLC2_inst.sliceC_inst.ff_0.Q \R3C40_PLC2_inst.sliceC_inst.ff_1.Q \R3C40_PLC2_inst.sliceD_inst.ff_0.Q \R3C40_PLC2_inst.sliceD_inst.ff_1.Q \R3C41_PLC2_inst.sliceA_inst.ff_0.Q \R3C41_PLC2_inst.sliceA_inst.ff_1.Q \R4C11_PLC2_inst.sliceB_inst.ff_0.Q \R4C13_PLC2_inst.sliceA_inst.ff_0.Q \R4C13_PLC2_inst.sliceA_inst.ff_1.Q \R4C13_PLC2_inst.sliceB_inst.ff_0.Q \R4C35_PLC2_inst.sliceB_inst.ff_1.Q \R4C35_PLC2_inst.sliceC_inst.ff_0.Q \R4C35_PLC2_inst.sliceC_inst.ff_1.Q \R4C35_PLC2_inst.sliceD_inst.ff_0.Q \R4C35_PLC2_inst.sliceD_inst.ff_1.Q \R4C36_PLC2_inst.sliceA_inst.ff_0.Q \R4C36_PLC2_inst.sliceA_inst.ff_1.Q \R4C36_PLC2_inst.sliceB_inst.ff_0.Q \R4C36_PLC2_inst.sliceB_inst.ff_1.Q \R4C36_PLC2_inst.sliceC_inst.ff_0.Q \R4C36_PLC2_inst.sliceC_inst.ff_1.Q \R4C36_PLC2_inst.sliceD_inst.ff_0.Q \R4C36_PLC2_inst.sliceD_inst.ff_1.Q \R4C37_PLC2_inst.sliceA_inst.ff_0.Q \R4C37_PLC2_inst.sliceA_inst.ff_1.Q \R4C37_PLC2_inst.sliceB_inst.ff_0.Q \R4C37_PLC2_inst.sliceB_inst.ff_1.Q \R4C37_PLC2_inst.sliceC_inst.ff_0.Q \R4C37_PLC2_inst.sliceC_inst.ff_1.Q \R4C37_PLC2_inst.sliceD_inst.ff_0.Q \R4C37_PLC2_inst.sliceD_inst.ff_1.Q \R4C38_PLC2_inst.sliceA_inst.ff_0.Q \R4C38_PLC2_inst.sliceA_inst.ff_1.Q \R4C38_PLC2_inst.sliceB_inst.ff_0.Q \R4C38_PLC2_inst.sliceB_inst.ff_1.Q \R4C38_PLC2_inst.sliceC_inst.ff_0.Q \R4C38_PLC2_inst.sliceC_inst.ff_1.Q \R4C38_PLC2_inst.sliceD_inst.ff_0.Q \R4C38_PLC2_inst.sliceD_inst.ff_1.Q \R4C39_PLC2_inst.sliceA_inst.ff_0.Q \R4C39_PLC2_inst.sliceA_inst.ff_1.Q \R5C12_PLC2_inst.sliceA_inst.ff_0.Q \R5C13_PLC2_inst.sliceA_inst.ff_1.Q \R5C35_PLC2_inst.sliceC_inst.ff_0.Q");
    for (i=0;i<4000;i=i+1) begin
      #5 clk=1; #5 clk=0;
      $display("%0d %b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b%b", i, p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24,p25,p26,p27,p28,p29,p30,p31,p32,p33,p34,p35,p36,p37,p38,p39,p40,p41,p42,p43,p44,p45,p46,p47,p48,p49,p50,p51,p52,p53,p54,p55,p56,p57,p58,p59,p60,p61,p62,p63,p64,p65,p66,p67,p68,p69,p70,p71,p72,p73,p74,p75,p76,p77,p78,p79,p80,p81,p82,p83,p84,p85,p86,p87,p88);
    end
    $finish;
  end
endmodule

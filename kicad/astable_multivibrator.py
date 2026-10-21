"""astable_multivibrator - classic 2-transistor astable LED flasher.

circuit-synth source (Phase 3). Topology / values / pad mapping: ../CLAUDE.md section 3 and 5.
Hybrid footprints and the 5-pin NPN symbol live in kicad/lib (Hybrid.*).
"""
from circuit_synth import Component, Net, circuit


@circuit(name="astable_multivibrator")
def astable_multivibrator():
    VCC = Net("VCC")
    GND = Net("GND")
    Q1_C = Net("Q1_C")
    Q2_C = Net("Q2_C")
    Q1_B = Net("Q1_B")
    Q2_B = Net("Q2_B")
    LED1_A = Net("LED1_A")
    LED2_A = Net("LED2_A")
    Q1_TL = Net("Q1_TL")
    Q1_TR = Net("Q1_TR")
    Q2_TL = Net("Q2_TL")
    Q2_TR = Net("Q2_TR")

    # power input
    j1 = Component(symbol="Connector_Generic:Conn_01x02", ref="J1", value="PWR_IN",
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j1[1] += VCC
    j1[2] += GND

    # collector loads: VCC - R - LED(A->K) - collector
    r1 = Component(symbol="Device:R", ref="R1", value="470",
                   footprint="Hybrid:R_Hybrid_0805_P2.54_Vertical")
    r1[1] += VCC
    r1[2] += LED1_A
    led1 = Component(symbol="Device:LED", ref="LED1", value="LED_RED",
                     footprint="Hybrid:LED_Hybrid_0805_D3.0mm")
    led1[2] += LED1_A   # anode
    led1[1] += Q1_C     # cathode

    r4 = Component(symbol="Device:R", ref="R4", value="470",
                   footprint="Hybrid:R_Hybrid_0805_P2.54_Vertical")
    r4[1] += VCC
    r4[2] += LED2_A
    led2 = Component(symbol="Device:LED", ref="LED2", value="LED_RED",
                     footprint="Hybrid:LED_Hybrid_0805_D3.0mm")
    led2[2] += LED2_A
    led2[1] += Q2_C

    # base bias
    r2 = Component(symbol="Device:R", ref="R2", value="47k",
                   footprint="Hybrid:R_Hybrid_0805_P2.54_Vertical")
    r2[1] += VCC
    r2[2] += Q1_B
    r3 = Component(symbol="Device:R", ref="R3", value="47k",
                   footprint="Hybrid:R_Hybrid_0805_P2.54_Vertical")
    r3[1] += VCC
    r3[2] += Q2_B

    # timing caps, + at collector
    c1 = Component(symbol="Device:C_Polarized", ref="C1", value="10uF",
                   footprint="Hybrid:CP_Hybrid_0805_D5.0mm_P2.50mm")
    c1[1] += Q1_C
    c1[2] += Q2_B
    c2 = Component(symbol="Device:C_Polarized", ref="C2", value="10uF",
                   footprint="Hybrid:CP_Hybrid_0805_D5.0mm_P2.50mm")
    c2[1] += Q2_C
    c2[2] += Q1_B

    # transistors: 1=E 2=B 3=C (SOT-23 + shared B hole), 4=TL 5=TR (TO-92 outer legs)
    q1 = Component(symbol="Hybrid:Q_NPN_Hybrid", ref="Q1", value="NPN",
                   footprint="Hybrid:Q_NPN_Hybrid_TO-92_SOT-23")
    q1[1] += GND
    q1[2] += Q1_B
    q1[3] += Q1_C
    q1[4] += Q1_TL
    q1[5] += Q1_TR
    q2 = Component(symbol="Hybrid:Q_NPN_Hybrid", ref="Q2", value="NPN",
                   footprint="Hybrid:Q_NPN_Hybrid_TO-92_SOT-23")
    q2[1] += GND
    q2[2] += Q2_B
    q2[3] += Q2_C
    q2[4] += Q2_TL
    q2[5] += Q2_TR

    # pinout-select solder jumpers (pin 2 = common = TO-92 outer leg)
    # bridged 1-2 by default: TL=E, TR=C -> E-B-C pinout (2N3904). Cut + bridge 2-3 -> C-B-E (BC547).
    jp1 = Component(symbol="Jumper:SolderJumper_3_Bridged12", ref="JP1", value="PINOUT",
                    footprint="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm")
    jp1[1] += GND
    jp1[2] += Q1_TL
    jp1[3] += Q1_C
    jp2 = Component(symbol="Jumper:SolderJumper_3_Bridged12", ref="JP2", value="PINOUT",
                    footprint="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm")
    jp2[1] += Q1_C
    jp2[2] += Q1_TR
    jp2[3] += GND
    jp3 = Component(symbol="Jumper:SolderJumper_3_Bridged12", ref="JP3", value="PINOUT",
                    footprint="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm")
    jp3[1] += GND
    jp3[2] += Q2_TL
    jp3[3] += Q2_C
    jp4 = Component(symbol="Jumper:SolderJumper_3_Bridged12", ref="JP4", value="PINOUT",
                    footprint="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm")
    jp4[1] += Q2_C
    jp4[2] += Q2_TR
    jp4[3] += GND


if __name__ == "__main__":
    c = astable_multivibrator()
    c.generate_kicad_project(project_name="astable_multivibrator", force_regenerate=True)

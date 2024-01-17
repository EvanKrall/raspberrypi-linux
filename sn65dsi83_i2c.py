#!/usr/bin/python3

from smbus2 import SMBus
import textwrap
import shutil


I2C_ADDRESS = 0x2d

with SMBus(10) as bus:
    regs = [bus.read_byte_data(I2C_ADDRESS, register, force=True) for register in range(0x00, 0xE5+1)]


def bit(reg_num, bit_num):
    return (regs[reg_num] >> bit_num) & 0x01


def bitrange(reg_num, high_bit, low_bit, little_endian=True):

    if high_bit >= 8:
        assert high_bit < 16
        if little_endian:
            reg = regs[reg_num] + (regs[reg_num+1] << 8)
        else:
            reg = regs[reg_num] << 8 + (regs[reg_num+1])
    else:
        reg = regs[reg_num]
    mask = (2<<(high_bit - low_bit)) - 1
    return (reg >> low_bit) & mask


def print_variable(name, reg_num, high_bit, low_bit=None, conv=None):
    if low_bit is None:
        low_bit = high_bit
    bits = bitrange(reg_num, high_bit, low_bit)
    length = high_bit - low_bit + 1
    bitstr = f"{bits:0{length}b}"
    if conv:
        try:
            # try first as a list/dict
            converted = conv[bits]
        except TypeError:
            # if that fails, try as a function.
            converted = conv(bits)
    else:
        converted = ""

    bitstr = (" " * (15 - high_bit)) + bitstr + (" " * low_bit)
    prefix = f"{name:>32}:   {bitstr}   "

    remaining_width = shutil.get_terminal_size((80, 24)).columns - len(prefix)

    # if converted is empty, textwrap.fill will return an empty string.
    lines = [x for l in converted.strip('\n').split('\n') for x in textwrap.wrap(l, width=remaining_width, replace_whitespace=False)]

    if lines:
        print(prefix+lines[0])
        for line in lines[1:]:
            print(" " * len(prefix) + line)
    else:
        print(prefix)

def endis(desc):
    return [f"Disable {desc}", f"Enable {desc}"]


def concat(*args):
    ret = []
    for arg in args:
        ret.extend(arg)
    return ret



print_variable("REG0A                           ", 0x0A, 7, 0)
print_variable("PLL_EN_STAT", 0x0A, 7, conv=[
    "PLL not enabled (default)",
    "PLL enabled",
])
print_variable("LVDS_CLK_RANGE", 0x0A, 3, 1, conv=[
    "25 MHz ≤ LVDS_CLK < 37.5 MHz",
    "37.5 MHz ≤ LVDS_CLK < 62.5 MHz",
    "62.5 MHz ≤ LVDS_CLK < 87.5 MHz",
    "87.5 MHz ≤ LVDS_CLK < 112.5 MHz",
    "112.5 MHz ≤ LVDS_CLK < 137.5 MHz",
    "137.5 MHz ≤ LVDS_CLK ≤ 154 MHz (default)",
    "Reserved",
    "Reserved",
])
print_variable("HS_CLK_SRC", 0x0A, 0, conv=[
    "LVDS pixel clock derived from input REFCLK (default)",
    "LVDS pixel clock derived from MIPI D-PHY channel A HS continuous clock",
])


print("\n")
print_variable("REG0B                           ", 0x0B, 7, 0)
print_variable("DSI_CLK_DIVIDER", 0x0B, 7, 3, conv=(
        ["LVDS clock = source clock (default)"] +
        [f"Divide by {n}" for n in range(2, 25+1)] +
        ["Reserved" for _ in range(0b11001, 0b11111+1)]
    )
)
print_variable("REFCLK_MULTIPLIER", 0x0B, 1, 0, conv=[
    "LVDS clock = source clock (default)",
    "Multiply by 2",
    "Multiply by 3",
    "Multiply by 4",
])

print('\n')
print_variable("REG0D                           ", 0x0D, 7, 0)
print_variable("PLL_EN", 0x0d, 0, conv=["PLL disabled", "PLL enabled"])

print('\n')
print_variable("REG10                           ", 0x10, 7, 0)
print_variable("CHA_DSI_LANES", 0x10, 4, 3, conv=[
    "Four lanes are enabled",
    "Three lanes are enabled",
    "Two lanes are enabled",
    "One lane is enabled (default)",
])
print_variable("SOT_ERR_TOL_DIS", 0x10, 0, conv=[
    "Single bit errors are tolerated for the start of transaction SoT leader sequence (default)",
    "No SoT bit errors are tolerated",
])

print('\n')
print_variable("REG11                           ", 0x11, 7, 0)
print_variable("CHA_DSI_DATA_EQ", 0x11, 7, 6, conv=[
    "No equalization (default)",
    "1 dB equalization",
    "Reserved",
    "2 dB equalization",
])
print_variable("CHA_DSI_CLK_EQ", 0x11, 3, 2, conv=[
    "No equalization (default)",
    "1 dB equalization",
    "Reserved",
    "2 dB equalization",
])

print('\n')
print_variable("REG12                           ", 0x12, 7, 0)
print_variable("CHA_DSI_CLK_RANGE", 0x12, 7, 0, conv=concat(
    ["Reserved"] * 8,
    [f"{n * 5} MHz <= DSI clock < {(n+1) * 5} MHz" for n in range(0x08, 0x64+1)],
    ["Reserved" for n in range(0x65, 0xFF+1)],
))

print('\n')
print_variable("REG18                           ", 0x18, 7, 0)
print_variable("DE_NEG_POLARITY", 0x18, 7, conv=[
    "DE is positive polarity driven ‘1’ during active pixel transmission on LVDS (default)",
    "DE is negative polarity driven ‘0’ during active pixel transmission on LVDS",
])
print_variable("HS_NEG_POLARITY", 0x18, 6, conv=[
    "HS is positive polarity driven ‘1’ during corresponding sync conditions",
    "HS is negative polarity driven ‘0’ during corresponding sync (default)",
])
print_variable("VS_NEG_POLARITY", 0x18, 5, conv=[
    "VS is positive polarity driven ‘1’ during corresponding sync conditions",
    "VS is negative polarity driven ‘0’ during corresponding sync (default)",
])
print_variable("CHA_24BPP_MODE", 0x18, 3, conv=[
    "Force 18bpp; LVDS channel A lane 4 (A_Y3P/N) is disabled (default)",
    "Force 24bpp; LVDS channel A lane 4 (B_Y3P/N) is enabled",
])
print_variable("CHA_24BPP_FORMAT1", 0x18, 1, conv=[
    "LVDS channel A lane A_Y3P/N transmits the 2 most significant bits (MSB) per color; Format 2 (default)",
    "LVDS channel B lane A_Y3P/N transmits the 2 least significant bits (LSB) per color; Format 1",
])

# Note1: This field must be ‘0’ when 18bpp data is received from
# DSI.
# Note2: If this field is set to ‘1’ and CHA_24BPP_MODE is ‘0’, the
# SN65DSI83-Q1 will convert 24bpp data to 18bpp data for
# transmission to an 18bpp panel. In this configuration, the
# SN65DSI83-Q1 will not transmit the 2 LSB per color on LVDS
# channel A, because LVDS channel A lane A_Y3P/N is disabled.


print('\n')
print_variable("REG19                           ", 0x19, 7, 0)
print_variable("CHA_LVDS_VOCM", 0x19, 6,  conv=[
    "LVDS Channel A common mode output voltage: 1.2V (default)",
    "LVDS Channel A common mode output voltage: 0.9V (CSR 0x1B.5:4 CHA_LVDS_CM_ADJUST must be set to ‘01b’)",
])
print_variable("CHA_LVDS_VOD_SWING", 0x19, 3, 2, conv=[
    textwrap.dedent("""
        LVDS differential output voltage:
                   100 Ω              200 Ω
               min. typ. max.     min. typ. max.
        data   180  245  330      150  204  275
        clock  140  191  262      117  159  220
    """).strip("\n"),
    textwrap.dedent("""
        LVDS differential output voltage: (default)
                   100 Ω              200 Ω
               min. typ. max.     min. typ. max.
        data   215  293  392      200  271  365
        clock  168  229  315      156  211  295
    """).strip("\n"),
    textwrap.dedent("""
        LVDS differential output voltage:
                   100 Ω              200 Ω
               min. typ. max.     min. typ. max.
        data   250  341  455      250  337  450
        clock  195  266  365      195  263  362
    """).strip("\n"),
    textwrap.dedent("""
        LVDS differential output voltage:
                   100 Ω              200 Ω
               min. typ. max.     min. typ. max.
        data   290  389  515      300  402  535
        clock  226  303  415      234  314  435
    """).strip("\n"),
])

print('\n')
print_variable("REG1A                           ", 0x1A, 7, 0)
print_variable("CHA_REVERSE_LVDS", 0x1A, 5, conv=["Normal LVDS Channel A pin order.", "Reversed LVDS Channel A pin order."])
print_variable("CHA_LVDS_TERM", 0x1A, 1, conv=["100Ω differential termination", "200Ω differential termination (default)"])


print('\n')
print_variable("REG1B                           ", 0x1B, 7, 0)
print_variable("CHA_LVDS_CM_ADJUST", 0x1B, 5, 4, conv=[
    "No change to common mode voltage (default)",
    "Adjust common mode voltage down 3%",
    "Adjust common mode voltage up 3%",
    "Adjust common mode voltage up 6%",
])


print('\n')
print_variable("REG20                           ", 0x20, 7, 0)
print_variable("REG21                           ", 0x20, 15, 8)
print_variable("CHA_ACTIVE_LINE_LENGTH_LOW", 0x20, 7, 0)
print_variable("CHA_ACTIVE_LINE_LENGTH_HIGH", 0x20, 11, 8)
print_variable("CHA_ACTIVE_LINE_LENGTH", 0x20, 11, 0, conv=lambda x: f"{x} pixels of the active horizontal line that are received on DSI Channel A and output to LVDS Channel A")


print('\n')
print_variable("REG24                           ", 0x24, 7, 0)
print_variable("REG25                           ", 0x24, 15, 8)
print_variable("CHA_VERTICAL_DISPLAY_SIZE_LOW", 0x24, 7, 0)
print_variable("CHA_VERTICAL_DISPLAY_SIZE_HIGH", 0x24, 11, 8)
print_variable("CHA_VERTICAL_DISPLAY_SIZE", 0x24, 11, 0, conv=lambda x: f"TEST PATTERN GENERATION PURPOSE ONLY. Vertical display size in lines = {x}")

print('\n')
print_variable("REG28                           ", 0x28, 7, 0)
print_variable("REG29                           ", 0x28, 15, 8)
print_variable("CHA_SYNC_DELAY_LOW", 0x28, 7, 0)
print_variable("CHA_SYNC_DELAY_HIGH", 0x28, 11, 8)
print_variable("CHA_SYNC_DELAY", 0x28, 11, 0, conv=lambda x: f"{x} pixel clocks from when an HSync or VSync is received on the DSI to when it is transmitted on the LVDS interface. The delay specified by this field is in addition to the pipeline and synchronization delays in the SN65DSI83-Q1. The additional delay is approximately 10 pixel clocks. The Sync delay must be programmed to at least 32 pixel clocks to ensure proper operation.")


print('\n')
print_variable("REG2C                           ", 0x2C, 7, 0)
print_variable("REG2D                           ", 0x2C, 15, 8)
print_variable("CHA_HSYNC_PULSE_WIDTH_LOW", 0x2C, 7, 0)
print_variable("CHA_HSYNC_PULSE_WIDTH_HIGH", 0x2D, 1, 0)
print_variable("CHA_HSYNC_PULSE_WIDTH", 0x2C, 9, 0, conv=lambda x: f"HSync Pulse Width = {x} pixel clocks")

print('\n')
print_variable("REG30                           ", 0x30, 7, 0)
print_variable("REG31                           ", 0x30, 15, 8)
print_variable("CHA_VSYNC_PULSE_WIDTH_LOW", 0x30, 7, 0)
print_variable("CHA_VSYNC_PULSE_WIDTH_HIGH", 0x31, 1, 0)
print_variable("CHA_VSYNC_PULSE_WIDTH", 0x30, 9, 0, conv=lambda x: f"VSync Pulse Width = {x} lines")

print('\n')
print_variable("REG34                           ", 0x34, 7, 0)
print_variable("CHA_HORIZONTAL_BACK_PORCH", 0x34, 7, 0, conv=lambda x: f"{x} pixel clocks between the end of the HSync Pulse and the start of the active video data (LVDS)")

print('\n')
print_variable("REG36                           ", 0x36, 7, 0)
print_variable("CHA_VERTICAL_BACK_PORCH", 0x36, 7, 0, conv=lambda x: f"TEST PATTERN GENERATION PURPOSE ONLY. {x} lines between the end of the VSync Pulse and the start of the active video data")

print('\n')
print_variable("REG38                           ", 0x38, 7, 0)
print_variable("CHA_HORIZONTAL_FRONT_PORCH", 0x38, 7, 0, conv=lambda x: f"TEST PATTERN GENERATION PURPOSE ONLY. {x} pixel clocks between the end of the active video data and the start of the HSync Pulse")

print('\n')
print_variable("REG3A                           ", 0x3A, 7, 0)
print_variable("CHA_VERTICAL_FRONT_PORCH", 0x3A, 7, 0, conv=lambda x: f"TEST PATTERN GENERATION PURPOSE ONLY. {x} lines between the end of the active video data and the start of the VSync Pulse")

print('\n')
print_variable("REG3C                           ", 0x3C, 7, 0)
print_variable("CHA_TEST_PATTERN", 0x3C, 4, conv=endis("Channel A test pattern"))

print('\n')
print_variable("REGE0                           ", 0xE0, 7, 0)
print_variable("IRQ_EN", 0xE0, 0, conv=[
    "IRQ output is high-impedance (default)",
    textwrap.dedent("""IRQ output is driven high when a bit is set in registers 0xE5
    that also has the corresponding IRQ_EN bit set to enable the
    interrupt condition""").strip(),
])

print('\n')
print_variable("REGE1                           ", 0xE1, 7, 0)
print_variable("CHA_SYNCH_ERR_EN", 0xE1, 7, conv=[
    "CHA_SYNCH_ERR is masked",
    "CHA_SYNCH_ERR is enabled to generate IRQ events",
])

print_variable("CHA_CRC_ERR_EN", 0xE1, 6, conv=[
    "CHA_CRC_ERR is masked",
    "CHA_CRC_ERR is enabled to generate IRQ events",
])

print_variable("CHA_UNC_ECC_ERR_EN", 0xE1, 5, conv=[
    "CHA_UNC_ECC_ERR is masked",
    "CHA_UNC_ECC_ERR is enabled to generate IRQ events",
])

print_variable("CHA_COR_ECC_ERR_EN", 0xE1, 4, conv=[
    "CHA_COR_ECC_ERR is masked",
    "CHA_COR_ECC_ERR is enabled to generate IRQ events",
])

print_variable("CHA_LLP_ERR_EN", 0xE1, 3, conv=[
    "CHA_LLP_ERR is masked",
    "CHA_ LLP_ERR is enabled to generate IRQ events",
])

print_variable("CHA_SOT_BIT_ERR_EN", 0xE1, 2, conv=[
    "CHA_SOT_BIT_ERR is masked",
    "CHA_SOT_BIT_ERR is enabled to generate IRQ events",
])
print_variable("PLL_UNLOCK_EN", 0xE1, 0, conv=[
    "PLL_UNLOCK is masked",
    "PLL_UNLOCK is enabled to generate IRQ events",
])

print('\n')
print_variable("REGE5                           ", 0xE5, 7, 0)
print_variable("CHA_SYNCH_ERR", 0xE5, 7, conv=["", """When the DSI channel A packet processor detects an HS or VS synchronization error, that is, an unexpected sync packet; this bit is set."""])
print_variable("CHA_CRC_ERR", 0xE5, 6, conv=["", """When the DSI channel A packet processor detects a data stream CRC error, this bit is set."""])
print_variable("CHA_UNC_ECC_ERR", 0xE5, 5, conv=["", """When the DSI channel A packet processor detects an uncorrectable ECC error, this bit is set."""])
print_variable("CHA_COR_ECC_ERR", 0xE5, 4, conv=["", """When the DSI channel A packet processor detects a correctable ECC error, this bit is set."""])
print_variable("CHA_LLP_ERR", 0xE5, 3, conv=["", """When the DSI channel A packet processor detects a low level protocol error, this bit is set. Low level protocol errors include SoT and EoT sync errors, Escape Mode entry command errors, LP transmission sync errors, and false control errors. Lane merge errors are reported by this status condition."""])
print_variable("CHA_SOT_BIT_ERR", 0xE5, 2, conv=["", """When the DSI channel A packet processor detects an SoT leader sequence bit error, this bit is set."""])
print_variable("PLL_UNLOCK", 0xE5, 0, conv=["", """This bit is set whenever the PLL Lock status transitions from LOCK to UNLOCK."""])

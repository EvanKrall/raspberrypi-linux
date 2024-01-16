#!/usr/bin/python3

import re
from smbus2 import SMBus
import textwrap
import shutil
import decimal


def drange(x, y, jump):
  while (x < y) if jump > 0 else (x > y):
    yield float(x)
    x += decimal.Decimal(jump)


I2C_ADDRESS = 0x18

with SMBus(1) as bus:
    regs = {}
    # for page in  range(0, 17) + range(26, 35) + range(44, 53) + range(62, 71):
    for page in [0, 1, 0x08, 0x2c]:
        bus.write_byte_data(I2C_ADDRESS, 0, page, force=True)
        regs[page] = [bus.read_byte_data(I2C_ADDRESS, reg, force=True) for reg in range(0, 0x7f)]
        assert page == bus.read_byte_data(I2C_ADDRESS, 0, force=True)


def bit(reg_num, bit_num):
    return (regs[page][reg_num] >> bit_num) & 0x01


def bitrange(page, reg_num, high_bit, low_bit, little_endian=True):

    if high_bit >= 8:
        assert high_bit < 16
        if little_endian:
            reg = regs[page][reg_num] + (regs[page][reg_num+1] << 8)
        else:
            reg = regs[page][reg_num] << 8 + (regs[page][reg_num+1])
    else:
        reg = regs[page][reg_num]
    mask = (2<<(high_bit - low_bit)) - 1
    return (reg >> low_bit) & mask


def print_variable(name, page, reg_num, high_bit, low_bit=None, conv=None):
    if low_bit is None:
        low_bit = high_bit
    bits = bitrange(page, reg_num, high_bit, low_bit)
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
    prefix = f"{name:>50}:   {bitstr}   "

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


    print("\n")
print_variable("Page00 Reg00", 0x00, 0x00, 7, 0)


print("\n")
print_variable("Page00 Reg04", 0x00, 0x04, 7, 0)
print_variable("Select PLL Range", 0x00, 0x04, 6, conv=["Low PLL Clock Range", "High PLL Clock Range"])
print_variable("Select PLL Range", 0x00, 0x04, 3, 2, conv=[
    'MCLK pin is input to PLL',
    'BCLK pin is input to PLL',
    'GPIO pin is input to PLL',
    'DIN pin is input to PLL',
])
print_variable("Select PLL Range", 0x00, 0x04, 1, 0, conv=[
    "MCLK pin is CODEC_CLKIN",
    "BCLK pin is CODEC_CLKIN",
    "GPIO pin is CODEC_CLKIN",
    "PLL Clock is CODEC_CLKIN",
])


print("\n")
print_variable("Page00 Reg05", 0x00, 0x05, 7, 0)
print_variable("PLL Power Up", 0x00, 0x05, 7)
print_variable("PLL divider P value", 0x00, 0x05, 6,4, conv=[
    "P=8",
    "P=1",
    "P=2",
    "P=3",
    "P=4",
    "P=5",
    "P=6",
    "P=7",
])
print_variable("PLL divider R value", 0x00, 0x05, 3, 0, conv=[
    "Reserved, do not use",
    "R=1",
    "R=2",
    "R=3",
    "R=4",
    "Reserved, do not use",
    "Reserved, do not use",
    "Reserved, do not use",
])

print("\n")
print_variable("Page00 Reg06", 0x00, 0x06, 7, 0)
print_variable("PLL divider J value", 0x00, 0x06, 5, 0, conv=lambda x: "Do not use" if x <= 0b11 else f"J={x}")

print("\n")
print_variable("Page00 Reg07-08", 0x00, 0x08, 15, 0)
print_variable("PLL divider D value", 0x00, 0x08, 13, 0, conv=lambda x: "Do not use" if x>9999 else f"D={x}")

print("\n")
print_variable("Page00 Reg0B", 0x00, 0x0B, 7, 0)
print_variable("NDAC Divider Power Control", 0x00, 0x0B, 7)
print_variable("NDAC value", 0x00, 0x0B, 6, 0, conv=lambda x: f"NDAC=128" if x==0 else f"NDAC={x}")

print("\n")
print_variable("Page00 Reg0C", 0x00, 0x0C, 7, 0)
print_variable("MDAC Divider Power Control", 0x00, 0x0C, 7)
print_variable("MDAC value", 0x00, 0x0C, 6, 0, conv=lambda x: f"MDAC=128" if x==0 else f"MDAC={x}")

print("\n")
print_variable("Page00 Reg0D-0E", 0x00, 0x0E, 15, 0)
print_variable("DAC OSR (DOSR) setting", 0x00, 0x0E, 10, 0, conv=lambda x: {0: "DOSR=1024", 1: "Reserved. Do not use.", 0x3ff: "Reserved. Do not use"}.get(x, f"DOSR={x}"))


print("\n")
print_variable("Page00 Reg12", 0x00, 0x12, 7, 0)
print_variable("NADC Clock Divider Power Control", 0x00, 0x12, 7, conv=[
    "NADC divider powered down, ADC_CLK is same as DAC_CLK",
    "NADC divider powered up",
])
print_variable("NADC value", 0x00, 0x12, 6, 0, conv=lambda x: "NADC=128" if x==0 else f"NADC={x}")


print("\n")
print_variable("Page00 Reg13", 0x00, 0x13, 7, 0)
print_variable("MADC Clock Divider Power Control", 0x00, 0x13, 7, conv=[
    "MADC divider powered down, ADC_MOD_CLK is same as DAC_MOD_CLK",
    "MADC divider powered up",
])
print_variable("MADC value", 0x00, 0x12, 6, 0, conv=lambda x: "MADC=128" if x==0 else f"MADC={x}")

print("\n")
print_variable("Page00 Reg14", 0x00, 0x14, 7, 0)
print_variable("ADC Oversampling (AOSR) value", 0x00, 0x14, 7, 0, conv=lambda x: {
            0: "AOSR = 256",
            0b0010_0000: "AOSR=32 (Use with PRB_R13 to PRB_R18, ADC Filter Type C)",
            0b0100_0000: "AOSR=64 (Use with PRB_R1 to PRB_R12, ADC Filter Type A or B)",
            0b1000_0000: "AOSR=128(Use with PRB_R1 to PRB_R6, ADC Filter Type A)",
        }.get(x, "Reserved. Do not use")
)


print("\n")
print_variable("Page00 Reg19", 0x00, 0x19, 7, 0)
print_variable("CDIV_CLKIN Clock Selection", 0x00, 0x19, 2, 0, conv={
    0b000: 'CDIV_CLKIN= MCLK',
    0b001: 'CDIV_CLKIN= BCLK',
    0b010: 'CDIV_CLKIN=DIN',
    0b011: 'CDIV_CLKIN=PLL_CLK',
    0b100: 'CDIV_CLKIN=DAC_CLK',
    0b101: 'CDIV_CLKIN=DAC_MOD_CLK',
    0b110: 'CDIV_CLKIN=ADC_CLK',
    0b111: 'CDIV_CLKIN=ADC_MOD_CLK',
})

print("\n")
print_variable("Page00 Reg1A", 0x00, 0x1A, 7, 0)
print_variable("CLKOUT M divider power control", 0x00, 0x1A, 7)
print_variable("CLKOUT M divider value", 0x00, 0x1A, 6, 0, conv=lambda x: "CLKOUT M divider=128" if x==0 else f"CLKOUT M divider={x}")

print("\n")
print_variable("Page00 Reg1B", 0x00, 0x1B, 7, 0)
print_variable("Audio Interface Selection", 0x00, 0x1B, 7, 6, conv={
    0b00: 'Audio Interface = I2S',
    0b01: 'Audio Interface = DSP',
    0b10: 'Audio Interface = RJF',
    0b11: 'Audio Interface = LJF',
})

print_variable("Audio Interface Selection", 0x00, 0x1B, 5, 4, conv={
    0b00: "Data Word length = 16 bits",
    0b01: "Data Word length = 20 bits",
    0b10: "Data Word length = 24 bits",
    0b11: "Data Word length = 32 bits",
})
print_variable("BCLK Direction Control", 0x00, 0x1B, 3, conv=["BCLK is input to the device", "BCLK is output from the device"])
print_variable("WCLK Direction Control", 0x00, 0x1B, 2, conv=["WCLK is input to the device", "WCLK is output from the device"])
print_variable("DOUT high impedance output", 0x00, 0x1B, 0, conv=[
    "DOUT will not be high impedance while Audio Interface is active",
    "DOUT will be high impedance after data has been transferred",
])

print("\n")
print_variable("Page00 Reg1C", 0x00, 0x1C, 7, 0)
print_variable("Data offset value", 0x00, 0x1C, 7, 0, conv=lambda x: f"Data offset={x} BCLK's")

print("\n")
print_variable("Page00 Reg1D", 0x00, 0x1D, 7, 0)
print_variable("Loopback control", 0x00, 0x1D, 5, conv=["No loopback", "Audio data in is routed to audio data out"])
print_variable("Loopback control", 0x00, 0x1D, 4, conv=["No loopback", "Stereo ADC output is routed to Stereo DAC input"])
print_variable("audio bit clock polarity", 0x00, 0x1D, 3, conv=["Default Bit Clock polarity", "Bit clock is inverted w.r.t. default polarity"])
print_variable("Primare BCLK/WCLK Power", 0x00, 0x1D, 2, conv=[
    'Priamry BCLK and Primary WCLK buffers are powered down when the codec is powered down',
    'Primary BCLK and Primary WCLK buffers are powered up when they are used in clock generation even when the codec is powered down',
])
print_variable("BDIV_CLKIN Multiplexer", 0x00, 0x1D, 1,0, conv=[
    'BDIV_CLKIN = DAC_CLK',
    'BDIV_CLKIN = DAC_MOD_CLK',
    'BDIV_CLKIN = ADC_CLK',
    'BDIV_CLKIN = ADC_MOD_CLK',
])


print("\n")
print_variable("Page00 Reg1e", 0x00, 0x1E, 7, 0)
print_variable("BCLK N Divider Power", 0x00, 0x1E, 7)
print_variable("BCLK N Divider value", 0x00, 0x1E, 6, 0, conv=lambda x: f"BCLK N divider=128" if x==0 else f"BCLK N divider={x}")


print("\n")
print_variable("Page00 Reg1F", 0x00, 0x1F, 7, 0)
print_variable("Secondary bit clock multiplexer", 0x00, 0x1F, 6, 5, conv=[
    "Secondary bit clock = GPIO",
    "Secondary bit clock = SCLK",
    "Secondary bit clock = MISO",
    "Secondary bit clock = DOUT",
])
print_variable("Secondary word clock multiplexer", 0x00, 0x1F, 4, 3, conv=[
    "Secondary word clock = GPIO",
    "Secondary word clock = SCLK",
    "Secondary word clock = MISO",
    "Secondary word clock = DOUT",
])
print_variable("ADC word clock multiplexer", 0x00, 0x1F, 2, 1, conv=[
    "ADC Word clock = GPIO",
    "ADC Word clock = SCLK",
    "ADC Word clock = MISO",
    "Do not use"
])
print_variable("Secondary Data Input Multiplexer", 0x00, 0x1F, 0, conv=[
    "Secondary data input = GPIO",
    "Secondary data input = SCLK",
])



print("\n")
print_variable("Page00 Reg20", 0x00, 0x20, 7, 0)
print_variable("Primary / Secondary Bit Clock Control", 0x00, 0x20, 3, conv=[
    "Primary Bit Clock(BCLK) is used for Audio Interface and Clocking",
    "Secondary Bit Clock is used for Audio Interface and Clocking",
])
print_variable("Primary / Secondary Word Clock Control", 0x00, 0x20, 2, conv=[
    "Primary Word Clock(WCLK) is used for Audio Interface",
    "Secondary Word Clock is used for Audio Interface",
])
print_variable("ADC Word Clock Control", 0x00, 0x20, 1, conv=[
    "ADC Word Clock is same as DAC Word Clock",
    "ADC Word Clock is Secondary ADC Word Clock",
])
print_variable("Audio Data In Control", 0x00, 0x20, 0, conv=[
    "DIN is used for Audio Data In",
    "Secondary Data In is used for Audio Data In",
])


def longest_common_prefix(*words):
    prefix = ""
    maxlen = min(len(word) for word in words)
    for i in range(maxlen):
        if all(word[i] == words[0][i] for word in words):
            prefix += words[0][i]
        else:
            break
    return prefix


def longest_common_suffix(*words):
    return longest_common_prefix(*(word[::-1] for word in words))[::-1]



def print_from_description(page, reg, description):
    print("\n")
    print_variable(f"Page{page:02x} Reg{reg:02x}", page, reg, 7, 0)
    lines = description.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("READ/ RESET BIT DESCRIPTION WRITE VALUE"):
            i += 1
            continue
        pattern = r"^D(?P<start>[0-7])(-D(?P<end>[0-7]))? R(/W)? [01X ]+ (?P<name>.*)$"
        match = re.match(pattern, line)
        assert match
        start = int(match.group("start"))
        end = match.group("end")
        end = int(end) if end is not None else start
        numbits = start - end + 1
        name = match.group("name")
        if "Reserved. Write only default values" in name or "Reserved. Do not use" in name:
            i += 1
            continue
        conv = {}
        conv_binary = True
        for j in range(i+1, len(lines)):
            convline = lines[j]
            if convmatch := re.match(r"^(?P<val>[0-9 ]+): (?P<desc>.*)$", convline):
                if conv_binary:
                    try:
                        val = int(convmatch.group("val").replace(" ", ""), 2)
                    except ValueError:
                        conv_binary = False
                if not conv_binary:
                    val = int(convmatch.group("val"))
                conv[val] = convmatch.group("desc")
            elif convmatch := re.match(r"^(?P<start>[0-9 ]+)-(?P<end>[0-9 ]+): (?P<desc>.*)$", convline):
                if conv_binary:
                    try:
                        convstart = int(convmatch.group("start").replace(" ", ""), 2)
                        convend = int(convmatch.group("end").replace(" ", ""), 2)
                    except ValueError:
                        conv_binary = False
                if not conv_binary:
                    convstart = int(convmatch.group("start"))
                    convend = int(convmatch.group("end"))
                dn = 1 if convend > convstart else -1
                for n in range(convstart, convend + dn, dn):
                    conv[n] = convmatch.group("desc")
            elif convline == "…" or convline == "...":
                before_dots_n_binary, before_dots = lines[j - 1].split(": ", 1)
                before_dots_n = int(before_dots_n_binary.replace(" ", ""), 2)
                after_dots_n_binary, after_dots = lines[j + 1].split(": ", 1)
                after_dots_n = int(after_dots_n_binary.replace(" ", ""), 2)
                prefix = longest_common_prefix(before_dots, after_dots)

                fixed_prefix_match = re.match(r"(?P<actual_prefix>.*)(?P<numeric_suffix>-?[0-9]+(\.[0-9]+)?)$", prefix)
                if fixed_prefix_match:
                    prefix = fixed_prefix_match.group("actual_prefix")

                before_dots_suffix_match = re.match(
                    r"(?P<number>-?[0-9.]+)(?P<suffix>.*)",
                    before_dots[len(prefix):],
                )
                after_dots_suffix_match = re.match(
                    r"(?P<number>-?[0-9.]+)(?P<suffix>.*)",
                    after_dots[len(prefix):],
                )
                suffix = before_dots_suffix_match.group("suffix")
                assert suffix == after_dots_suffix_match.group("suffix")

                before_dots_y = before_dots_suffix_match.group("number")
                before_dots_y = decimal.Decimal(before_dots_y)
                after_dots_y = after_dots_suffix_match.group("number")
                after_dots_y = decimal.Decimal(after_dots_y)

                dn = 1 if after_dots_n > before_dots_n else -1
                n_sequence = list(range(before_dots_n+dn, after_dots_n, dn))

                two = decimal.Decimal(2)

                if before_dots_y * two**(len(n_sequence) + 1) == after_dots_y:
                    y_sequence = [before_dots_y * two**x for x in range(len(n_sequence))]
                elif before_dots_y * two**-(len(n_sequence) + 1) == after_dots_y:
                    y_sequence = [before_dots_y * two**-x for x in range(len(n_sequence))]
                else:
                    dy = (after_dots_y - before_dots_y) / abs(after_dots_n - before_dots_n)
                    y_sequence = drange(before_dots_y+dy, after_dots_y, dy)
                for n, y in zip(n_sequence, y_sequence):
                    conv[n] = f"{prefix}{y}{suffix}"
            elif convline.startswith("Others: "):
                others_msg = convline.split(": ", 1)[1]
                for n in range(2**numbits):
                    conv.setdefault(n, others_msg)
            elif convline.startswith("Note: "):
                for k in conv:
                    conv[k] = f"{conv[k]} -- {convline}"
            else:
                # lines[j] isn't a conv line; let the outer while loop handle this
                i = j
                break
        else:
            # if nothing in for j in range(i+1, len(lines)) caused a break, no need for the outer loop to process anything else.
            i = len(lines)
        assert len(conv) == 0 or len(conv) == 2**numbits
        print_variable(name, page, reg, start, end, conv=conv)

print_from_description(0x00, 0x21, """
D7 R/W 0 BCLK Output Control
0: BCLK Output = Generated Primary Bit Clock
1: BCLK Output = Secondary Bit Clock Input
D6 R/W 0 Secondary Bit Clock Output Control
0: Secondary Bit Clock = BCLK input
1: Secondary Bit Clock = Generated Primary Bit Clock
D5-D4 R/W 00 WCLK Output Control
00: WCLK Output = Generated DAC_FS
01: WCLK Output = Generated ADC_FS
10: WCLK Output = Secondary Word Clock Input
11: Reserved. Do not use
D3-D2 R/W 00 Secondary Word Clock Output Control
00: Secondary Word Clock output = WCLK input
01: Secondary Word Clock output = Generated DAC_FS
10: Secondary Word Clock output = Generated ADC_FS
11: Reserved. Do not use
D1 R/W 0 Primary Data Out output control
0: DOUT output = Data Output from Serial Interface
1: DOUT output = Secondary Data Input (Loopback)
D0 R/W 0 Secondary Data Out output control
0: Secondary Data Output = DIN input (Loopback)
1: Secondary Data Output = Data output from Serial Interface
""")

print_from_description(0x00, 0x22, """
D7 R 0 Reserved. Write only default values
D6 R 0 Reserved. Write only default values
D5 R/W 0 I2C General Call Address Configuration
0: I2C General Call Address will be ignored
1: I2C General Call Address accepted
D4-D0 R 0 0000 Reserved. Write only default values
""")

print_from_description(0x00, 0x24, """
D7 R 0 Left ADC PGA Status Flag
0: Gain Applied in Left ADC PGA is not equal to Programmed Gain in Control Register
1: Gain Applied in Left ADC PGA is equal to Programmed Gain in Control Register
D6 R 0 Left ADC Power Status Flag
0: Left ADC Powered Down
1: Left ADC Powered Up
D5 R 0 Left AGC Gain Status.
0: Gain in Left AGC is not saturated
1: Gain in Left ADC is equal to maximum allowed gain in Left AGC
D4 R 0 Reserved. Write only default values
D3 R 0 Right ADC PGA Status Flag
0: Gain Applied in Right ADC PGA is not equal to Programmed Gain in Control Register
1: Gain Applied in Right ADC PGA is equal to Programmed Gain in Control Register
D2 R 0 Right ADC Power Status Flag
0: Right ADC Powered Down
1: Right ADC Powered Up
D1 R 0 Right AGC Gain Status.
0: Gain in Right AGC is not saturated
1: Gain in Right ADC is equal to maximum allowed gain in Right AGC
D0 R 0 Reserved. Write only default values
""")


print_from_description(0x00, 0x25, """
D7 R 0 Left DAC Power Status Flag
0: Left DAC Powered Down
1: Left DAC Powered Up
D6 R 0 Left Line Output Driver(LOL) Power Status Flag
0: LOL Powered Down
1: LOL Powered Up
D5 R 0 Left Headphone Driver (HPL) Power Status Flag
0: HPL Powered Down
1: HPL Powered Up
D4 R 0 Reserved. Write only default values
D3 R 0 Right DAC Power Status Flag
0: Right DAC Powered Down
1: Right DAC Powered Up
D2 R 0 Right Line Output Driver(LOR) Power Status Flag
0: LOR Powered Down
1: LOR Powered Up
D1 R 0 Right Headphone Driver (HPR) Power Status Flag
0: HPR Powered Down
1: HPR Powered Up
D0 R 0 Reserved. Write only default values
""")

print_from_description(0x00, 0x26, """
D7-D5 R 000 Reserved. Write only default values
D4 R 0 Left DAC PGA Status Flag
0: Gain applied in Left DAC PGA is not equal to Gain programmed in Control Register
1: Gain applied in Left DAC PGA is equal to Gain programmed in Control Register
D3-D1 R 000 Reserved. Write only default values
D0 R 0 Right DAC PGA Status Flag
0: Gain applied in Right DAC PGA is not equal to Gain programmed in Control Register
1: Gain applied in Right DAC PGA is equal to Gain programmed in Control Register
""")

print_from_description(0x00, 0x2A, """
D7 R 0 Left DAC Overflow Status.
0: No overflow in Left DAC
1: Overflow has happened in Left DAC since last read of this register
D6 R 0 Right DAC Overflow Status.
0: No overflow in Right DAC
1: Overflow has happened in Right DAC since last read of this register
D5-D4 R 00 Reserved. Write only default values
D3 R 0 Left ADC Overflow Status.
0: No overflow in Left ADC
1: Overflow has happened in Left ADC since last read of this register
D2 R 0 Right ADC Overflow Status.
0: No overflow in Right ADC
1: Overflow has happened in Right ADC since last read of this register
D1-D0 R 00 Reserved. Write only default values
""")

print_from_description(0x00, 0x2B, """
D7 R 0 Left DAC Overflow Status.
0: No overflow in Left DAC
1: Overflow condition is present in Left ADC at the time of reading the register
D6 R 0 Right DAC Overflow Status.
0: No overflow in Right DAC
1: Overflow condition is present in Right DAC at the time of reading the register
D5-D4 R 00 Reserved. Write only default values
D3 R 0 Left ADC Overflow Status.
0: No overflow in Left ADC
1: Overflow condition is present in Left ADC at the time of reading the register
D2 R 0 Right ADC Overflow Status.
0: No overflow in Right ADC
1: Overflow condition is present in Right ADC at the time of reading the register
D1-D0 R 0 Reserved. Write only default values
""")

print_from_description(0x00, 0x2C, """
D7 R 0 HPL Over Current Detect Flag
0: Over Current not detected on HPL
1: Over Current detected on HPL (will be cleared when the register is read)
D6 R 0 HPR Over Current Detect Flag
0: Over Current not detected on HPR
1: Over Current detected on HPR (will be cleared when the register is read)
D5 R 0 Headset Button Press
0: Button Press not detected
1: Button Press detected (will be cleared when the register is read)
D4 R 0 Headset Insertion/Removal Detect Flag
0: Insertion/Removal event not detected
1: Insertion/Removal event detected (will be cleared when the register is read)
D3 R 0 Left Channel DRC, Signal Threshold Flag
0: Signal Power is below Signal Threshold
1: Signal Power exceeded Signal Threshold (will be cleared when the register is read)
D2 R 0 Right Channel DRC, Signal Threshold Flag
0: Signal Power is below Signal Threshold
1: Signal Power exceeded Signal Threshold (will be cleared when the register is read)
D1-D0 R 00 Reserved. Write only default values
""")

print_from_description(0x00, 0x2D, """
D7 R 0 Reserved. Write only default values
D6 R 0 Left AGC Noise Threshold Flag
0: Signal Power is greater than Noise Threshold
1: Signal Power was lower than Noise Threshold (will be cleared when the register is read)
D5 R 0 Right AGC Noise Threshold Flag
0: Signal Power is greater than Noise Threshold
1: Signal Power was lower than Noise Threshold (will be cleared when the register is read)
D4-D3 R 00 Reserved. Write only default values
D2 R 0 Left ADC DC Measurement Data Available Flag
0: Data not available
1: Data available (will be cleared when the register is read)
D1 R 0 Right ADC DC Measurement Data Available Flag
0: Data not available
1: Data available (will be cleared when the register is read)
D0 R 0 Reserved. Write only default values
""")


print_from_description(0x00, 0x2E, """
D7 R 0 HPL Over Current Detect Flag
0: Over Current not detected on HPL
1: Over Current detected on HPL
D6 R 0 HPR Over Current Detect Flag
0: Over Current not detected on HPR
1: Over Current detected on HPR
D5 R 0 Headset Button Press
0: Button Press not detected
1: Button Press detected
D4 R 0 Headset Insertion/Removal Detect Flag
0: Headset removal detected
1: Headset insertion detected
D3 R 0 Left Channel DRC, Signal Threshold Flag
0: Signal Power is below Signal Threshold
1: Signal Power exceeded Signal Threshold
D2 R 0 Right Channel DRC, Signal Threshold Flag
0: Signal Power is below Signal Threshold
1: Signal Power exceeded Signal Threshold
D1-D0 R 00 Reserved. Write only default values
""")

print_from_description(0x00, 0x2F, """
D7 R 0 Reserved. Write only default values
D6 R 0 Left AGC Noise Threshold Flag
0: Signal Power is greater than Noise Threshold
1: Signal Power was lower than Noise Threshold
D5 R 0 Right AGC Noise Threshold Flag
0: Signal Power is greater than Noise Threshold
1: Signal Power was lower than Noise Threshold
D4-D3 R 00 Reserved. Write only default values
D2 R 0 Left ADC DC Measurement Data Available Flag
0: Data not available
1: Data available
D1 R 0 Right ADC DC Measurement Data Available Flag
0: Data not available
1: Data available
D0 R 0 Reserved. Write only default values
""")

print_from_description(0x00, 0x30, """
D7 R/W 0 INT1 Interrupt for Headset Insertion Event
0: Headset Insertion event will not generate a INT1 interrupt
1: Headset Insertion even will generate a INT1 interrupt
D6 R/W 0 INT1 Interrupt for Button Press Event
0: Button Press event will not generate a INT1 interrupt
1: Button Press event will generate a INT1 interrupt
D5 R/W 0 INT1 Interrupt for DAC DRC Signal Threshold
0: DAC DRC Signal Power exceeding Signal Threshold will not generate a INT1 interrupt
1: DAC DRC Signal Power exceeding Signal Threshold for either of Left or Right Channel will generate a INT1 interrupt. Read Page-0, Register-44 to distinguish between Left or Right Channel
D4 R/W 0 INT1 Interrupt for AGC Noise Interrupt
0: Noise level detected by AGC will not generate a INT1 interrupt
1: Noise level detected by either off Left or Right Channel AGC will generate a INT1 interrupt. Read Page-0, Register-45 to distinguish between Left or Right Channel
D3 R/W 0 INT1 Interrupt for Over Current Condition
0: Headphone Over Current condition will not generate a INT1 interrupt.
1: Headphone Over Current condition on either off Left or Right Channels will generate a INT1 interrupt. Read Page-0, Register-44 to distinguish between HPL and HPR
D2 R/W 0 INT1 Interrupt for overflow event
0: ADC or DAC data overflows does not result in a INT1 interrupt
1: ADC or DAC data overflow will result in a INT1 interrupt. Read Page-0, Register-42 to distinguish between ADC or DAC data overflow
D1 R/W 0 INT1 Interrupt for DC Measurement
0: DC Measurement data available will not generate INT1 interrupt
1: DC Measurement data available will generate INT1 interrupt
D0 R/W 0 INT1 pulse control
0: INT1 is active high interrupt of 1 pulse of approx. 2ms duration
1: INT1 is active high interrupt of multiple pulses, each of duration 2ms. To stop the pulse train, read Page-0, Reg-42d, 44d or 45d
""")


print_from_description(0x00, 0x31, """
D7 R/W 0 INT2 Interrupt for Headset Insertion Event
0: Headset Insertion event will not generate a INT2 interrupt
1: Headset Insertion even will generate a INT2 interrupt
D6 R/W 0 INT2 Interrupt for Button Press Event
0: Button Press event will not generate a INT2 interrupt
1: Button Press event will generate a INT2 interrupt
D5 R/W 0 INT2 Interrupt for DAC DRC Signal Threshold
0: DAC DRC Signal Power exceeding Signal Threshold will not generate a INT2 interrupt
1: DAC DRC Signal Power exceeding Signal Threshold for either of Left or Right Channel will generate a INT2 interrupt. Read Page-0, Register-44 to distinguish between Left or Right Channel
D4 R/W 0 INT2 Interrupt for AGC Noise Interrupt
0: Noise level detected by AGC will not generate a INT2 interrupt
1: Noise level detected by either off Left or Right Channel AGC will generate a INT2 interrupt. Read Page-0, Register-45 to distinguish between Left or Right Channel
D3 R/W 0 INT2 Interrupt for Over Current Condition
0: Headphone Over Current condition will not generate a INT2 interrupt.
1: Headphone Over Current condition on either off Left or Right Channels will generate a INT2 interrupt. Read Page-0, Register-44 to distinguish between HPL and HPR
D2 R/W 0 INT2 Interrupt for overflow event
0: ADC or DAC data overflow will not result in a INT2 interrupt
1: ADC or DAC data overflow will result in a INT2 interrupt. Read Page-0, Register-42 to distinguish between ADC or DAC data overflow
D1 R/W 0 INT2 Interrupt for DC Measurement
0: DC Measurement data available will not generate INT2 interrupt
1: DC Measurement data available will generate INT2 interrupt
D0 R/W 0 INT2 pulse control
0: INT2 is active high interrupt of 1 pulse of approx. 2ms duration
1: INT2 is active high interrupt of multiple pulses, each of duration 2ms. To stop the pulse train, read Page-0, Reg-42d, 44d and 45d
""")

print_from_description(0x00, 0x34, """
D7-D6 R 00 Reserved. Write only default values
D5-D2 R/W 0000 GPIO Control
0000: GPIO input/output disabled.
0001: GPIO input is used for secondary audio interface, digital microphone input or clock input. Configure other registers to choose the functionality of GPIO input
0010: GPIO is general purpose input
0011: GPIO is general purpose output
0100: GPIO output is CLKOUT
0101: GPIO output is INT1
0110: GPIO output is INT2
0111: GPIO output is ADC_WCLK for Audio Interface
1000: GPIO output is secondary bit-clock for Audio Interface
1001: GPIO output is secondary word-clock for Audio Interface
1010: GPIO output is clock for digital microphone
1011-1111: Reserved. Do not use.
D1 R X GPIO Input Pin state
D0 R/W 0 GPIO as general purpose output control
0: GPIO pin is driven to '0' in general purpose output mode
1: GPIO pin is driven to '1' in general purpose output mode
""")

print_from_description(0x00, 0x35, """
D7-D5 R 000 Reserved. Write only default values
D4 R/W 1 DOUT Bus Keeper Control
0: DOUT Bus Keeper Enabled
1: DOUT Bus Keeper Disabled
D3-D1 R/W 001 DOUT MUX Control
000: DOUT disabled
001: DOUT is Primary DOUT
010: DOUT is General Purpose Output
011: DOUT is CLKOUT
100: DOUT is INT1
101: DOUT is INT2
110: DOUT is Secondary BCLK
111: DOUT is Secondary WCLK
D0 R/W 0 DOUT as General Purpose Output
0: DOUT General Purpose Output is '0'
1: DOUT General Purpose Output is '1'
""")


print_from_description(0x00, 0x36, """
D7-D3 R 0 0000 Reserved. Write only reserved values
D2-D1 R/W 01 DIN function control
00: DIN pin is disabled
01: DIN is enabled for Primary Data Input or Digital Microphone Input or General Purpose Clock input
10: DIN is used as General Purpose Input
11: Reserved. Do not use
D0 R X DIN General Purpose Input value
""")


print_from_description(0x00, 0x37, """
D7-D5 R 000 Reserved. Write only default values
D4-D1 R/W 0001 MISO function control
0000: MISO buffer disabled
0001: MISO is used for data output in SPI interface, is disabled for I2C interface
0010: MISO is General Purpose Output
0011: MISO is CLKOUT output
0100: MISO is INT1 output
0101: MISO is INT2 output
0110: MISO is ADC Word Clock output
0111: MISO is clock output for Digital Microphone
1000: MISO is Secondary Data Output for Audio Interface
1001: MISO is Secondary Bit Clock for Audio Interface
1010: MISO is Secondary Word Clock for Audio Interface
1011-1111: Reserved. Do not use
D0 R/W 0 MISO pin General Purpose Output value
""")

print_from_description(0x00, 0x38, """
D7-D3 R 0 0000 Reserved. Write only default values
D2-D1 R/W 01 SCLK function control
00: SCLK pin is disabled
01: SCLK pin is enabled for SPI clock in SPI Interface mode or when in I2C Interface enabled for Secondary Data Input or Secondary Bit Clock Input or Secondary Word Clock or Secondary ADC Word Clock or Digital Microphone Input
10: SCLK is enabled as General Purpose Input
11: Reserved. Do not use
D0 R X SCLK General Purpose Input
""")
print_from_description(0x00, 0x3C, """
D7-D5 R 000 Reserved. Write only default values
D4-D0 R/W 0 0001 Selects the DAC (playback) signal processing block
0 0000: Reserved. Do not use
0 0001: DAC Signal Processing Block PRB_P1
0 0010: DAC Signal Processing Block PRB_P2
0 0011: DAC Signal Processing Block PRB_P3
0 0100: DAC Signal Processing Block PRB_P4
…
1 1000: DAC Signal Processing Block PRB_P24
1 1001: DAC Signal Processing Block PRB_P25
1 1010-1 1111: Reserved. Do not use
Note: Please check the overview section for description of the Signal Processing Blocks
""")

# Note: in 0x00 / 0x3D, the value 1 0010 is listed twice for D4-D0, once as ADC Signal Processing Block PRB_R18 and once as the beginning of the Reserved range.
# I've edited the description here.
print_from_description(0x00, 0x3D, """
D7-D5 R 000 Reserved. Write only default values
D4-D0 R/W 0 0001 Selects the ADC (recording) signal processing block
0 0000: Reserved. Do not use
0 0001: ADC Singal Processing Block PRB_R1
0 0010: ADC Signal Processing Block PRB_R2
0 0011: ADC Signal Processing Block PRB_R3
0 0100: ADC Signal Processing Block PRB_R4
…
1 0001: ADC Signal Processing Block PRB_R17
1 0010: ADC Signal Processing Block PRB_R18
1 0011-1 1111: Reserved. Do not use
Note: Please check the overview section for description of the Signal Processing Blocks
""")


print_from_description(0x00, 0x3E, """
D7-D0 R 0000 0000 Reserved. Write only default values
""")
print_from_description(0x00, 0x3F, """
D7 R/W 0 Left DAC Channel Power Control
0: Left DAC Channel Powered Down
1: Left DAC Channel Powered Up
D6 R/W 0 Right DAC Channel Power Control
0: Right DAC Channel Powered Down
1: Right DAC Channel Powered Up
D5-D4 R/W 01 Left DAC Data path Control
00: Left DAC data is disabled
01: Left DAC data Left Channel Audio Interface Data
10: Left DAC data is Right Channel Audio Interface Data
11: Left DAC data is Mono Mix of Left and Right Channel Audio Interface Data
D3-D2 R/W 01 Right DAC Data path Control
00: Right DAC data is disabled
01: Right DAC data Right Channel Audio Interface Data
10: Right DAC data is Left Channel Audio Interface Data
11: Right DAC data is Mono Mix of Left and Right Channel Audio Interface Data
D1-D0 R/W 00 DAC Channel Volume Control's Soft-Step control
00: Soft-Stepping is 1 step per 1 DAC Word Clock
01: Soft-Stepping is 1 step per 2 DAC Word Clocks
10: Soft-Stepping is disabled
11: Reserved. Do not use
""")


print_from_description(0x00, 0x40, """
D7 R/W 0 Right Modulator Output Control
0: When Right DAC Channel is powered down, the data is zero.
1: When Right DAC Channel is powered down, the data is inverted version of Left DAC Modulator Output. Can be used when differential mono output is used
D6-D4 R/W 000 DAC Auto Mute Control
000: Auto Mute disabled
001: DAC is auto muted if input data is DC for more than 100 consecutive inputs
010: DAC is auto muted if input data is DC for more than 200 consecutive inputs
011: DAC is auto muted if input data is DC for more than 400 consecutive inputs
100: DAC is auto muted if input data is DC for more than 800 consecutive inputs
101: DAC is auto muted if input data is DC for more than 1600 consecutive inputs
110: DAC is auto muted if input data is DC for more than 3200 consecutive inputs
111: DAC is auto muted if input data is DC for more than 6400 consecutive inputs
D3 R/W 1 Left DAC Channel Mute Control
0: Left DAC Channel not muted
1: Left DAC Channel muted
D2 R/W 1 Right DAC Channel Mute Control
0: Right DAC Channel not muted
1: Right DAC Channel muted
D1-D0 R/W 00 DAC Master Volume Control
00: Left and Right Channel have independent volume control
01: Left Channel Volume is controlled by Right Channel Volume Control setting
10: Right Channel Volume is controlled by Left Channel Volume Control setting
11: Reserved. Do not use
""")


print_from_description(0x00, 0x41, """
D7-D0 R/W 0000 0000 Left DAC Channel Digital Volume Control Setting
0111 1111-0011 0001: Reserved. Do not use
0011 0000: Digital Volume Control = +24dB
0010 1111: Digital Volume Control = +23.5dB
…
0000 0001: Digital Volume Control = +0.5dB
0000 0000: Digital Volume Control = 0.0dB
1111 1111: Digital Volume Control = -0.5dB
...
1000 0010: Digital Volume Control = -63dB
1000 0001: Digital Volume Control = -63.5dB
1000 0000: Reserved. Do not use
"""
)

print_from_description(0x00, 0x42, """
D7-D0 R/W 0000 0000 Right DAC Channel Digital Volume Control Setting
0111 1111-0011 0001: Reserved. Do not use
0011 0000: Digital Volume Control = +24dB
0010 1111: Digital Volume Control = +23.5dB
…
0000 0001: Digital Volume Control = +0.5dB
0000 0000: Digital Volume Control = 0.0dB
1111 1111: Digital Volume Control = -0.5dB
...
1000 0010: Digital Volume Control = -63dB
1000 0001: Digital Volume Control = -63.5dB
1000 0000: Reserved. Do not use
"""
)

print_from_description(0x00, 0x43, """
D7 R/W 0 Headset Detection
0: Headset Detection Disabled
1: Headset Detection Enabled
D6-D5 R 00 Headset Type Flag
00: Headset not detected
01: Stereo Headset detected
10: Reserved
11: Stereo + Cellular Headset detected
D4-D2 R/W 000 Headset Detection Debounce Programmability
000: Debounce Time = 16ms
001: Debounce Time = 32ms
010: Debounce Time = 64ms
011: Debounce Time = 128ms
100: Debounce Time = 256ms
101: Debounce Time = 512ms
110-111: Reserved. Do not use
D1-D0 R/W 00 Headset Button Press Debounce Programmability
00: Debounce disabled
01: Debounce Time = 8ms
10: Debounce Time = 16ms
11: Debounce Time = 32ms
""")

print_from_description(0x00, 0x44, """
D7 R 0 Reserved. Write only default values
D6 R/W 1 DRC Enable Control
0: Left Channel DRC disabled
1: Left Channel DRC enabled
Note: DRC only active if a PRB_Px has been selected that supports DRC
D5 R/W 1 DRC Enable Control
0: Right Channel DRC disabled
1: Right Channel DRC enabled
Note: DRC only active if a PRB_Px has been selected that supports DRC
D4-D2 R/W 011 DRC Threshold control
000: DRC Threshold = -3dBFS
001: DRC Threshold = -6dBFS
010: DRC Threshold = -9dBFS
011: DRC Threshold = -12dBFS
100: DRC Threshold = -15dBFS
101: DRC Threshold = -18dBFS
110: DRC Threshold = -21dBFS
111: DRC Threshold = -24dBFS
D1-D0 R/W 11 DRC Hysteresis Control
00: DRC Hysteresis = 0dB
01: DRC Hysteresis = 1dB
10: DRC Hysteresis = 2dB
11: DRC Hysteresis = 3dB
""")


print_from_description(0x00, 0x45, """
D7 R 0 Reserved. Write only default values.
D6-D3 R/W 0111 DRC Hold Programmability
0000: DRC Hold Disabled
0001: DRC Hold Time = 32 DAC Word Clocks
0010: DRC Hold Time = 64 DAC Word Clocks
0011: DRC Hold Time = 128 DAC Word Clocks
0100: DRC Hold Time = 256 DAC Word Clocks
0101: DRC Hold Time = 512 DAC Word Clocks
0110: DRC Hold Time = 1024 DAC Word Clocks
0111: DRC Hold Time = 2048 DAC Word Clocks
1000: DRC Hold Time = 4096 DAC Word Clocks
1001: DRC Hold Time = 8192 DAC Word Clocks
1010: DRC Hold Time = 16384 DAC Word Clocks
1011: DRC Hold Time = 32768 DAC Word Clocks
1100: DRC Hold Time = 2*32768 DAC Word Clocks
1101: DRC Hold Time = 3*32768 DAC Word Clocks
1110: DRC Hold Time = 4*32768 DAC Word Clocks
1111: DRC Hold Time = 5*32768 DAC Word Clocks
D2-D0 R/W 000 Reserved. Write only default values
""")


print_from_description(0x00, 0x46, """
D7-D4 R/W 0000 DRC Attack Rate control
0000: DRC Attack Rate = 4.0dB per DAC Word Clock
0001: DRC Attack Rate = 2.0dB per DAC Word Clock
0010: DRC Attack Rate = 1.0dB per DAC Word Clock
0011: DRC Attack Rate = 0.5dB per DAC Word Clock
0100: DRC Attack Rate = 0.25dB per DAC Word Clock
0101: DRC Attack Rate = 0.125dB per DAC Word Clock
0110: DRC Attack Rate = 0.0625dB per DAC Word Clock
0111: DRC Attack Rate = 0.03125dB per DAC Word Clock
1000: DRC Attack Rate = 1.5625e-2dB per DAC Word Clock
1001: DRC Attack Rate = 7.8125e-3dB per DAC Word Clock
1010: DRC Attack Rate = 3.9062e-3dB per DAC Word Clock
1011: DRC Attack Rate = 1.9531e-3dB per DAC Word Clock
1100: DRC Attack Rate = 9.7656e-4dB per DAC Word Clock
1101: DRC Attack Rate = 4.8828e-4dB per DAC Word Clock
1110: DRC Attack Rate = 2.4414e-4dB per DAC Word Clock
1111: DRC Attack Rate = 1.2207e-4dB per DAC Word Clock
D3-D0 R/W 0000 DRC Decay Rate control
0000: DRC Decay Rate = 1.5625e-2dB per DAC Word Clock
0001: DRC Decay Rate = 7.8125e-3dB per DAC Word Clock
0010: DRC Decay Rate = 3.9062e-3dB per DAC Word Clock
0011: DRC Decay Rate = 1.9531e-3dB per DAC Word Clock
0100: DRC Decay Rate = 9.7656e-4dB per DAC Word Clock
0101: DRC Decay Rate = 4.8828e-4dB per DAC Word Clock
0110: DRC Decay Rate = 2.4414e-4dB per DAC Word Clock
0111: DRC Decay Rate = 1.2207e-4dB per DAC Word Clock
1000: DRC Decay Rate = 6.1035e-5dB per DAC Word Clock
1001: DRC Decay Rate = 3.0517e-5dB per DAC Word Clock
1010: DRC Decay Rate = 1.5258e-5dB per DAC Word Clock
1011: DRC Decay Rate = 7.6293e-6dB per DAC Word Clock
1100: DRC Decay Rate = 3.8146e-6dB per DAC Word Clock
1101: DRC Decay Rate = 1.9073e-6dB per DAC Word Clock
1110: DRC Decay Rate = 9.5367e-7dB per DAC Word Clock
1111: DRC Decay Rate = 4.7683e-7dB per DAC Word Clock
""")
print_from_description(0x00, 0x47, """
D7 R/W 0 Beep Generator
0: Beep Generator Disabled
1: Beep Generator Enabled. This bit will self clear after the beep has been generated.
D6 R 0 Reserved. Write only default values
D5-D0 R/W 00 0000 Left Channel Beep Volume Control
00 0000: Left Channel Beep Volume = 0dB
00 0001: Left Channel Beep Volume = -1dB
…
11 1110: Left Channel Beep Volume = -62dB
11 1111: Left Channel Beep Volume = -63dB
""")

print_from_description(0x00, 0x48, """
D7-D6 R/W 00 Beep Generator Master Volume Control Setting
00: Left and Right Channels have independent Volume Settings
01: Left Channel Beep Volume is the same as programmed for Right Channel
10: Right Channel Beep Volume is the same as programmed for Left Channel
11: Reserved. Do not use
D5-D0 R 00 0000 Right Channel Beep Volume Control
00 0000: Right Channel Beep Volume = 0dB
00 0001: Right Channel Beep Volume = -1dB
…
11 1110: Right Channel Beep Volume = -62dB
11 1111: Right Channel Beep Volume = -63dB
""")
print_from_description(0x00, 0x49, """
D7-D0 R/W 0000 0000 Programmed value is Beep Sample Length(23:16)
""")
print_from_description(0x00, 0x4A, """
D7-D0 R/W 0000 0000 Programmed value is Beep Sample Length(15:8)
""")
print_from_description(0x00, 0x4B, """
D7-D0 R/W 1110 1110 Programmed value is Beep Sample Length(7:0)
""")
print_variable("Beep sin frequency", 0x00, 0x4D, 15, 0, conv=lambda x: f"frequency = {x} / DAC sample rate")
print_variable("Beep cos frequency", 0x00, 0x4F, 15, 0, conv=lambda x: f"frequency = {x} / DAC sample rate")



print_from_description(0x00, 0x51, """
D7 R/W 0 Left Channel ADC Power Control
0: Left Channel ADC is powered down
1: Left Channel ADC is powered up
D6 R/W 0 Right Channel ADC Power Control
0: Right Channel ADC is powered down
1: Right Channel ADC is powered up
D5-D4 R/W 00 Digital Microphone Input Configuration
00: GPIO serves as Digital Microphone Input
01: SCLK serves as Digital Microphone Input
10: DIN serves as Digital Microphone Input
11: Reserved. Do not use
D3 R/W 0 Left Channel Digital Microphone Power Control
0: Left Channel ADC not configured for Digital Microphone
1: Left Channel ADC configured for Digital Microphone
D2 R/W 0 Right Channel Digital Microphone Power Control
0: Right Channel ADC not configured for Digital Microphone
1: Right Channel ADC configured for Digital Microphone
D1-D0 R/W 00 ADC Volume Control Soft-Stepping Control
00: ADC Volume Control changes by 1 gain step per ADC Word Clock
01: ADC Volume Control changes by 1 gain step per two ADC Word Clocks
10: ADC Volume Control Soft-Stepping disabled
11: Reserved. Do not use
""")
print_from_description(0x00, 0x52, """
D7 R/W 1 Left ADC Channel Mute Control
0: Left ADC Channel Un-muted
1: Left ADC Channel Muted
D6-D4 R/W 000 Left ADC Channel Fine Gain Adjust
000: Left ADC Channel Fine Gain = 0dB
111: Left ADC Channel Fine Gain = -0.1dB
110: Left ADC Channel Fine Gain = -0.2dB
101: Left ADC Channel Fine Gain = -0.3dB
100: Left ADC Channel Fine Gain = -0.4dB
001-011: Reserved. Do not use
D3 R/W 1 Right ADC Channel Mute Control
0: Right ADC Channel Un-muted
1: Right ADC Channel Muted
D2-D0 R/W 000 Right ADC Channel Fine Gain Adjust
000: Right ADC Channel Fine Gain = 0dB
111: Right ADC Channel Fine Gain = -0.1dB
110: Right ADC Channel Fine Gain = -0.2dB
101: Right ADC Channel Fine Gain = -0.3dB
100: Right ADC Channel Fine Gain = -0.4dB
001-011: Reserved. Do not use
""")


print_from_description(0x00, 0x53, """
D7 R 0 Reserved. Write only default values
D6-D0 R/W 000 0000 Left ADC Channel Volume Control
000 0000-110 0111: Reserved. Do not use
110 1000: Left ADC Channel Volume = -12dB
110 1001: Left ADC Channel Volume = -11.5dB
110 1010: Left ADC Channel Volume = -11.0dB
…
111 1111: Left ADC Channel Volume = -0.5dB
000 0000: Left ADC Channel Volume = 0.0dB
000 0001: Left ADC Channel Volume = 0.5dB
...
010 0110: Left ADC Channel Volume = 19.0dB
010 0111: Left ADC Channel Volume = 19.5dB
010 1000: Left ADC Channel Volume = 20.0dB
010 1001-111 1111: Reserved. Do not use
""")
print_from_description(0x00, 0x54, """
D7 R 0 Reserved. Write only default values
D6-D0 R/W 000 0000 Right ADC Channel Volume Control
000 0000-110 0111: Reserved. Do not use
110 1000: Right ADC Channel Volume = -12dB
110 1001: Right ADC Channel Volume = -11.5dB
110 1010: Right ADC Channel Volume = -11.0dB
…
111 1111: Right ADC Channel Volume = -0.5dB
000 0000: Right ADC Channel Volume = 0.0dB
000 0001: Right ADC Channel Volume = 0.5dB
...
010 0110: Right ADC Channel Volume = 19.0dB
010 0111: Right ADC Channel Volume = 19.5dB
010 1000: Right ADC Channel Volume = 20.0dB
010 1001-111 1111: Reserved. Do not use
""")
print_from_description(0x00, 0x55, """
D7-D0 R/W 0000 0000 ADC Phase Compensation Control
1000 0000-1111 1111: Left ADC Channel Data is delayed with respect to Right ADC Channel Data. For details of delayed amount please refer to the description of Phase Compensation in the Overview section.
0000 0000: Left and Right ADC Channel data are not delayed with respect to each other
0000 0001-0111 1111: Right ADC Channel Data is delayed with respect to Left ADC Channel Data. For details of delayed amount please refer to the description of Phase Compensation in the Overview section.
""")
print_from_description(0x00, 0x56, """
D7 R/W 0 Left Channel AGC
0: Left Channel AGC Disabled
1: Left Channel AGC Enabled
D6-D4 R/W 000 Left Channel AGC Target Level Setting
000: Left Channel AGC Target Level = -5.5dBFS
001: Left Channel AGC Target Level = -8.0dBFS
010: Left Channel AGC Target Level = -10.0dBFS
011: Left Channel AGC Target Level = -12.0dBFS
100: Left Channel AGC Target Level = -14.0dBFS
101: Left Channel AGC Target Level = -17.0dBFS
110: Left Channel AGC Target Level = -20.0dBFS
111: Left Channel AGC Target Level = -24.0dBFS
D3-D2 R 00 Reserved. Write only default values
D1-D0 R/W 00 Left Channel AGC Gain Hysteresis Control
00: Left Channel AGC Gain Hysteresis is disabled
01: Left Channel AGC Gain Hysteresis is ±0.5dB
10: Left Channel AGC Gain Hysteresis is ±1.0dB
11: Left Channel AGC Gain Hysteresis is ±1.5dB
""")


print_from_description(0x00, 0x57, """
D7-D6 R/W 00 Left Channel AGC Hysteresis Setting
00: Left Channel AGC Hysteresis is 1.0dB
01: Left Channel AGC Hysteresis is 2.0dB
10: Left Channel AGC Hysteresis is 4.0dB
11: Left Channel AGC Hysteresis is disabled
D5-D1 R/W 0 0000 Left Channel AGC Noise Threshold
0 0000: Left Channel AGC Noise Gate disabled
0 0001: Left Channel AGC Noise Threshold is -30dB
0 0010: Left Channel AGC Noise Threshold is -32dB
0 0011: Left Channel AGC Noise Threshold is -34dB
…
1 1101: Left Channel AGC Noise Threshold is -86dB
1 1110: Left Channel AGC Noise Threshold is -88dB
1 1111: Left Channel AGC Noise Threshold is -90dB
D0 R 0 Reserved. Write only default values
""")
print_from_description(0x00, 0x58, """
D7 R 0 Reserved. Write only default values
D6-D0 R/W 111 1111 Left Channel AGC Maximum Gain Setting
000 0000: Left Channel AGC Maximum Gain = 0.0dB
000 0001: Left Channel AGC Maximum Gain = 0.5dB
000 0010: Left Channel AGC Maximum Gain = 1.0dB
…
111 0011: Left Channel AGC Maximum Gain = 57.5dB
111 0100: Left Channel AGC Maximum Gain = 58.0dB
111 0101-111 1111: not recommended for usage, Left Channel AGC Maximum Gain = 58.0dB
""")
print_from_description(0x00, 0x59, """
D7-D3 R/W 0 0000 Left Channel AGC Attack Time Setting
0 0000: Left Channel AGC Attack Time = 1*32 ADC Word Clocks
0 0001: Left Channel AGC Attack Time = 3*32 ADC Word Clocks
0 0010: Left Channel AGC Attack Time = 5*32 ADC Word Clocks
…
1 1101: Left Channel AGC Attack Time = 59*32 ADC Word Clocks
1 1110: Left Channel AGC Attack Time = 61*32 ADC Word Clocks
1 1111: Left Channel AGC Attack Time = 63*32 ADC Word Clocks
D2-D0 R/W 000 Left Channel AGC Attack Time Scale Factor Setting
000: Scale Factor = 1
001: Scale Factor = 2
010: Scale Factor = 4
…
101: Scale Factor = 32
110: Scale Factor = 64
111: Scale Factor = 128
D7-D3 R/W 0 0000 Left Channel AGC Decay Time Setting
0 0000: Left Channel AGC Decay Time = 1*512 ADC Word Clocks
0 0001: Left Channel AGC Decay Time = 3*512 ADC Word Clocks
0 0010: Left Channel AGC Decay Time = 5*512 ADC Word Clocks
…
1 1101: Left Channel AGC Decay Time = 59*512 ADC Word Clocks
1 1110: Left Channel AGC Decay Time = 61*512 ADC Word Clocks
1 1111: Left Channel AGC Decay Time = 63*512 ADC Word Clocks
D2-D0 R/W 000 Left Channel AGC Decay Time Scale Factor Setting
000: Scale Factor = 1
001: Scale Factor = 2
010: Scale Factor = 4
…
101: Scale Factor = 32
110: Scale Factor = 64
111: Scale Factor = 128
""")


print_from_description(0x00, 0x5A, """
D7-D3 R/W 0 0000 Left Channel AGC Decay Time Setting
0 0000: Left Channel AGC Decay Time = 1*512 ADC Word Clocks
0 0001: Left Channel AGC Decay Time = 3*512 ADC Word Clocks
0 0010: Left Channel AGC Decay Time = 5*512 ADC Word Clocks
…
1 1101: Left Channel AGC Decay Time = 59*512 ADC Word Clocks
1 1110: Left Channel AGC Decay Time = 61*512 ADC Word Clocks
1 1111: Left Channel AGC Decay Time = 63*512 ADC Word Clocks
D2-D0 R/W 000 Left Channel AGC Decay Time Scale Factor Setting
000: Scale Factor = 1
001: Scale Factor = 2
010: Scale Factor = 4
…
101: Scale Factor = 32
110: Scale Factor = 64
111: Scale Factor = 128
""")
print_from_description(0x00, 0x5B, """
D7-D5 R 000 Reserved. Write only default values
D4-D0 R/W 0 0000 Left Channel AGC Noise Debounce Time Setting
0 0000: UNKNOWN -- Error in datasheet
0 0001: Left Channel AGC Noise Debounce Time = 0
0 0010: Left Channel AGC Noise Debounce Time = 4 ADC Word Clocks
0 0011: Left Channel AGC Noise Debounce Time = 8 ADC Word Clocks
…
0 1010: Left Channel AGC Noise Debounce Time = 2048 ADC Word Clocks
0 1011: Left Channel AGC Noise Debounce Time = 4096 ADC Word Clocks
0 1100: Left Channel AGC Noise Debounce Time = 2*4096 ADC Word Clocks
0 1101: Left Channel AGC Noise Debounce Time = 3*4096 ADC Word Clocks
...
1 1101: Left Channel AGC Noise Debounce Time = 19*4096 ADC Word Clocks
1 1110: Left Channel AGC Noise Debounce Time = 20*4096 ADC Word Clocks
1 1111: Left Channel AGC Noise Debounce Time = 21*4096 ADC Word Clocks
""")
print_from_description(0x00, 0x5C, """
D7-D4 R 0000 Reserved. Write only default values
D3-D0 R/W 0000 Left Channel AGC Signal Debounce Time Setting
0000: UNKNOWN -- Error in datasheet
0001: Left Channel AGC Signal Debounce Time = 0
0010: Left Channel AGC Signal Debounce Time = 4 ADC Word Clocks
0011: Left Channel AGC Signal Debounce Time = 8 ADC Word Clocks
…
1001: Left Channel AGC Signal Debounce Time = 1024 ADC Word Clocks
1010: Left Channel AGC Signal Debounce Time = 2048 ADC Word Clocks
1011: Left Channel AGC Signal Debounce Time = 2*2048 ADC Word Clocks
1100: Left Channel AGC Signal Debounce Time = 3*2048 ADC Word Clocks
1101: Left Channel AGC Signal Debounce Time = 4*2048 ADC Word Clocks
1110: Left Channel AGC Signal Debounce Time = 5*2048 ADC Word Clocks
1111: Left Channel AGC Signal Debounce Time = 6*2048 ADC Word Clocks
""")


print_from_description(0x00, 0x5D, """
D7-D0 R 0000 0000 Left Channel AGC Gain Flag
1000 0000-1110 0111: UNSPECIFIED IN DATASHEET
1110 1000: Left Channel AGC Gain = -12.0dB
1110 1001: Left Channel AGC Gain = -11.5dB
1110 1010: Left Channel AGC Gain = -11.0dB
…
1111 1111: Left Channel AGC Gain = -0.5dB
0000 0000: Left Channel AGC Gain = 0.0dB
0000 0001: Left Channel AGC Gain = 0.5dB
…
0111 0010: Left Channel AGC Gain = 57.0dB
0111 0011: Left Channel AGC Gain = 57.5dB
0111 0100: Left Channel AGC Gain = 58.0dB
0111 0101-0111 1111: UNSPECIFIED IN DATASHEET
""")
print_from_description(0x00, 0x5E, """
D7 R/W 0 Right Channel AGC
0: Right Channel AGC Disabled
1: Right Channel AGC Enabled
D6-D4 R/W 000 Right Channel AGC Target Level Setting
000: Right Channel AGC Target Level = -5.5dBFS
001: Right Channel AGC Target Level = -8.0dBFS
010: Right Channel AGC Target Level = -10.0dBFS
011: Right Channel AGC Target Level = -12.0dBFS
100: Right Channel AGC Target Level = -14.0dBFS
101: Right Channel AGC Target Level = -17.0dBFS
110: Right Channel AGC Target Level = -20.0dBFS
111: Right Channel AGC Target Level = -24.0dBFS
D3-D2 R 00 Reserved. Write only default values
D1-D0 R/W 00 Right Channel AGC Gain Hysteresis Control
00: Right Channel AGC Gain Hysteresis is disabled
01: Right Channel AGC Gain Hysteresis is ±0.5dB
10: Right Channel AGC Gain Hysteresis is ±1.0dB
11: Right Channel AGC Gain Hysteresis is ±1.5dB
""")
print_from_description(0x00, 0x5F, """
D7-D6 R/W 00 Right Channel AGC Hysteresis Setting
00: Right Channel AGC Hysteresis is 1.0dB
01: Right Channel AGC Hysteresis is 2.0dB
10: Right Channel AGC Hysteresis is 4.0dB
11: Right Channel AGC Hysteresis is disabled
D5-D1 R/W 0 0000 Right Channel AGC Noise Threshold
0 0000: Right Channel AGC Noise Gate disabled
0 0001: Right Channel AGC Noise Threshold is -30dB
0 0010: Right Channel AGC Noise Threshold is -32dB
0 0011: Right Channel AGC Noise Threshold is -34dB
…
1 1101: Right Channel AGC Noise Threshold is -86dB
1 1110: Right Channel AGC Noise Threshold is -88dB
1 1111: Right Channel AGC Noise Threshold is -90dB
D0 R 0 Reserved. Write only default values
""")


print_from_description(0x00, 0x60, """
D7 R 0 Reserved. Write only default values
D6-D0 R/W 111 1111 Right Channel AGC Maximum Gain Setting
000 0000: Right Channel AGC Maximum Gain = 0.0dB
000 0001: Right Channel AGC Maximum Gain = 0.5dB
000 0010: Right Channel AGC Maximum Gain = 1.0dB
…
111 0011: Right Channel AGC Maximum Gain = 57.5dB
111 0100: Right Channel AGC Maximum Gain = 58.0dB
111 0101-111 1111: not recommended for usage, Right Channel AGC Maximum Gain = 58.0dB
""")
print_from_description(0x00, 0x61, """
D7-D3 R/W 0 0000 Right Channel AGC Attack Time Setting
0 0000: Right Channel AGC Attack Time = 1*32 ADC Word Clocks
0 0001: Right Channel AGC Attack Time = 3*32 ADC Word Clocks
0 0010: Right Channel AGC Attack Time = 5*32 ADC Word Clocks
…
1 1101: Right Channel AGC Attack Time = 59*32 ADC Word Clocks
1 1110: Right Channel AGC Attack Time = 61*32 ADC Word Clocks
1 1111: Right Channel AGC Attack Time = 63*32 ADC Word Clocks
D2-D0 R/W 000 Right Channel AGC Attack Time Scale Factor Setting
000: Scale Factor = 1
001: Scale Factor = 2
010: Scale Factor = 4
…
101: Scale Factor = 32
110: Scale Factor = 64
111: Scale Factor = 128
""")
print_from_description(0x00, 0x62, """
D7-D3 R/W 0 0000 Right Channel AGC Decay Time Setting
0 0000: Right Channel AGC Decay Time = 1*512 ADC Word Clocks
0 0001: Right Channel AGC Decay Time = 3*512 ADC Word Clocks
0 0010: Right Channel AGC Decay Time = 5*512 ADC Word Clocks
…
1 1101: Right Channel AGC Decay Time = 59*512 ADC Word Clocks
1 1110: Right Channel AGC Decay Time = 61*512 ADC Word Clocks
1 1111: Right Channel AGC Decay Time = 63*512 ADC Word Clocks
D2-D0 R/W 000 Right Channel AGC Decay Time Scale Factor Setting
000: Scale Factor = 1
001: Scale Factor = 2
010: Scale Factor = 4
…
101: Scale Factor = 32
110: Scale Factor = 64
111: Scale Factor = 128
""")


print_from_description(0x00, 0x63, """
D7-D5 R 000 Reserved. Write only default values
D4-D0 R/W 0 0000 Right Channel AGC Noise Debounce Time Setting
0 0000: UNSPECIFIED IN DATASHEET
0 0001: Right Channel AGC Noise Debounce Time = 0
0 0010: Right Channel AGC Noise Debounce Time = 4 ADC Word Clocks
0 0011: Right Channel AGC Noise Debounce Time = 8 ADC Word Clocks
…
0 1010: Right Channel AGC Noise Debounce Time = 2048 ADC Word Clocks
0 1011: Right Channel AGC Noise Debounce Time = 4096 ADC Word Clocks
0 1100: Right Channel AGC Noise Debounce Time = 2*4096 ADC Word Clocks
0 1101: Right Channel AGC Noise Debounce Time = 3*4096 ADC Word Clocks
...
1 1101: Right Channel AGC Noise Debounce Time = 19*4096 ADC Word Clocks
1 1110: Right Channel AGC Noise Debounce Time = 20*4096 ADC Word Clocks
1 1111: Right Channel AGC Noise Debounce Time = 21*4096 ADC Word Clocks
""")
print_from_description(0x00, 0x64, """
D7-D4 R 0000 Reserved. Write only default values
D3-D0 R/W 0000 Right Channel AGC Signal Debounce Time Setting
0000: UNSPECIFIED IN DATASHEET
0001: Right Channel AGC Signal Debounce Time = 0
0010: Right Channel AGC Signal Debounce Time = 4 ADC Word Clocks
0011: Right Channel AGC Signal Debounce Time = 8 ADC Word Clocks
…
1001: Right Channel AGC Signal Debounce Time = 1024 ADC Word Clocks
1010: Right Channel AGC Signal Debounce Time = 2048 ADC Word Clocks
1011: Right Channel AGC Signal Debounce Time = 2*2048 ADC Word Clocks
1100: Right Channel AGC Signal Debounce Time = 3*2048 ADC Word Clocks
1101: Right Channel AGC Signal Debounce Time = 4*2048 ADC Word Clocks
1110: Right Channel AGC Signal Debounce Time = 5*2048 ADC Word Clocks
1111: Right Channel AGC Signal Debounce Time = 6*2048 ADC Word Clocks
""")

print_from_description(0x00, 0x65, """
D7-D0 R 0000 0000 Right Channel AGC Gain Flag
1000 0000-1110 0111: UNSPECIFIED IN DATASHEET
1110 1000: Right Channel AGC Gain = -12.0dB
1110 1001: Right Channel AGC Gain = -11.5dB
1110 1010: Right Channel AGC Gain = -11.0dB
…
1111 1111: Right Channel AGC Gain = -0.5dB
0000 0000: Right Channel AGC Gain = 0.0dB
0000 0001: Right Channel AGC Gain = 0.5dB
…
0111 0010: Right Channel AGC Gain = 57.0dB
0111 0011: Right Channel AGC Gain = 57.5dB
0111 0100: Right Channel AGC Gain = 58.0dB
0111 0101-0111 1111: UNSPECIFIED IN DATASHEET
""")
print_from_description(0x00, 0x66, """
D7 R/W 0 DC Measurement Mode for Left ADC Channel
0: DC Measurement Mode disabled for Left ADC Channel
1: DC Measurement Mode enabled for Left ADC Channel
D6 R/W 0 DC Measurement Mode for Right ADC Channel
0: DC Measurement Mode disabled for Right ADC Channel
1: DC Measurement Mode enabled for Right ADC Channel
D5 R/W 0 DC Measurement filtering
0: DC Measurement is done using 1st order moving average filter with averaging of 2^D
1: DC Measurement is done with 1sr order Low-pass IIR filter with coefficients as a function of D
D4-D0 R/W 0 0000 DC Measurement D setting
0 0000: Reserved. Do not use
0 0001: DC Measurement D parameter = 1
0 0010: DC Measurement D parameter = 2
...
1 0011: DC Measurement D parameter = 19
1 0100: DC Measurement D parameter = 20
1 0101-1 1111: Reserved. Do not use
""")
print_from_description(0x00, 0x67, """
D7 R 0 Reserved. Write only default values
D6 R/W 0 DC measurement result update en/dis
0: Left and Right Channel DC measurement result update enabled
1: Left and Right Channel DC measurement result update disabled i.e. new results will be updated while old results are being read
D5 R/W 0 IIR-based DC measurement mode
0: For IIR based DC measurement, measurement value is the instantaneous output of IIR filter
1: For IIR based DC measurement, the measurement value is updated before periodic clearing of IIR filter
D4-D0 R/W 0 0000 IIR based DC Measurement, averaging time setting
0 0000: Infinite average is used
0 0001: Averaging time is 2^1 ADC Modulator clocks
0 0010: Averaging time is 2^2 ADC Modulator clocks
…
1 0011: Averaging time is 2^19 ADC Modulator clocks
1 0100: Averaging time is 2^20 ADC Modulator clocks
1 0101-1 1111: Reserved. Do not use
""")
print_from_description(0x00, 0x68, """
D7-D0 R 0000 0000 Left Channel DC Measurement Output (23:16)
""")
print_from_description(0x00, 0x69, """
D7-D0 R 0000 0000 Left Channel DC Measurement Output (15:8)
""")
print_from_description(0x00, 0x6A, """
D7-D0 R 0000 0000 Left Channel DC Measurement Output (7:0)
""")
print_from_description(0x00, 0x6B, """
D7-D0 R 0000 0000 Right Channel DC Measurement Output (23:16)
""")
print_from_description(0x00, 0x6C, """
D7-D0 R 0000 0000 Right Channel DC Measurement Output (15:8)
""")
print_from_description(0x00, 0x6D, """
D7-D0 R 0000 0000 Right Channel DC Measurement Output (7:0)
""")

### PAGE 1

print_from_description(0x01, 0x01, """
D7-D4 R 0000 Reserved. Write only default values
D3 R/W 0 -
0: AVDD will be weakly connected to DVDD. Use while AVDD is not externally powered
1: Disabled weak connection of AVDD with DVDD
D2 R/W 0 Reserved. Write only default values
D1-D0 R/W 00 Charge Pump Conrol and Configuration
00: Power Down Charge Pump
01: Reserved. Do not use.
10: Power Up Charge Pump with Internal Oscillator Clock (nom. 8MHz)
11: Reserved. Do not use.
""")
print_from_description(0x01, 0x02, """
D7-D6 R/W 00 Reserved. Write only default values
D5-D4 R/W 00 Reserved. Write only default values
D3 R/W 1 Analog Block Power Control
0: Analog Blocks Enabled
1: Analog Blocks Disabled
D2 R 0 Headphone Driver Powerup Flag.
0: The Headphone Driver is powered down or not yet completely powered up. This flag is conditional to Page 1 / Register 10 D2. For Page 1 / Register 10 D2 = 1 it shows the status of HPL else the status of HPR
1: The Headphone Driver is completely powered up. This flag is conditional to Page 1 / Register 10 D2. For Page 1 / Register 10 D2 = 1 it shows the status of HPL else the status of HPR
D1 R 0 Reserved.
D0 R/W 0 Reserved. Write only default values
""")
print_from_description(0x01, 0x03, """
D7-D6 R/W 00 Reserved. Write only default values
D5 R/W 0 Left DAC performance mode selection
0: Left DAC is enabled in high performance mode
1: Left DAC is enabled in normal mode
D4-D2 R/W 000 Left DAC PTM Control
000: Left DAC in mode PTM_P3, PTM_P4
001: Left DAC in mode PTM_P2
010: Left DAC in mode PTM_P1
011-111: Reserved. Do not use
D1-D0 R 00 Reserved. Write only default values
""")
print_from_description(0x01, 0x04, """
D7-D6 R/W 00 Reserved. Write only default values
D5 R/W 0 Right DAC performance mode selection
0: Right DAC is enabled in high performance mode
1: Right DAC is enabled in normal mode
D4-D2 R/W 000 Right DAC PTM Control
000: Right DAC in mode PTM_P3, PTM_P4
001: Right DAC in mode PTM_P2
010: Right DAC in mode PTM_P1
011-111: Reserved. Do not use
D1-D0 R 00 Reserved. Write only default values
""")
print_from_description(0x01, 0x09, """
D7-D6 R 00 Reserved. Write only default value
D5 R/W 0 -
0: HPL is powered down
1: HPL is powered up
D4 R/W 0 -
0: HPR is powered down
1: HPR is powered up
D3 R/W 0 -
0: LOL is powered down
1: LOL is powered up
D2 R/W 0 -
0: LOR is powered down
1: LOR is powered up
D1 R/W 0 -
0: Left Mixer Amplifier(MAL) is powered down
1: Left Mixer Amplifier(MAL) is powered up
D0 R/W 0 -
0: Right Mixer Amplifier(MAR) is powered down
1: Right Mixer Amplifier(MAR) is powered up
""")
print_from_description(0x01, 0x0A, """
D7 R 0 Reserved. Write only default value.
D6 R/W 0 -
0: Full Chip Common Mode is 0.9V
1: Full Chip Common Mode is 0.75V
D5-D4 R/W 00 -
00: Output Common Mode for HPL & HPR is same as full-chip common mode
01: Output Common Mode for HPL & HPR is 1.25V
10: Output Common Mode for HPL & HPR is 1.5V
11: Output Common Mode for HPL & HPR is 1.65V if D6=0, 1.5V if D6=1
D3 R/W 0 -
0: Output Common Mode for LOL & LOR is same as full-chip common mode
1: Output Common Mode for LOL & LOR is 1.65V and output is powered by DRVDD_HP. DRVDD_HP supply should be >3.3V & VNEG connected to AVSS.
D2 R/W 0 Ground Centered Headphone Flag Channel Selection.
0: Page 1 / Register 2 D2 will show status according to the following selection: Flag shows HPR status
1: Page 1 / Register 2 D2 will show status according to the following selection: Flag shows HPL status
D1-D0 R/W 00 GND SENSE Configuration
00: Enable GND_SENSE for ground centered mode of operation.
01: Do not use
10: Disable GND_SENSE for ground centered mode of operation
11: Do not use
""")
print_from_description(0x01, 0x0B, """
D7-D5 R 000 Reserved. Write only default values
D4 R/W 1 Reserved, Do not write '0'
D3-D1 R/W 000 -
000: No debounce is used for Over Current detection
001: Over Current detection is debounced by 8ms
010: Over Current detection is debounce by 16ms
011: Over Current detection is debounced by 32ms
100: Over Current detection is debounced by 64ms
101: Over Current detection is debounced by 128ms
110: Over Current detection is debounced by 256ms
111: Over Current detection is debounced by 512ms
D0 R/W 0 -
0: Output current will be limited if over current condition is detected
1: Output driver will be powered down if over current condition is detected
""")
print_from_description(0x01, 0x0C, """
D7-D4 R 0000 Reserved. Write only default values
D3 R/W 0 -
0: Left Channel DAC reconstruction filter's positive terminal is not routed to HPL
1: Left Channel DAC reconstruction filter's positive terminal is routed to HPL
D2 R/W 0 -
0: IN1L is not routed to HPL
1: IN1L is routed to HPL
D1 R/W 0 -
0: MAL output is not routed to HPL
1: MAL output is routed to HPL
D0 R/W 0 -
0: MAR output is not routed to HPL
1: MAR output is routed to HPL
""")
print_from_description(0x01, 0x0D, """
D7-D5 R 000 Reserved. Write only default values
D4 R/W 0 -
0: Left Channel DAC reconstruction filter's negative terminal is not routed to HPR
1: Left Channel DAC reconstruction filter's negative terminal is routed to HPR
D3 R/W 0 -
0: Right Channel DAC reconstruction filter's positive terminal is not routed to HPR
1: Right Channel DAC reconstruction filter's positive terminal is routed to HPR
D2 R/W 0 -
0: IN1R is not routed to HPR
1: IN1R is routed to HPR
D1 R/W 0 -
0: MAR output is not routed to HPR
1: MAR output is routed to HPR
D0 R/W 0 Reserved. Write only default values
""")
print_from_description(0x01, 0x0E, """
D7-D5 R 000 Reserved. Write only default values
D4 R/W 0 -
0: Right Channel DAC reconstruction filter's negative terminal is not routed to LOL
1: Right Channel DAC reconstruction filter's negative terminal is routed to LOL
D3 R/W 0 -
0: Left Channel DAC reconstruction filter output is not routed to LOL
1: Left Channel DAC reconstruction filter output is routed to LOL
D2 R 0 Reserved. Write only default value.
D1 R/W 0 -
0: MAL output is not routed to LOL
1: MAL output is routed to LOL
D0 R/W 0 -
0: LOR output is not routed to LOL
1: LOR output is routed to LOL(use when LOL&LOR output is powered by AVDD)
""")
print_from_description(0x01, 0x0F, """
D7-D4 R 0000 Reserved. Write only default values
D3 R/W 0 -
0: Right Channel DAC reconstruction filter output is not routed to LOR
1: Right Channel DAC reconstruction filter output is routed to LOR
D2 R 0 Reserved. Write only default value.
D1 R/W 0 -
0: MAR output is not routed to LOR
1: MAR output is routed to LOR
D0 R 0 Reserved. Write only default value.
""")
print_from_description(0x01, 0x10, """
D7 R 0 Reserved. Write only default value.
D6 R/W 1 -
0: HPL driver is not muted
1: HPL driver is muted
D5-D0 R/W 00 0000 -
10 0000-11 1001: Reserved. Do not use
11 1010: HPL driver gain is -6dB (Note: It is not possible to mute HPR while programmed to -6dB)
11 1011: HPL driver gain is -5dB
11 1100: HPL driver gain is -4dB
…
11 1111: HPL driver gain is -1dB
00 0000: HPL driver gain is 0dB
...
00 1110: HPL driver gain is 14dB
00 1111-01 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x11, """
D7 R 0 Reserved. Write only default value.
D6 R/W 1 -
0: HPR driver is not muted
1: HPR driver is muted
D5-D0 R/W 00 0000 -
10 0000-11 1001: Reserved. Do not use
11 1010: HPR driver gain is -6dB (Note: It is not possible to mute HPR while programmed to -6dB)
11 1011: HPR driver gain is -5dB
11 1100: HPR driver gain is -4dB
…
11 1111: HPR driver gain is -1dB
00 0000: HPR driver gain is 0dB
...
00 1110: HPR driver gain is 14dB
00 1111-01 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x12, """
D7 R 0 Reserved. Write only default value.
D6 R/W 1 -
0: LOL driver is not muted
1: LOL driver is muted
D5-D0 R/W 00 0000 -
10 0000-11 1001: Reserved. Do not use
11 1010: LOL driver gain is -6dB
11 1011: LOL driver gain is -5dB
11 1100: LOL driver gain is -4dB
…
11 1111: LOL driver gain is -1dB
00 0000: LOL driver gain is 0dB
...
01 1011: LOL driver gain is 27dB
01 1100: LOL driver gain is 28dB
01 1101: LOL driver gain is 29dB
01 1110-01 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x13, """
D7 R 0 Reserved. Write only default value.
D6 R/W 1 -
0: LOR driver is not muted
1: LOR driver is muted
D5-D0 R/W 00 0000 -
10 0000-11 1001: Reserved. Do not use
11 1010: LOR driver gain is -6dB
11 1011: LOR driver gain is -5dB
11 1100: LOR driver gain is -4dB
…
11 1111: LOR driver gain is -1dB
00 0000: LOR driver gain is 0dB
...
01 1011: LOR driver gain is 27dB
01 1100: LOR driver gain is 28dB
01 1101: LOR driver gain is 29dB
01 1110-01 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x14, """
D7-D6 R/W 00 -
00: Soft routing step time is 0ms
01: Soft routing step time is 50ms
10: Soft routing step time is 100ms
11: Soft routing step time is 200ms
D5-D2 R/W 0000 -
0000: Slow power up of headphone amp's is disabled
0001: Headphone amps power up slowly in 0.5 time constants
0010: Headphone amps power up slowly in 0.625 time constants
0011: Headphone amps power up slowly in 0.725 time constants
0100: Headphone amps power up slowly in 0.875 time constants
0101: Headphone amps power up slowly in 1.0 time constants
0110: Headphone amps power up slowly in 2.0 time constants
0111: Headphone amps power up slowly in 3.0 time constants
1000: Headphone amps power up slowly in 4.0 time constants
1001: Headphone amps power up slowly in 5.0 time constants
1010: Headphone amps power up slowly in 6.0 time constants
1011: Headphone amps power up slowly in 7.0 time constants
1100: Headphone amps power up slowly in 8.0 time constants
1101: Headphone amps power up slowly in 16.0 time constants ( do not use for Rchg=25K)
1110: Headphone amps power up slowly in 24.0 time constants (do not use for Rchg=25K)
1111: Headphone amps power up slowly in 32.0 time constants (do not use for Rchg=25K) Note: Time constants assume 47uF decoupling cap
D1-D0 R/W 00 -
00: Headphone amps power up time is determined with 25K resistance
01: Headphone amps power up time is determined with 6K resistance
10: Headphone amps power up time is determined with 2K resistance
11: Reserved. Do not use
""")


print_from_description(0x01, 0x16, """
D7 R 0 Reserved. Write only default value.
D6-D0 R/W 000 0000 IN1L to HPL Volume Control
000 0000: Volume Control = 0.0dB
000 0001: Volume Control = -0.5dB
000 0010: Volume Control = -1.0dB
000 0011: Volume Control = -1.5dB
000 0100: Volume Control = -2.0dB
000 0101: Volume Control = -2.5dB
000 0110: Volume Control = -3.0dB
000 0111: Volume Control = -3.5dB
000 1000: Volume Control = -4.0dB
000 1001: Volume Control = -4.5dB
000 1010: Volume Control = -5.0dB
000 1011: Volume Control = -5.5dB
000 1100: Volume Control = -6.0dB
000 1101: Volume Control = -7.0dB
000 1110: Volume Control = -8.0dB
000 1111: Volume Control = -8.5dB
001 0000: Volume Control = -9.0dB
001 0001: Volume Control = -9.5dB
001 0010: Volume Control = -10.0dB
001 0011: Volume Control = -10.5dB
001 0100: Volume Control = -11.0dB
001 0101: Volume Control = -11.5dB
001 0110: Volume Control = -12.0dB
001 0111: Volume Control = -12.5dB
001 1000: Volume Control = -13.0dB
001 1001: Volume Control = -13.5dB
001 1010: Volume Control = -14.0dB
001 1011: Volume Control = -14.5dB
001 1100: Volume Control = -15.0dB
001 1101: Volume Control = -15.5dB
001 1110: Volume Control = -16.0dB
001 1111: Volume Control = -16.5dB
010 0000: Volume Control = -17.1dB
010 0001: Volume Control = -17.5dB
010 0010: Volume Control = -18.1dB
010 0011: Volume Control = -18.6dB
010 0100: Volume Control = -19.1dB
010 0101: Volume Control = -19.6dB
010 0110: Volume Control = -20.1dB
010 0111: Volume Control = -20.6dB
010 1000: Volume Control = -21.1dB
010 1001: Volume Control = -21.6dB
010 1010: Volume Control = -22.1dB
010 1011: Volume Control = -22.6dB
010 1100: Volume Control = -23.1dB
010 1101: Volume Control = -23.6dB
010 1110: Volume Control = -24.1dB
010 1111: Volume Control = -24.6dB
011 0000: Volume Control = -25.1dB
011 0001: Volume Control = -25.6dB
011 0010: Volume Control = -26.1dB
011 0011: Volume Control = -26.6dB
011 0100: Volume Control = -27.1dB
011 0101: Volume Control = -27.6dB
011 0110: Volume Control = -28.1dB
011 0111: Volume Control = -28.6dB
011 1000: Volume Control = -29.1dB
011 1001: Volume Control = -29.6dB
011 1010: Volume Control = -30.1dB
011 1011: Volume Control = -30.6dB
011 1100: Volume Control = -31.1dB
011 1100: Volume Control = -31.6dB
011 1101: Volume Control = -32.1dB
011 1110: Volume Control = -32.6dB
011 1111: Volume Control = -33.1dB
100 0000: Volume Control = -33.6dB
100 0001: Volume Control = -34.1dB
100 0010: Volume Control = -34.6dB
100 0011: Volume Control = -35.2dB
100 0100: Volume Control = -35.7dB
100 0101: Volume Control = -36.2dB
100 0110: Volume Control = -36.7dB
100 0111: Volume Control = -37.2dB
100 1000: Volume Control = -37.7dB
100 1001: Volume Control = -38.2dB
100 1010: Volume Control = -38.7dB
100 1011: Volume Control = -39.2dB
100 1100: Volume Control = -39.7dB
100 1101: Volume Control = -40.2dB
100 1110: Volume Control = -40.7dB
100 1111: Volume Control = -41.2dB
101 0000: Volume Control = -41.7dB
101 0001: Volume Control = -42.1dB
101 0010: Volume Control = -42.7dB
101 0011: Volume Control = -43.2dB
101 0100: Volume Control = -43.8dB
101 0101: Volume Control = -44.3dB
101 0110: Volume Control = -44.8dB
101 0111: Volume Control = -45.2dB
101 1000: Volume Control = -45.8dB
101 1001: Volume Control = -46.2dB
101 1010: Volume Control = -46.7dB
101 1011: Volume Control = -47.4dB
101 1100: Volume Control = -47.9dB
101 1101: Volume Control = -48.2dB
101 1110: Volume Control = -48.7dB
101 1111: Volume Control = -49.3dB
110 0000: Volume Control = -50.0dB
110 0001: Volume Control = -50.3dB
110 0010: Volume Control = -51.0dB
110 0011: Volume Control = -51.42dB
110 0100: Volume Control = -51.82dB
110 0101: Volume Control = -52.3dB
110 0110: Volume Control = -52.7dB
110 0111: Volume Control = -53.7dB
110 1000: Volume Control = -54.2dB
110 1001: Volume Control = -55.4dB
110 1010: Volume Control = -56.7dB
110 1011: Volume Control = -58.3dB
110 1100: Volume Control = -60.2dB
110 1101: Volume Control = -62.7dB
110 1110: Volume Control = -64.3dB
110 1111: Volume Control = -66.2dB
111 0000: Volume Control = -68.7dB
111 0001: Volume Control = -72.3dB
111 0010: Volume Control = MUTE
111 0011-111 1111: Reserved. Do not use
""")

print_from_description(0x01, 0x17, """
D7 R 0 Reserved. Write only default value
D6-D0 R/W 000 0000 IN1R to HPR Volume Control
000 0000: Volume Control = 0.0dB
000 0001: Volume Control = -0.5dB
000 0010: Volume Control = -1.0dB
000 0011: Volume Control = -1.5dB
000 0100: Volume Control = -2.0dB
000 0101: Volume Control = -2.5dB
000 0110: Volume Control = -3.0dB
000 0111: Volume Control = -3.5dB
000 1000: Volume Control = -4.0dB
000 1001: Volume Control = -4.5dB
000 1010: Volume Control = -5.0dB
000 1011: Volume Control = -5.5dB
000 1100: Volume Control = -6.0dB
000 1101: Volume Control = -7.0dB
000 1110: Volume Control = -8.0dB
000 1111: Volume Control = -8.5dB
001 0000: Volume Control = -9.0dB
001 0001: Volume Control = -9.5dB
001 0010: Volume Control = -10.0dB
001 0011: Volume Control = -10.5dB
001 0100: Volume Control = -11.0dB
001 0101: Volume Control = -11.5dB
001 0110: Volume Control = -12.0dB
001 0111: Volume Control = -12.5dB
001 1000: Volume Control = -13.0dB
001 1001: Volume Control = -13.5dB
001 1010: Volume Control = -14.0dB
001 1011: Volume Control = -14.5dB
001 1100: Volume Control = -15.0dB
001 1101: Volume Control = -15.5dB
001 1110: Volume Control = -16.0dB
001 1111: Volume Control = -16.5dB
010 0000: Volume Control = -17.1dB
010 0001: Volume Control = -17.5dB
010 0010: Volume Control = -18.1dB
010 0011: Volume Control = -18.6dB
010 0100: Volume Control = -19.1dB
010 0101: Volume Control = -19.6dB
010 0110: Volume Control = -20.1dB
010 0111: Volume Control = -20.6dB
010 1000: Volume Control = -21.1dB
010 1001: Volume Control = -21.6dB
010 1010: Volume Control = -22.1dB
010 1011: Volume Control = -22.6dB
010 1100: Volume Control = -23.1dB
010 1101: Volume Control = -23.6dB
010 1110: Volume Control = -24.1dB
010 1111: Volume Control = -24.6dB
011 0000: Volume Control = -25.1dB
011 0001: Volume Control = -25.6dB
011 0010: Volume Control = -26.1dB
011 0011: Volume Control = -26.6dB
011 0100: Volume Control = -27.1dB
011 0101: Volume Control = -27.6dB
011 0110: Volume Control = -28.1dB
011 0111: Volume Control = -28.6dB
011 1000: Volume Control = -29.1dB
011 1001: Volume Control = -29.6dB
011 1010: Volume Control = -30.1dB
011 1011: Volume Control = -30.6dB
011 1100: Volume Control = -31.1dB
011 1100: Volume Control = -31.6dB
011 1101: Volume Control = -32.1dB
011 1110: Volume Control = -32.6dB
011 1111: Volume Control = -33.1dB
100 0000: Volume Control = -33.6dB
100 0001: Volume Control = -34.1dB
100 0010: Volume Control = -34.6dB
100 0011: Volume Control = -35.2dB
100 0100: Volume Control = -35.7dB
100 0101: Volume Control = -36.2dB
100 0110: Volume Control = -36.7dB
100 0111: Volume Control = -37.2dB
100 1000: Volume Control = -37.7dB
100 1001: Volume Control = -38.2dB
100 1010: Volume Control = -38.7dB
100 1011: Volume Control = -39.2dB
100 1100: Volume Control = -39.7dB
100 1101: Volume Control = -40.2dB
100 1110: Volume Control = -40.7dB
100 1111: Volume Control = -41.2dB
101 0000: Volume Control = -41.7dB
101 0001: Volume Control = -42.1dB
101 0010: Volume Control = -42.7dB
101 0011: Volume Control = -43.2dB
101 0100: Volume Control = -43.8dB
101 0101: Volume Control = -44.3dB
101 0110: Volume Control = -44.8dB
101 0111: Volume Control = -45.2dB
101 1000: Volume Control = -45.8dB
101 1001: Volume Control = -46.2dB
101 1010: Volume Control = -46.7dB
101 1011: Volume Control = -47.4dB
101 1100: Volume Control = -47.9dB
101 1101: Volume Control = -48.2dB
101 1110: Volume Control = -48.7dB
101 1111: Volume Control = -49.3dB
110 0000: Volume Control = -50.0dB
110 0001: Volume Control = -50.3dB
110 0010: Volume Control = -51.0dB
110 0011: Volume Control = -51.42dB
110 0100: Volume Control = -51.82dB
110 0101: Volume Control = -52.3dB
110 0110: Volume Control = -52.7dB
110 0111: Volume Control = -53.7dB
110 1000: Volume Control = -54.2dB
110 1001: Volume Control = -55.4dB
110 1010: Volume Control = -56.7dB
110 1011: Volume Control = -58.3dB
110 1100: Volume Control = -60.2dB
110 1101: Volume Control = -62.7dB
110 1110: Volume Control = -64.3dB
110 1111: Volume Control = -66.2dB
111 0000: Volume Control = -68.7dB
111 0001: Volume Control = -72.3dB
111 0010: Volume Control = MUTE
111 0011-111 1111: Reserved. Do not use
""")


print_from_description(0x01, 0x18, """
D7-D6 R 00 Reserved. Write only default values
D5-D0 R/W 00 0000 Mixer Amplifier Left Volume Control
00 0000: Volume Control = 0.0dB
00 0001: Volume Control = -0.4dB
00 0010: Volume Control = -0.9dB
00 0011: Volume Control = -1.3dB
00 0100: Volume Control = -1.8dB
00 0101: Volume Control = -2.3dB
00 0110: Volume Control = -2.9dB
00 0111: Volume Control = -3.3dB
00 1000: Volume Control = -3.9dB
00 1001: Volume Control = -4.3dB
00 1010: Volume Control = -4.8dB
00 1011: Volume Control = -5.2dB
00 1100: Volume Control = -5.8dB
00 1101: Volume Control = -6.3dB
00 1110: Volume Control = -6.6dB
00 1111: Volume Control = -7.2dB
01 0000: Volume Control = -7.8dB
01 0001: Volume Control = -8.2dB
01 0010: Volume Control = -8.5dB
01 0011: Volume Control = -9.3dB
01 0100: Volume Control = -9.7dB
01 0101: Volume Control = -10.1dB
01 0110: Volume Control = -10.6dB
01 0111: Volume Control = -11.0dB
01 1000: Volume Control = -11.5dB
01 1001: Volume Control = -12.0dB
01 1010: Volume Control = -12.6dB
01 1011: Volume Control = -13.2dB
01 1100: Volume Control = -13.8dB
01 1101: Volume Control = -14.5dB
01 1110: Volume Control = -15.3dB
01 1111: Volume Control = -16.1dB
10 0000: Volume Control = -17.0dB
10 0001: Volume Control = -18.1dB
10 0010: Volume Control = -19.2dB
10 0011: Volume Control = -20.6dB
10 0100: Volume Control = -22.1dB
10 0101: Volume Control = -24.1dB
10 0110: Volume Control = -26.6dB
10 0111: Volume Control = -30.1dB
10 1000: Volume Control = MUTE
10 1001-11 1111: Reserved. Do no use
""")

print_from_description(0x01, 0x19, """
D7-D6 R 00 Reserved. Write only default values
D5-D0 R/W 00 0000 Mixer Amplifier Right Volume Control
00 0000: Volume Control = 0.0dB
00 0001: Volume Control = -0.4dB
00 0010: Volume Control = -0.9dB
00 0011: Volume Control = -1.3dB
00 0100: Volume Control = -1.8dB
00 0101: Volume Control = -2.3dB
00 0110: Volume Control = -2.9dB
00 0111: Volume Control = -3.3dB
00 1000: Volume Control = -3.9dB
00 1001: Volume Control = -4.3dB
00 1010: Volume Control = -4.8dB
00 1011: Volume Control = -5.2dB
00 1100: Volume Control = -5.8dB
00 1101: Volume Control = -6.3dB
00 1110: Volume Control = -6.6dB
00 1111: Volume Control = -7.2dB
01 0000: Volume Control = -7.8dB
01 0001: Volume Control = -8.2dB
01 0010: Volume Control = -8.5dB
01 0011: Volume Control = -9.3dB
01 0100: Volume Control = -9.7dB
01 0101: Volume Control = -10.1dB
01 0110: Volume Control = -10.6dB
01 0111: Volume Control = -11.0dB
01 1000: Volume Control = -11.5dB
01 1001: Volume Control = -12.0dB
01 1010: Volume Control = -12.6dB
01 1011: Volume Control = -13.2dB
01 1100: Volume Control = -13.8dB
01 1101: Volume Control = -14.5dB
01 1110: Volume Control = -15.3dB
01 1111: Volume Control = -16.1dB
10 0000: Volume Control = -17.0dB
10 0001: Volume Control = -18.1dB
10 0010: Volume Control = -19.2dB
10 0011: Volume Control = -20.6dB
10 0100: Volume Control = -22.1dB
10 0101: Volume Control = -24.1dB
10 0110: Volume Control = -26.6dB
10 0111: Volume Control = -30.1dB
10 1000: Volume Control = MUTE
10 1001-11 1111: Reserved. Do no use
""")

print_from_description(0x01, 0x33, """
D7 R 0 Reserved. Write only default value.
D6 R/W 0 MICBIAS power
0: MICBIAS powered down
1: MICBIAS powered up
D5-D4 R/W 00 MICBIAS Output Voltage Configuration
00: MICBIAS = 1.04V (CM=0.75V) or MICBIAS = 1.25V(CM=0.9V)
01: MICBIAS = 1.425V(CM=0.75V) or MICBIAS = 1.7V(CM=0.9V)
10: MICBIAS = 2.075V(CM=0.75V) or MICBIAS = 2.5V(CM=0.9V)
11: MICBIAS is switch to power supply
D3 R/W 0 MICBIAS voltage source
0: MICBIAS voltage is generated from AVDD
1: MICBIAS voltage is generated from DRVdd_HP
D2-D0 R 000 Reserved. Write only default value.
""")

print_from_description(0x01, 0x34, """
D7-D6 R/W 00 IN1L to Left MICPGA positive terminal selection
00: IN1L is not routed to Left MICPGA
01: IN1L is routed to Left MICPGA with 10K resistance
10: IN1L is routed to Left MICPGA with 20K resistance
11: IN1L is routed to Left MICPGA with 40K resistance
D5-D4 R/W 00 IN2L to Left MICPGA positive terminal selection
00: IN2L is not routed to Left MICPGA
01: IN2L is routed to Left MICPGA with 10K resistance
10: IN2L is routed to Left MICPGA with 20K resistance
11: IN2L is routed to Left MICPGA with 40K resistance
D3-D2 R/W 00 IN3L to Left MICPGA positive terminal selection
00: IN3L is not routed to Left MICPGA
01: IN3L is routed to Left MICPGA with 10K resistance
10: IN3L is routed to Left MICPGA with 20K resistance
11: IN3L is routed to Left MICPGA with 40K resistance
D1-D0 R/W 00 IN1R to Left MICPGA positive terminal selection
00: IN1R is not routed to Left MICPGA
01: IN1R is routed to Left MICPGA with 10K resistance
10: IN1R is routed to Left MICPGA with 20K resistance
11: IN1R is routed to Left MICPGA with 40K resistance
""")

print_from_description(0x01, 0x36, """
D7-D6 R/W 00 CM to Left MICPGA (CM1L)
00: CM is not routed to Left MICPGA
01: CM is routed to Left MICPGA via CM1L with 10K resistance
10: CM is routed to Left MICPGA via CM1L with 20K resistance
11: CM is routed to Left MICPGA via CM1L with 40K resistance
D5-D4 R/W 00 IN2R to Left MICPGA positive terminal selection
00: IN2R is not routed to Left MICPGA
01: IN2R is routed to Left MICPGA with 10K resistance
10: IN2R is routed to Left MICPGA with 20K resistance
11: IN2R is routed to Left MICPGA with 40K resistance
D3-D2 R/W 00 IN3R to Left MICPGA positive terminal selection
00: IN3R is not routed to Left MICPGA
01: IN3R is routed to Left MICPGA with 10K resistance
10: IN3R is routed to Left MICPGA with 20K resistance
11: IN3R is routed to Left MICPGA with 40K resistance
D1-D0 R/W 00 CM to Left MICPGA (CM2L)
00: CM is not routed to Left MICPGA
01: CM is routed to Left MICPGA via CM2L with 10K resistance
10: CM is routed to Left MICPGA via CM2L with 20K resistance
11: CM is routed to Left MICPGA via CM2L with 40K resistance
""")

print_from_description(0x01, 0x37, """
D7-D6 R/W 00 IN1R to Right MICPGA positive terminal selection
00: IN1R is not routed to Right MICPGA
01: IN1R is routed to Right MICPGA with 10K resistance
10: IN1R is routed to Right MICPGA with 20K resistance
11: IN1R is routed to Right MICPGA with 40K resistance
D5-D4 R/W 00 IN2R to Right MICPGA positive terminal selection
00: IN2R is not routed to Right MICPGA
01: IN2R is routed to Right MICPGA with 10K resistance
10: IN2R is routed to Right MICPGA with 20K resistance
11: IN2R is routed to Right MICPGA with 40K resistance
D3-D2 R/W 00 IN3R to Right MICPGA positive terminal selection
00: IN3R is not routed to Right MICPGA
01: IN3R is routed to Right MICPGA with 10K resistance
10: IN3R is routed to Right MICPGA with 20K resistance
11: IN3R is routed to Right MICPGA with 40K resistance
D1-D0 R/W 00 IN2L to Right MICPGA positive terminal selection
00: IN2L is not routed to Right MICPGA
01: IN2L is routed to Right MICPGA with 10K resistance
10: IN2L is routed to Right MICPGA with 20K resistance
11: IN2L is routed to Right MICPGA with 40K resistance
""")

print_from_description(0x01, 0x39, """
D7-D6 R/W 00 CM to Right MICPGA (CM1R)
00: CM is not routed to Right MICPGA
01: CM is routed to Right MICPGA via CM1R with 10K resistance
10: CM is routed to Right MICPGA via CM1R with 20K resistance
11: CM is routed to Right MICPGA via CM1R with 40K resistance
D5-D4 R/W 00 IN1L to Right MICPGA
00: IN1L is not routed to Right MICPGA
01: IN1L is routed to Right MICPGA with 10K resistance
10: IN1L is routed to Right MICPGA with 20K resistance
11: IN1L is routed to Right MICPGA with 40K resistance
D3-D2 R/W 00 IN3L to Right MICPGA
00: IN3L is not routed to Right MICPGA
01: IN3L is routed to Right MICPGA with 10K resistance
10: IN3L is routed to Right MICPGA with 20K resistance
11: IN3L is routed to Right MICPGA with 40K resistance
D1-D0 R/W 00 CM to Right MICPGA (CM2R)
00: CM is not routed to Right MICPGA
01: CM is routed to Right MICPGA via CM2R with 10K resistance
10: CM is routed to Right MICPGA via CM2R with 20K resistance
11: CM is routed to Right MICPGA via CM2R with 40K resistance
""")

print_from_description(0x01, 0x3A, """
D7 R/W 0 -
0: IN1L input is not weakly connected to common mode
1: IN1L input is weakly driven to common mode. Use when not routing IN1L to Left and Right MICPGA and HPL
D6 R/W 0 -
0: IN1R input is not weakly connected to common mode
1: IN1R input is weakly driven to common mode. Use when not routing IN1L to Left and Right MICPGA and HPR
D5 R/W 0 -
0: IN2L input is not weakly connected to common mode
1: IN2L input is weakly driven to common mode. Use when not routing IN2L to Left and Right MICPGA
D4 R/W 0 -
0: IN2R input is not weakly connected to common mode
1: IN2R input is weakly driven to common mode. Use when not routing IN2R to Left and Right MICPGA
D3 R/W 0 -
0: IN3L input is not weakly connected to common mode
1: IN3L input is weakly driven to common mode. Use when not routing IN3L to Left and Right MICPGA
D2 R/W 0 -
0: IN3R input is not weakly connected to common mode
1: IN3R input is weakly driven to common mode. Use when not routing IN3R to Left and Right MICPGA
D1-D0 R 00 Reserved. Write only default values
""")

print_from_description(0x01, 0x3B, """
D7 R/W 1 Left MICPGA Gain
0: Left MICPGA Gain is enabled
1: Left MICPGA Gain is set to 0dB
D6-D0 R/W 000 0000 Left MICPGA Volume Control
000 0000: Volume Control = 0.0dB
000 0001: Volume Control = 0.5dB
000 0010: Volume Control = 1.0dB
…
101 1101: Volume Control = 46.5dB
101 1110: Volume Control = 47.0dB
101 1111: Volume Control = 47.5dB
110 0000-111 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x3C, """
D7 R/W 1 Right MICPGA Gain
0: Right MICPGA Gain is enabled
1: Right MICPGA Gain is set to 0dB
D6-D0 R/W 000 0000 Right MICPGA Volume Control
000 0000: Volume Control = 0.0dB
000 0001: Volume Control = 0.5dB
000 0010: Volume Control = 1.0dB
…
101 1101: Volume Control = 46.5dB
101 1110: Volume Control = 47.0dB
101 1111: Volume Control = 47.5dB
110 0000-111 1111: Reserved. Do not use
""")
print_from_description(0x01, 0x3D, """
D7-D0 R/W 0000 0000 ADC Power Tune Configuration
0000 0000: PTM_R4 (Default)
0110 0100: PTM_R3
1011 0110: PTM_R2
1111 1111: PTM_R1
Others: UNDEFINED IN DATASHEET
""")


print_from_description(0x01, 0x3E, """
D7-D2 R 00 0000 Reserved. Write only default values
D1 R 0 Left Channel Analog Volume Control Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
D0 R 0 Right Channel Analog Volume Control Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
""")
print_from_description(0x01, 0x3F, """
D7 R 0 HPL Gain Flag
0: Applied Gain is not equal to Programmed Gain
1: Applied Gain is equal to Programmed Gain
D6 R 0 HPR Gain Flag
0: Applied Gain is not equal to Programmed Gain
1: Applied Gain is equal to Programmed Gain
D5 R 0 LOL Gain Flag
0: Applied Gain is not equal to Programmed Gain
1: Applied Gain is equal to Programmed Gain
D4 R 0 LOR Gain Flag
0: Applied Gain is not equal to Programmed Gain
1: Applied Gain is equal to Programmed Gain
D3 R 0 IN1L to HPL Bypass Volume Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
D2 R 0 IN1R to HPR Bypass Volume Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
D1 R 0 MAL Volume Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
D0 R 0 MAR Volume Flag
0: Applied Volume is not equal to Programmed Volume
1: Applied Volume is equal to Programmed Volume
""")
print_from_description(0x01, 0x40-0x46, """
D7-D0 R 0000 0000 Reserved. Write only default values
""")
print_from_description(0x01, 0x47, """
D7-D6 R 00 Reserved. Write only default values
D5-D0 R/W 00 0000 Analog inputs power up time
00 0000: Default. Use one of the values give below
11 0001: Analog inputs power up time is 3.1 ms
11 0010: Analog inputs power up time is 6.4 ms
11 0011: Analog inputs power up time is 1.6 ms
Others: Do not use
""")

print_from_description(0x01, 0x7B, """
READ/ RESET BIT DESCRIPTION WRITE VALUE
D7-D3 R 0 0000 Reserved. Write only default values
D2-D0 R/W 000 Reference Power Up configuration
000: Reference will power up slowly when analog blocks are powered up
001: Reference will power up in 40ms when analog blocks are powered up
010: Reference will power up in 80ms when analog blocks are powered up
011: Reference will power up in 120ms when analog blocks are powered up
100: Force power up of reference. Power up will be slow
101: Force power up of reference. Power up time will be 40ms
110: Force power up of reference. Power up time will be 80ms
111: Force power up of reference. Power up time will be 120ms
""")
print_from_description(0x01, 0x7C, """
READ/ RESET BIT DESCRIPTION WRITE VALUE
D7 R/W 0 Reserved
D6-D4 R/W 000 Charge Pump Power Configuration
000: Charge Pump Configuration is for Peak Load Current
001: Charge Pump Configuration is for 1/8 x Peak Load Current
...
111: Charge Pump Configuration is for 7/8 x Peak Load Current
D3-D0 R/W 0000 Charge Pump Clock Divide Control
0000: Clock Divide = 64
0001: Clock Divide = 4
0010: Clock Divide = 8
...
1111: Clock Divide = 60
Note: To power up charge pump, please program Page 1 / Register 1
""")
print_from_description(0x01, 0x7D, """
READ/ RESET BIT DESCRIPTION WRITE VALUE
D7 R/W 0 Headphone amplifier compensation adjustment
Note: For use with low capacitive loading at the headpone output (<100pF//10k)
D6-D5 R/W 00 Master Gain Control in Ground Centered Mode
0: HPL and HPR have independent Gain Control in Ground Centered Mode
1: HPR Gain acts as Master Gain in Ground Centered Mode
2: HPL Gain acts as Master Gain in Ground Centered Mode
3: Reserved. Do not use
Note: The use of D6:5=1 or 2 will lead to lower power consumption. For these power saving modes to operate correctly the gains of HPL and HPR need to be programmed to the same values in Page 1 / Register 16 and Page 1 / Register 17
D4 R/W 0 Ground Centered Mode
0: Disable Ground Centered Mode for Headphone Drivers
1: Enable Ground Centered Mode for Headphone Drivers
Note: The internal charge pump needs to be enabled if ground centered mode is enabled. Page 1 / Register 1 D1:0
D3-D2 R/W 00 Headphone Driver Power Configuration
0: Output Power Rating is 100%.
1: Output Power Rating is 75%
2: Output Power Rating is 50%
3: Output Power Ratign is 25%
D1-D0 R/W 00 Ground Centered Mode DC Correction
0: DC Offset Correction is disabled
1: Reserved.
2: DC Offset Correction is enabled for all signal routings which are enabled for HPL and HPR
3: DC Offset Correction for all possible signal routings for HPL and HPR
Note: Read status for HP amplifier from Page 1 / Register 2
""")


print_from_description(0x08, 0x01, """
READ/ RESET BIT DESCRIPTION WRITE VALUE
D7-D3 R 0000 0 Reserved. Write only default values
D2 R/W 0 ADC Adaptive Filtering Control
0: Adaptive Filtering disabled for ADC
1: Adaptive Filtering enabled for ADC
D1 R 0 ADC Adaptive Filter Buffer Control Flag
0: In adaptive filter mode, ADC accesses ADC Coefficient Buffer-A and control interface accesses ADC Coefficient Buffer-B
1: In adaptive filter mode, ADC accesses ADC Coefficient Buffer-B and control interface accesses ADC Coefficient Buffer-A
D0 R/W 0 ADC Adaptive Filter Buffer Switch control
0: ADC Coefficient Buffers will not be switched at next frame boundary
1: ADC Coefficient Buffers will be switched at next frame boundary, if in adaptive filtering mode. This will self clear on switching.
""")

print_from_description(0x2C, 0x01, """
READ/ RESET BIT DESCRIPTION WRITE VALUE
D7-D3 R 0000 0 Reserved. Write only default values
D2 R/W 0 DAC Adaptive Filtering Control
0: Adaptive Filtering disabled for DAC
1: Adaptive Filtering enabled for DAC
D1 R 0 DAC Adaptive Filter Buffer Control Flag
0: In adaptive filter mode, DAC accesses DAC Coefficient Buffer-A and control interface accesses DAC Coefficient Buffer-B
1: In adaptive filter mode, DAC accesses DAC Coefficient Buffer-B and control interface accesses DAC Coefficient Buffer-A
D0 R/W 0 DAC Adaptive Filter Buffer Switch control
0: DAC Coefficient Buffers will not be switched at next frame boundary
1: DAC Coefficient Buffers will be switched at next frame boundary, if in adaptive filtering mode. This will self clear on switching.
""")

from typing import List
import re

with open('gt9110_config.txt') as f:
    lines = list(f)

output = []

last_addr = 0x8046

for line in lines:
    line = re.sub("#.*$", '', line).rstrip()
    if line:
        addr, content = line.split(' ')
        addr = int(addr, 16)
        content = int(content, 16)

        assert addr == last_addr + 1
        output.append(content.to_bytes(1, byteorder='big'))
        last_addr = addr


def calculate_checksum(cfg: bytes):
    raw_cfg_len = len(cfg) - 2
    check_sum = 0

    # for (i = 0; i < raw_cfg_len; i++)
    for value in cfg[:-2]:
        check_sum += value
        check_sum %= 256
    check_sum = ((~check_sum) + 1) % 256;
    print(f"fixing checksum to 0x{check_sum:02x} (was 0x{cfg[-2]:02x})")
    return cfg[:-2] + check_sum.to_bytes(1, byteorder='big') + cfg[-1:]


fixed_checksum = calculate_checksum(b''.join(output))

with open('goodix_9110_cfg.bin', 'wb') as out_f:
    out_f.write(fixed_checksum)

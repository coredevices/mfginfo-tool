# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CRC_POLY = 0x04C11DB7

def precompute_table(bits):
    lookup_table = []
    for i in range(2**bits):
        rr = i << (32 - bits)
        for x in range(bits):
            if rr & 0x80000000:
                rr = (rr << 1) ^ CRC_POLY
            else:
                rr <<= 1
        lookup_table.append(rr & 0xffffffff)
    return lookup_table

lookup_table = precompute_table(8)

def process_word(data, crc=0xffffffff):
    if (len(data) < 4):
        # The CRC data is "padded" in a very unique and confusing fashion.
        data = data[::-1] + b'\0' * (4 - len(data))

    for char in reversed(data):
        b = char
        crc = ((crc << 8) ^ lookup_table[(crc >> 24) ^ b]) & 0xffffffff
    return crc

def process_buffer(buf, c=0xffffffff):
    word_count = (len(buf) + 3) // 4

    crc = c
    for i in range(word_count):
        crc = process_word(buf[i * 4 : (i + 1) * 4], crc)
    return crc

def crc32(data):
    return process_buffer(data)

if __name__ == '__main__':
    import sys

    assert(0x89f3bab2 == process_buffer("123 567 901 34"))
    assert(0xaff19057 == process_buffer("123456789"))
    assert(0x519b130 == process_buffer("\xfe\xff\xfe\xff"))
    assert(0x495e02ca == process_buffer("\xfe\xff\xfe\xff\x88"))

    print("All tests passed!")

    if len(sys.argv) >= 2:
        b = open(sys.argv[1]).read()
        crc = crc32(b)
        print("%u or 0x%x" % (crc, crc))

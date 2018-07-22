import fix_path
from dynamixel import protocol2
from unittest import mock

def test_crc():
    assert protocol2.crc16([0]) == 0
    assert protocol2.crc16([1, 2, 3, 4]) == 40499
    assert protocol2.crc16([230, 15, 67]) == 11890


def test_pack_packet():
    build = protocol2.Protocol2Bus._build_packet
    # These were done on a version that worked, but weren't calculated by
    # hand. Hopefully they'll function as a regression test.
    assert build(0x01, 0x03, [0x01, 0x00]) == b'\xff\xff\xfd\x00\x01\x05\x00\x03\x01\x00h\xa3'
    assert build(0x04, 0x01, []) == b'\xff\xff\xfd\x00\x04\x03\x00\x01\x19\n'


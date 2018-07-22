import fix_path
from dynamixel import servo

def test_hex():
    assert servo.format_data([5], {'type':'hex'}) == '5'
    assert servo.format_data([15], {'type':'hex'}) == 'f'
    assert servo.format_data([254], {'type':'hex'}) == 'fe'
    assert servo.format_data([2, 1], {'type':'hex'}) == '102'

    assert servo.format_data_inverse('5', {'type':'hex'}) == [5]
    assert servo.format_data_inverse('f', {'type':'hex'}) == [15]
    assert servo.format_data_inverse('fe', {'type':'hex'}) == [254]
    assert servo.format_data_inverse('102', {'type':'hex'}) == [2, 1]

def test_int():
    assert servo.format_data([5], {'type':'int'}) == 5
    assert servo.format_data([15], {'type':'int'}) == 15
    assert servo.format_data([254], {'type':'int'}) == 254
    assert servo.format_data([2, 1], {'type':'int'}) == 258

    assert servo.format_data_inverse(5, {'type':'int'}) == [5]
    assert servo.format_data_inverse(15, {'type':'int'}) == [15]
    assert servo.format_data_inverse(254, {'type':'int'}) == [254]
    assert servo.format_data_inverse(258, {'type':'int'}) == [2, 1]

def test_float():
    assert servo.format_data([5], {'type':'float'}) == 5.0
    assert servo.format_data_inverse(5.1, {'type':'float'}) == [5]

def test_bool():
    assert servo.format_data([0], {'type':'bool'}) == False
    assert servo.format_data([1], {'type':'bool'}) == True
    assert servo.format_data_inverse(False, {'type':'float'}) == []
    assert servo.format_data_inverse(True, {'type':'float'}) == [1]

def test_offset():
    assert servo.format_data([10], {'type':'int', 'offset':5}) == 5
    assert servo.format_data_inverse(5, {'type':'int', 'offset':5}) == [10]

def test_scale():
    assert servo.format_data([5], {'type':'int', 'scale':2}) == 10
    assert servo.format_data_inverse(10, {'type':'int', 'scale':2}) == [5]

def test_limits():
    assert servo.format_data_inverse(5, {'type':'int', 'min':10}) == [10]
    assert servo.format_data_inverse(15, {'type':'int', 'min':10}) == [15]
    assert servo.format_data_inverse(5, {'type':'int', 'max':10}) == [5]
    assert servo.format_data_inverse(15, {'type':'int', 'max':10}) == [10]

def test_limits_and_offset():
    assert servo.format_data_inverse(5, {'type':'int', 'offset':5, 'max':8}) == [8]
    assert servo.format_data_inverse(5, {'type':'int', 'offset':-5, 'min':2}) == [2]

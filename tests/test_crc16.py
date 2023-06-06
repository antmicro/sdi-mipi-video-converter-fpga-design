# Copyright 2023 Antmicro <www.antmicro.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from common import bbb_line, bbb_line_crc
from cocotb.triggers import Timer
from cocotb.regression import TestFactory

# Beginning of the first line of the Big Buck Bunny frame
CRC1_DATA = [0X5380, 0x5376, 0x5380, 0x5376, 0X5380, 0x5376, 0x5380, 0x5376, 0X5580, 0x5576, 0x5580, 0x5576]
CRC1_RESULT = 0x730b


async def test_crc16(dut, crc_test_case):
    test_case = crc_test_case
    if crc_test_case == "bbb_1":
        test_case = (bbb_line, bbb_line_crc)
    crc_data = test_case[0]
    crc_result = test_case[1]

    for i in range(len(crc_data)):
        if i == 0:
            # Set initial CRC to all 1s
            dut.crc_i.value = 0xffff
        else:
            # Calculated CRC becomes new CRC input
            dut.crc_i.value = dut.crc_o.value

        dut.data_i.value = crc_data[i]
        await Timer(10)

    # Add delay to separate tests on waveform
    await Timer(100)
    assert dut.crc_o.value == crc_result, "Incorrect CRC: {crc_o}, should be: {golden}".format(
            crc_o=dut.crc_i.value, golden=crc_result)

tf = TestFactory(test_function=test_crc16)
tf.add_option(name="crc_test_case", optionlist=[
    (CRC1_DATA, CRC1_RESULT),
    "bbb_1"
])
tf.generate_tests()

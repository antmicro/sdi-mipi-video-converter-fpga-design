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


dphy_timings = {
    "1080p30": {
        "CN": "0b10000",# 3
        "CM": "0b10100000", # 96
        "CO": "0b010", # 4
        "TINIT_VALUE": 15000,
        "T_LPX": 4,
        "T_DATPREP": 4,
        "T_DAT_HSZERO": 10,
        "T_DATTRAIL": 13,
        "T_DATEXIT": 9,
        "T_CLKPREP": 3,
        "T_CLK_HSZERO": 20,
        "T_CLKPRE": 1,
        "T_CLKPOST": 10,
        "T_CLKTRAIL": 6,
    }
}


class UnsupportedVideoFormatException(Exception):
    def __init__(self, supported_video_formats):
        msg = "Unsupported video format. Available options are: {"
        msg += ", ".join(supported_video_formats)
        msg += "}"
        super().__init__(msg)

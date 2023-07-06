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

supported_formats_hd = ["720p_hd", "720p50", "720p60", "1080p_hd", "1080p25", "1080p30"]
supported_formats_3g = ["1080p_3g", "1080p50", "1080p60"]
supported_formats = supported_formats_hd + supported_formats_3g

clock_timings_2lanes = {
    "74_25MHz": {
        "CN": "0b10000",# 3
        "CM": "0b10100000", # 96
        "CO": "0b010", # 4
        "TINIT_VALUE": 5000,
        "T_LPX": 4,
        "T_DATPREP": 4,
        "T_DAT_HSZERO": 10,
        "T_DATTRAIL": 13,
        "T_CLKPREP": 3,
        "T_CLK_HSZERO": 20,
        "T_CLKPOST": 10,
        "T_CLKTRAIL": 6,
    },
    "148_5MHz": {
        "CN": "0b11100",# 5
        "CM": "0b10010000", # 80
        "CO": "0b001", # 2
        "TINIT_VALUE": 10000,
        "T_LPX": 8,
        "T_DATPREP": 7,
        "T_DAT_HSZERO": 18,
        "T_DATTRAIL": 19,
        "T_CLKPREP": 6,
        "T_CLK_HSZERO": 39,
        "T_CLKPOST": 15,
        "T_CLKTRAIL": 10,
    }
}

clock_timings_4lanes = {
    "74_25MHz": {
        "CN": "0b10000",# 3
        "CM": "0b10100000", # 96
        "CO": "0b011", # 8
        "TINIT_VALUE": 5000,
        "T_LPX": 2,
        "T_DATPREP": 2,
        "T_DAT_HSZERO": 6,
        "T_DATTRAIL": 10,
        "T_CLKPREP": 2,
        "T_CLK_HSZERO": 10,
        "T_CLKPOST": 8,
        "T_CLKTRAIL": 4,
    },
    "148_5MHz": {
        "CN": "0b11100",# 5
        "CM": "0b10010000", # 80
        "CO": "0b010", # 4
        "TINIT_VALUE": 10000,
        "T_LPX": 4,
        "T_DATPREP": 4,
        "T_DAT_HSZERO": 9,
        "T_DATTRAIL": 10,
        "T_CLKPREP": 3,
        "T_CLK_HSZERO": 20,
        "T_CLKPOST": 8,
        "T_CLKTRAIL": 5,
    }
}

dphy_timings = {
    "sdi_hd-2lanes" : clock_timings_2lanes["74_25MHz"],
    "sdi_3g-2lanes" : clock_timings_2lanes["148_5MHz"],
    "sdi_hd-4lanes" : clock_timings_4lanes["74_25MHz"],
    "sdi_3g-4lanes" : clock_timings_4lanes["148_5MHz"],
}

def get_timings(video_format, four_lanes):
    LANES = 4 if four_lanes else 2
    lanes = str(LANES) + "lanes"

    if video_format in supported_formats_hd:
        timings_str = "sdi_hd-" + lanes
    elif video_format in supported_formats_3g:
        timings_str = "sdi_3g-" + lanes

    return dphy_timings[timings_str]

#!/usr/bin/env python3
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


import os
import sys

sys.path.append("src")

import argparse

from top import Top
from migen.fhdl.verilog import convert

supported_formats = ["720p50", "720p60", "1080p25", "1080p30", "1080p50", "1080p60"]
supported_data_rates = ["720p_hd", "1080p_hd", "1080p_3g"]

def prepare_top_sources(output_dir, video_format, four_lanes, sim, pattern_gen):
    top = Top(video_format, four_lanes, sim, pattern_gen)
    top_path = os.path.join(output_dir, "top.v")

    with open(top_path, "w") as fd:
        fd.write(str(convert(top, top.ios, name="top")))


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description="Generate FPGA Design for SDI MIPI Video Converter"
    )
    parser.add_argument(
        "--video-format",
        default="1080p30",
        help='Video format (%s)' % str(supported_formats),
    )
    parser.add_argument(
        "--lanes", type=int, default=2, help='Number of lanes ("2", or "4")'
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="Generate sources compatible with Icarus simulator",
    )
    parser.add_argument(
        "--pattern-gen",
        action="store_true",
        help="Generate fixed pattern based on artificially generated frame timings",
    )
    args = parser.parse_args()

    if args.video_format in supported_data_rates:
        video_format = args.video_format
        if args.pattern_gen:
            sys.exit("Video format must be precise ()" % str(supported_formats))
    elif args.pattern_gen:
        video_format = "pattern_gen-" + args.video_format
    elif args.video_format in ("720p50", "720p60", "1080p25", "1080p30"):
        video_format = args.video_format[:-2] + "_hd"
    elif args.video_format in ("1080p50", "1080p60"):
        video_format = args.video_format[:-2] + "_3g"
    else:
        sys.exit("Unsupported video format")

    if args.lanes not in (2, 4):
        sys.exit("Unsupported number of lanes")

    # create names
    four_lanes = True if args.lanes == 4 else False
    lanes_name_part = "4lanes" if four_lanes else "2lanes"
    output_dir_rel = os.path.join("build", f"{video_format}-{lanes_name_part}")
    output_dir = os.path.abspath(output_dir_rel)

    # generate sources
    four_lanes = True if args.lanes == 4 else False
    os.makedirs(output_dir, exist_ok=True)
    prepare_top_sources(output_dir, args.video_format, four_lanes, args.sim, args.pattern_gen)

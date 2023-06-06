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
from cocotb.triggers import RisingEdge, ClockCycles

tests_dir = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.realpath(os.path.join(tests_dir, "..", "src"))
sys.path.append(src_path)

# 74.25 MHz
PIX_CLK_74_25MHZ = 13468
BYTE_CLK_74_25MHZ = 13466

# 148.5 MHz
PIX_CLK_148_5MHZ = 6734
BYTE_CLK_148_5MHZ = 6732

bbb_line_crc = 0x465e
bbb_line = [
    0x5380, 0x5376, 0x5380, 0x5376, 0x5380, 0x5376, 0x5380, 0x5376, 0x5580, 0x5576, 0x5580, 0x5576,
    0x5580, 0x5576, 0x5581, 0x5576, 0x5582, 0x5476, 0x5482, 0x5476, 0x5482, 0x5476, 0x5482, 0x5376,
    0x5382, 0x5176, 0x5182, 0x5176, 0x5382, 0x5376, 0x5482, 0x5477, 0x5481, 0x5579, 0x5580, 0x557a,
    0x5680, 0x577a, 0x5780, 0x577a, 0x5980, 0x597a, 0x5980, 0x597a, 0x5980, 0x597a, 0x5980, 0x5a7a,
    0x5c80, 0x5d79, 0x5e7f, 0x5e78, 0x5e7f, 0x5e78, 0x5d81, 0x5d78, 0x5f7f, 0x5f78, 0x6080, 0x6277,
    0x647f, 0x6678, 0x697d, 0x6b78, 0x7873, 0x7877, 0x7873, 0x7878, 0x7873, 0x7878, 0x7873, 0x7877,
    0x7873, 0x7877, 0x7873, 0x7877, 0x7873, 0x7877, 0x7674, 0x7679, 0x7975, 0x777a, 0x7775, 0x767a,
    0x7475, 0x747a, 0x7375, 0x717a, 0x6f75, 0x6e7a, 0x6975, 0x677a, 0x6175, 0x607a, 0x5b75, 0x5779,
    0x5880, 0x5778, 0x5680, 0x5477, 0x5080, 0x5077, 0x4e80, 0x4f77, 0x4f81, 0x5077, 0x5280, 0x5276,
    0x5280, 0x5276, 0x527f, 0x5278, 0x5180, 0x537b, 0x5380, 0x517c, 0x5980, 0x5d7c, 0x667f, 0x6c7c,
    0x6c7d, 0x6b7b, 0x687d, 0x687c, 0x597d, 0x577c, 0x547d, 0x547b, 0x557f, 0x547b, 0x547f, 0x547a,
    0x537f, 0x527a, 0x517f, 0x517a, 0x4e7f, 0x4e7a, 0x4d7f, 0x4d7a, 0x4c7f, 0x4b7a, 0x4b7f, 0x4b7a,
    0x4981, 0x497a, 0x4881, 0x477a, 0x4881, 0x4a7a, 0x4d80, 0x4f7a, 0x4e7f, 0x4e7a, 0x4f7e, 0x4f7a,
    0x4f7e, 0x4f7a, 0x4f7d, 0x4e7b, 0x507d, 0x4f7c, 0x4f7d, 0x4f7c, 0x4f7d, 0x4f7c, 0x4e7d, 0x4e7b,
    0x4b7d, 0x4a79, 0x497d, 0x4978, 0x497d, 0x4978, 0x497d, 0x4978, 0x4a7b, 0x4877, 0x467b, 0x4576,
    0x457b, 0x4776, 0x4b7b, 0x4d76, 0x507b, 0x5176, 0x537b, 0x5676, 0x577b, 0x5776, 0x577b, 0x5776,
    0x5679, 0x5875, 0x5679, 0x5574, 0x5179, 0x5c74, 0x6b79, 0x7574, 0x8079, 0x7b74, 0x7179, 0x6c74,
    0x6379, 0x5e74, 0x5779, 0x5b74, 0x5279, 0x5073, 0x5079, 0x5072, 0x5179, 0x5472, 0x5279, 0x5072,
    0x5679, 0x6072, 0x5c79, 0x4c72, 0x5079, 0x6272, 0x6f78, 0x6d73, 0x7275, 0x6c74, 0x6074, 0x5975,
    0x6174, 0x6975, 0x7272, 0x7b75, 0x7f71, 0x8075, 0x836f, 0x8375, 0x846f, 0x8475, 0x846e, 0x8476,
    0x846d, 0x8477, 0x836c, 0x8478, 0x846c, 0x8378, 0x836e, 0x8278, 0x8070, 0x8078, 0x8072, 0x7f78,
    0x7772, 0x6e78, 0x5f74, 0x5877, 0x4877, 0x4b75, 0x4e79, 0x5274, 0x5679, 0x5874, 0x5c79, 0x5c74,
    0x5979, 0x5974, 0x5879, 0x5774, 0x5779, 0x5774, 0x577a, 0x5774, 0x567b, 0x5673, 0x577c, 0x5773,
    0x577c, 0x5773, 0x577c, 0x5773, 0x617c, 0x6173, 0x5d7c, 0x5973, 0x537c, 0x5173, 0x4c7c, 0x4a73,
    0x4a7b, 0x4a73, 0x497b, 0x4873, 0x4a7b, 0x4b73, 0x4e7b, 0x5073, 0x527b, 0x5473, 0x567b, 0x5873,
    0x5c7b, 0x5f73, 0x6179, 0x6173, 0x6079, 0x6073, 0x6078, 0x5d73, 0x5c78, 0x5c73, 0x5d78, 0x5e73,
    0x6078, 0x6173, 0x6178, 0x6173, 0x6078, 0x5e73, 0x5d78, 0x5c73, 0x5a77, 0x5a73, 0x5b77, 0x5c73,
    0x6173, 0x6673, 0x6e70, 0x7373, 0x7871, 0x7271, 0x6372, 0x5872, 0x4b77, 0x4872, 0x4b79, 0x4d72,
    0x3c75, 0x3f6b, 0x4074, 0x4b68, 0x586e, 0x6162, 0x6a6b, 0x6c5e, 0x6e70, 0x6d60, 0x6772, 0x6263,
    0x5b74, 0x5a6c, 0x5c76, 0x5e6f, 0x7977, 0x726e, 0x6378, 0x5b6f, 0x5377, 0x536f, 0x5579, 0x5671,
    0x4f79, 0x4971, 0x3b7b, 0x3674, 0x3c7b, 0x4874, 0x5d7b, 0x6875, 0x4e7d, 0x4e76, 0x4e7d, 0x4e76,
    0x4e81, 0x4e76, 0x4e85, 0x4c76, 0x4686, 0x416e, 0x5388, 0x6867, 0x808c, 0x825a, 0x6a8d, 0x5457,
    0xa08d, 0xab50, 0xbb8f, 0xc650, 0xa38f, 0xab50, 0xb98d, 0xc052, 0xaf88, 0xac55, 0xa786, 0xa35b,
    0x5186, 0x5063, 0x5187, 0x5167, 0x5086, 0x5068, 0x5087, 0x5068, 0x5087, 0x5069, 0x5087, 0x5068,
    0x5184, 0x5267, 0x5184, 0x5166, 0x5180, 0x5167, 0x5280, 0x5066, 0x4f82, 0x4a63, 0x4f82, 0x615f,
    0x8182, 0x9856, 0xa283, 0xa654, 0xae82, 0xa056, 0x8284, 0x705b, 0x5a83, 0x5768, 0x5582, 0x556e,
    0x5480, 0x556c, 0x547f, 0x516c, 0x517b, 0x526c, 0x507a, 0x4b6b, 0x4779, 0x476b, 0x4677, 0x446a,
    0x4478, 0x446a, 0x4478, 0x436c, 0x4079, 0x426f, 0x4579, 0x4b70, 0x5579, 0x5a70, 0x5b79, 0x5870,
    0x4279, 0x4070, 0x4079, 0x4370, 0x4979, 0x4c70, 0x4e79, 0x4e6f, 0x4e7b, 0x4b6b, 0x4b7b, 0x496b,
    0x4b7c, 0x4f6a, 0x557c, 0x5968, 0x627c, 0x6366, 0x667c, 0x6863, 0x697c, 0x6864, 0x667b, 0x6664,
    0x4777, 0x4662, 0x4776, 0x4762, 0x4876, 0x4c62, 0x5376, 0x5564, 0x5576, 0x5469, 0x5376, 0x536c,
    0x5376, 0x5370, 0x5176, 0x5271, 0x5177, 0x5172, 0x4e77, 0x4d71, 0x4977, 0x4671, 0x4378, 0x4173,
    0x3d79, 0x3974, 0x3a7a, 0x4076, 0x4079, 0x3e76, 0x3f79, 0x4376, 0x407b, 0x4076, 0x407b, 0x4076,
    0x407b, 0x3f76, 0x407b, 0x3f75, 0x3e7c, 0x3f74, 0x407b, 0x4071, 0x407b, 0x4071, 0x3f7b, 0x3f70,
    0x4179, 0x4f6c, 0x6979, 0x796b, 0x8179, 0x7b6c, 0x6d79, 0x656b, 0x6679, 0x636a, 0x5b79, 0x5669,
    0x4c79, 0x4969, 0x4678, 0x4369, 0x4477, 0x3b68, 0x2a74, 0x2673, 0x3e6e, 0x5d68, 0x916b, 0xab6a,
    0xb470, 0xa66a, 0x9071, 0x7e6c, 0x6e70, 0x646c, 0x6270, 0x5b6b, 0x5372, 0x526a, 0x5170, 0x5169,
    0x5172, 0x5068, 0x5073, 0x5069, 0x4e73, 0x4d6a, 0x4c72, 0x4b6a, 0x4a72, 0x4c6a, 0x4e73, 0x5069,
    0x5075, 0x5166, 0x5176, 0x5166, 0x5276, 0x5269, 0x5276, 0x536c, 0x5476, 0x546d, 0x5376, 0x536f,
    0x5377, 0x536f, 0x5279, 0x5471, 0x507b, 0x5176, 0x507b, 0x4f77, 0x4f7d, 0x5178, 0x537c, 0x5679,
    0x5874, 0x5c7b, 0x5e74, 0x6179, 0x6174, 0x6075, 0x5f74, 0x5e72, 0x5b74, 0x5a6e, 0x5b75, 0x5b6d,
    0x5b75, 0x5b6c, 0x5b75, 0x5b6c, 0x5a75, 0x5a6d, 0x5675, 0x556d, 0x4375, 0x496c, 0x5575, 0x5b6c,
    0x5e76, 0x5e75, 0x5d76, 0x5d76, 0x5c76, 0x5977, 0x5876, 0x5579, 0x5176, 0x527a, 0x5276, 0x527b,
    0x5276, 0x527b, 0x5276, 0x527b, 0x5475, 0x5575, 0x5574, 0x5675, 0x5774, 0x5674, 0x5374, 0x5271,
    0x5174, 0x4f71, 0x4c74, 0x4a70, 0x4a74, 0x4c70, 0x4e75, 0x4f70, 0x5076, 0x516f, 0x5277, 0x526e,
    0x5277, 0x546e, 0x5577, 0x556e, 0x5f76, 0x6b6d, 0x7871, 0x7d68, 0x8067, 0x7f5e, 0x7f62, 0x8359,
    0x9059, 0x8c56, 0x8059, 0x7a56, 0x785a, 0x7a56, 0x8459, 0x8856, 0x7b5a, 0x7e56, 0x8b5a, 0x9656,
    0x975a, 0x8e56, 0x855b, 0x8158, 0x7d5f, 0x7c58, 0x7b5f, 0x7c58, 0x7c5f, 0x7c58, 0x7c5f, 0x7d57,
    0x7d62, 0x995e, 0x9067, 0x6563, 0x4770, 0x556c, 0x5f75, 0x5672, 0x5079, 0x5072, 0x4f79, 0x4c72,
    0x4879, 0x4473, 0x4277, 0x4074, 0x4376, 0x4674, 0x5473, 0x6675, 0x7974, 0x7c75, 0x6875, 0x5a77,
    0x5777, 0x577b, 0x5779, 0x577b, 0x5779, 0x577c, 0x5579, 0x567a, 0x5579, 0x5577, 0x5579, 0x5676,
    0x567a, 0x5773, 0x587b, 0x5873, 0x567e, 0x5773, 0x567f, 0x5373, 0x507f, 0x4e73, 0x4d7f, 0x4b73,
    0x547f, 0x5473, 0x557f, 0x5573, 0x557f, 0x5573, 0x557f, 0x5673, 0x557e, 0x5473, 0x547e, 0x5273,
    0x4f7e, 0x4d73, 0x4c7e, 0x4a73, 0x477e, 0x4673, 0x467e, 0x4673, 0x467e, 0x4674, 0x467d, 0x4675,
    0x4f79, 0x4a77, 0x3e78, 0x3879, 0x3477, 0x3777, 0x3c76, 0x3f7a, 0x5574, 0x695d, 0x8572, 0x985d,
    0xa072, 0x995e, 0x8a72, 0x805d, 0x5c72, 0x5c6b, 0x5c72, 0x5b69, 0x6372, 0x6b62, 0x7974, 0x8161,
    0x5975, 0x5161, 0x3f77, 0x3669, 0x3d77, 0x3e68, 0x4378, 0x476a, 0x4c7a, 0x4f75, 0x527b, 0x5772,
    0x577b, 0x5c6c, 0x5e7b, 0x606a, 0x5b7b, 0x556a, 0x477b, 0x406e, 0x4b7b, 0x4c76, 0x4c7b, 0x4c7b,
    0x4c7d, 0x4c7e, 0x4c7d, 0x4c7e, 0x4b7d, 0x4b7f, 0x4a7d, 0x4a7f, 0x4b7b, 0x497d, 0x497c, 0x4879,
    0x487c, 0x4874, 0x487d, 0x4770, 0x4777, 0x476e, 0x4777, 0x486e, 0x4977, 0x496e, 0x4a75, 0x4b6e,
    0x4c74, 0x4d6d, 0x4e72, 0x4e6d, 0x5072, 0x526d, 0x5174, 0x516f, 0x5275, 0x5072, 0x5075, 0x4f73,
    0x4f75, 0x5073, 0x5275, 0x5373, 0x5375, 0x5473, 0x5575, 0x5673, 0x5675, 0x5573, 0x5575, 0x5474,
    0x5174, 0x5977, 0x6a73, 0x7278, 0x7173, 0x6877, 0x5675, 0x4e76, 0x4d76, 0x4e75, 0x4f78, 0x4f73,
    0x4f78, 0x4f73, 0x4f78, 0x4f73, 0x4978, 0x4475, 0x3f78, 0x457a, 0x5477, 0x5a82, 0x5877, 0x5286,
    0x4d79, 0x4d74, 0x4e77, 0x4e74, 0x4e77, 0x4e75, 0x4d7b, 0x4d74, 0x4e7d, 0x4e73, 0x4f7e, 0x4e73,
    0x4d7e, 0x4e73, 0x4e7c, 0x5075, 0x4d79, 0x4f76, 0x4e76, 0x4e77, 0x4c77, 0x4b78, 0x4977, 0x4976,
    0x487a, 0x4673, 0x457b, 0x4473, 0x447b, 0x4373, 0x437b, 0x4473, 0x457b, 0x4673, 0x467b, 0x4673,
    0x467b, 0x4673, 0x467c, 0x4673, 0x467d, 0x4672, 0x467d, 0x4571, 0x457d, 0x4471, 0x437f, 0x4271,
    0x427f, 0x3f71, 0x3e81, 0x3d72, 0x3d81, 0x3f71, 0x4181, 0x4072, 0x4180, 0x4273, 0x427f, 0x4274,
    0x427f, 0x4275, 0x417f, 0x4074, 0x3e7f, 0x3e74, 0x3d7f, 0x3d74, 0x3d7f, 0x3d74, 0x3d80, 0x3c74,
    0x3c81, 0x3b74, 0x3b81, 0x3a74, 0x3a81, 0x3874, 0x3881, 0x3875, 0x3881, 0x3875, 0x3881, 0x3875,
    0x3881, 0x3875, 0x3981, 0x3976, 0x3880, 0x3b77, 0x3b7f, 0x3c78, 0x3e7f, 0x4078, 0x417d, 0x4078,
    0x3c7b, 0x3b78, 0x3c7a, 0x3d79, 0x4179, 0x4377, 0x447b, 0x4578, 0x4d7b, 0x4577, 0x5c7c, 0x7977,
    0x767b, 0x5776, 0x3c7c, 0x4277, 0x4c7b, 0x4777, 0x407b, 0x3a76, 0x357b, 0x3577, 0x397d, 0x3b77,
    0x3d7d, 0x3f76, 0x3d7d, 0x3f76, 0x3f7d, 0x4076, 0x3f7d, 0x3f76, 0x3f7d, 0x3f76, 0x3f7d, 0x3f76,
    0x3f7d, 0x4076, 0x3f7d, 0x3d76, 0x3d7d, 0x3d78, 0x3d7d, 0x3d78, 0x3d7d, 0x3d78, 0x3d7d, 0x3d78,
    0x3d7d, 0x3d78, 0x3d7d, 0x3d78, 0x3d7d, 0x3d78, 0x3d7d, 0x3d78, 0x3d7d, 0x3d7f, 0x3d7d, 0x3d7f,
    0x3d7d, 0x3d7f, 0x3d7d, 0x3d7f, 0x3d7b, 0x3d7f, 0x3f79, 0x3f7f, 0x3f79, 0x3f7f, 0x3f79, 0x407f,
    0x4478, 0x447e, 0x4477, 0x457e, 0x4477, 0x447e, 0x4475, 0x447e, 0x7470, 0x806c, 0x886f, 0x836c,
    0x736e, 0x686c, 0x646e, 0x696c, 0x4879, 0x4670, 0x4579, 0x4571, 0x4479, 0x4473, 0x4379, 0x4176,
    0x3e79, 0x3d76, 0x4079, 0x4176, 0x4479, 0x4776, 0x4779, 0x4976, 0x477a, 0x4975, 0x4979, 0x4a75,
    0x4a79, 0x4975, 0x4679, 0x4475, 0x417a, 0x4075, 0x3d7a, 0x3b75, 0x3b79, 0x3e76, 0x3e79, 0x4076,
    0x4479, 0x4377, 0x4079, 0x3e78, 0x3879, 0x3577, 0x3279, 0x3177, 0x3179, 0x3278, 0x3279, 0x3277,
    0x3279, 0x3277, 0x307a, 0x2e79, 0x2d7d, 0x2b79, 0x287e, 0x287a, 0x2e7e, 0x347a, 0x3d7f, 0x427a,
    0x467f, 0x467b, 0x4580, 0x447a, 0x4280, 0x427a, 0x4282, 0x427b, 0x4082, 0x407c, 0x4082, 0x3f7c,
    0x3e82, 0x3c7c, 0x3982, 0x387c, 0x3482, 0x347c, 0x3482, 0x347c, 0x3482, 0x347c, 0x3482, 0x347c,
    0x3481, 0x347c, 0x3481, 0x347c, 0x3481, 0x347c, 0x3481, 0x347c, 0x3481, 0x347c, 0x3481, 0x347c,
    0x3481, 0x347c, 0x3481, 0x347c, 0x3580, 0x3577, 0x347f, 0x3476, 0x347f, 0x3476, 0x347f, 0x3476,
    0x347f, 0x3476, 0x347f, 0x3575, 0x357f, 0x3675, 0x367f, 0x3676, 0x3878, 0x3875, 0x3978, 0x3975,
    0x3978, 0x3975, 0x3978, 0x3a75, 0x3978, 0x3975, 0x3978, 0x3975, 0x3978, 0x3974, 0x3979, 0x3a74,
    0x3d7b, 0x3e72, 0x3f7b, 0x4072, 0x407b, 0x3f72, 0x3d7b, 0x3c73, 0x3a7b, 0x3a72, 0x3979, 0x3975,
    0x3977, 0x3976, 0x3976, 0x3977, 0x3973, 0x3a78, 0x3a70, 0x3c78, 0x4570, 0x4978, 0x4c70, 0x4f78,
    0x5d70, 0x5e78, 0x5e70, 0x5f78, 0x2e70, 0x2b78, 0x2672, 0x2477, 0x2a6a, 0x3e77, 0x5d6a, 0x6e77,
    0x7175, 0x6378, 0x4b79, 0x3877, 0x397b, 0x3978, 0x397b, 0x3978, 0x397b, 0x3978, 0x387c, 0x3879,
    0x397b, 0x397a, 0x397b, 0x397a, 0x397b, 0x397a, 0x397b, 0x397a, 0x397b, 0x397a, 0x3b7b, 0x3f7a,
    0x3f7d, 0x407a, 0x417d, 0x407a, 0x407b, 0x4074, 0x3f7a, 0x3f74, 0x3e79, 0x3e74, 0x3d79, 0x3d74,
    0x3d7a, 0x3b74, 0x3b7a, 0x3b74, 0x3b7a, 0x3b74, 0x3b7b, 0x3b74, 0x3b7b, 0x3b7a, 0x3b7b, 0x3b7b,
    0x3c7b, 0x3c7d, 0x3a7b, 0x3a7f, 0x387c, 0x377f, 0x367b, 0x3580, 0x357b, 0x3480, 0x347b, 0x3480,
    0x337b, 0x337f, 0x337b, 0x347e, 0x347b, 0x337e, 0x337b, 0x337e, 0x337b, 0x317d, 0x317b, 0x307d,
    0x307b, 0x317d, 0x317b, 0x347d, 0x3e79, 0x3f7c, 0x4179, 0x427b, 0x4279, 0x3f7b, 0x3b7a, 0x367b,
    0x3279, 0x307b, 0x307b, 0x2f7b, 0x2f7b, 0x2f7b, 0x307c, 0x317b, 0x307d, 0x317b, 0x307d, 0x327b,
    0x327d, 0x327b, 0x357d, 0x357b, 0x377d, 0x3a7b, 0x357d, 0x367b, 0x327d, 0x307b, 0x2e7d, 0x2c7b,
    0x297d, 0x2b7b, 0x2e7b, 0x2f7b, 0x347c, 0x367b, 0x397b, 0x3a7b, 0x377c, 0x397b, 0x377c, 0x367b,
    0x357b, 0x357b, 0x357b, 0x357b, 0x3679, 0x3678, 0x3579, 0x3477, 0x3579, 0x3777, 0x397a, 0x3b79,
    0x3b7a, 0x3d79, 0x407b, 0x437b, 0x457b, 0x457b, 0x477b, 0x467b, 0x3c7d, 0x3b7a, 0x3a7e, 0x3a7a,
    0x3b7d, 0x3b78, 0x397d, 0x3976, 0x3a7b, 0x3a76, 0x397b, 0x3975, 0x397b, 0x3976, 0x397d, 0x3975,
    0x3a80, 0x3a75, 0x3881, 0x3875, 0x3881, 0x3875, 0x3a80, 0x3a76, 0x3a80, 0x3a76, 0x397f, 0x3979,
    0x397f, 0x3979, 0x3a7f, 0x3a78, 0x397d, 0x3b77, 0x3f7d, 0x3f76, 0x407d, 0x4076, 0x457d, 0x4774,
    0x477d, 0x4772, 0x467d, 0x4670, 0x457d, 0x4470, 0x447c, 0x4373, 0x407a, 0x3f75, 0x3e79, 0x3d76,
    0x3d79, 0x3d76, 0x3d79, 0x3d76, 0x3b79, 0x3e76, 0x4179, 0x4176, 0x4479, 0x4776, 0x4e77, 0x4f76,
    0x5c75, 0x5a77, 0x5973, 0x5978, 0x5474, 0x5177, 0x4e75, 0x4b79, 0x4576, 0x4379, 0x3f77, 0x3e7b,
    0x3977, 0x377b, 0x3477, 0x327c, 0x3279, 0x307c, 0x3279, 0x347c, 0x3579, 0x387c, 0x397b, 0x397c,
    0x397b, 0x397c, 0x397d, 0x397c, 0x387d, 0x387c, 0x397b, 0x397c, 0x387e, 0x387e, 0x387e, 0x387e,
    0x387e, 0x387e, 0x387e, 0x387e, 0x387e, 0x397e, 0x3b7f, 0x3e7e, 0x407e, 0x427e, 0x447d, 0x467d,
    0x467b, 0x467b, 0x467b, 0x467b, 0x467b, 0x477b, 0x477a, 0x477b, 0x4879, 0x487c, 0x5377, 0x5f77,
    0x6e78, 0x716e, 0x6778, 0x5c6a, 0x5377, 0x516f, 0x4d76, 0x4975, 0x4476, 0x4180, 0x3d77, 0x3a86,
    0x6d6e, 0x8095, 0x9268, 0x8e9f, 0x835c, 0x7bab, 0x8456, 0x94a9, 0xab58, 0x95a2, 0x6858, 0x51a0,
    0x3c5e, 0x4f9e, 0x7459, 0x8fa1, 0x8c57, 0x8daf, 0x8d5d, 0x8ea9, 0x9869, 0x849d, 0x5d6e, 0x4898,
    0x3173, 0x3a86, 0x4e70, 0x597b, 0x856a, 0x986e, 0x8068, 0x556c, 0x3477, 0x387c, 0x3c78, 0x407e,
    0x4677, 0x4681, 0x4777, 0x4682, 0x3679, 0x3a87, 0x4178, 0x4a8a, 0x6376, 0x7094, 0x8574, 0x9098,
    0x856d, 0x4e9c, 0x4068, 0x6a99, 0x7467, 0x5395, 0x4d6e, 0x6995, 0x3d78, 0x3f84, 0x3f77, 0x3f84,
    0x3f78, 0x3f7f, 0x3e79, 0x3f7f, 0x3f79, 0x3f80, 0x3f79, 0x3f82, 0x3f79, 0x3f81, 0x3f79, 0x3f82,
    0x3f78, 0x4083, 0x4578, 0x4583, 0x5d79, 0x597c, 0x467a, 0x357b, 0x5179, 0x507b, 0x4a7b, 0x467e,
    0x437b, 0x4081, 0x3c7b, 0x3c82, 0x3d79, 0x3d82, 0x3d79, 0x3d82, 0x6379, 0x5482, 0x2b79, 0x1e82,
    0x3b7b, 0x3b82, 0x3c79, 0x3d82, 0x3c79, 0x3c82, 0x3d7c, 0x3d81, 0x417b, 0x4082, 0x427b, 0x4383,
    0x427b, 0x4082, 0x3d7b, 0x3b82, 0x3e79, 0x477f, 0x5877, 0x647e, 0x6977, 0x687d, 0x5e76, 0x5d7d,
    0x5675, 0x517b, 0x5674, 0x607b, 0x5974, 0x5882, 0x5676, 0x4582, 0x2777, 0x2980, 0x2e79, 0x307e,
    0x3379, 0x367e, 0x3b7a, 0x3b7e, 0x367d, 0x367f, 0x397e, 0x347f, 0x287f, 0x267f, 0x387d, 0x457f,
    0x487c, 0x407f, 0x327b, 0x2d7f, 0x307b, 0x337f, 0x377b, 0x397f, 0x3c77, 0x347e, 0x3075, 0x357e,
    0x3a76, 0x3a7e, 0x2b76, 0x1f7f, 0x3276, 0x2679, 0x3773, 0x567b, 0x686e, 0x5f81, 0x4f6d, 0x4f81,
    0x5076, 0x5280, 0x5476, 0x5280, 0x4c76, 0x4880, 0x4376, 0x3e80, 0x5976, 0x5981, 0x5976, 0x5981,
    0x4b76, 0x4880, 0x4576, 0x4480, 0x4c77, 0x3480, 0x2d75, 0x3580, 0x5870, 0x8c80, 0xae6e, 0x9080,
    0x6970, 0x5f80, 0x5970, 0x4f80, 0x4174, 0x3b81, 0x3175, 0x317f, 0x3379, 0x327d, 0x317b, 0x307d,
    0x317b, 0x337d, 0x347b, 0x367d, 0x377c, 0x3d7d, 0x3d7c, 0x3d7d, 0x3f7b, 0x407c, 0x427b, 0x437d,
    0x4279, 0x447d, 0x4b79, 0x4d7c, 0x4779, 0x3f7c, 0x3278, 0x2a7d, 0x2b77, 0x3e7d, 0x5573, 0x577d,
    0x5370, 0x4a7d, 0x4d6e, 0x557d, 0x5a6e, 0x5a7d, 0x5a6e, 0x5a7d, 0x556e, 0x4e7d, 0x3c6e, 0x337d,
    0x3a6d, 0x2b7c, 0x436e, 0x757d, 0x4077, 0x3f7d, 0x3a7b, 0x3a7c, 0x3776, 0x377d, 0x4177, 0x467d,
    0x4c76, 0x4b7d, 0x4577, 0x407c, 0x4377, 0x437c, 0x4379, 0x437d, 0x4379, 0x427d, 0x407b, 0x407c,
    0x3d7d, 0x3c7d, 0x3c80, 0x3c7d, 0x3c80, 0x3d7d, 0x3d7d, 0x407d, 0x427b, 0x417d, 0x3c79, 0x397d,
    0x3679, 0x357d, 0x3479, 0x347e, 0x3479, 0x337f, 0x3379, 0x3380, 0x3379, 0x3380, 0x3479, 0x3480,
    0x3579, 0x3480, 0x3379, 0x3280, 0x2e79, 0x2c80, 0x2a79, 0x2980, 0x3577, 0x3580, 0x3779, 0x3880,
    0x3a77, 0x3a80, 0x3b77, 0x3c80, 0x3776, 0x4880, 0x5975, 0x5980, 0x5075, 0x4980, 0x4d75, 0x5b7f,
    0x5774, 0x467e, 0x4374, 0x507d, 0x5075, 0x3f7d, 0x3b74, 0x497d, 0x6473, 0x637d, 0x5f72, 0x5b7d,
    0x5672, 0x547d, 0x5072, 0x4e7d, 0x487d, 0x467d, 0x427d, 0x3e7d, 0x3b7d, 0x377d, 0x357d, 0x347d,
    0x317b, 0x337d, 0x3579, 0x387c, 0x3a79, 0x3c7d, 0x3c7a, 0x3c7e, 0x3c79, 0x3c7f, 0x3b79, 0x3b7f,
    0x3a79, 0x3a7f, 0x3978, 0x397f, 0x2977, 0x2a7f, 0x2c76, 0x2f7f, 0x3776, 0x3b7f, 0x3e77, 0x3f7f,
    0x4078, 0x407f, 0x4278, 0x417f, 0x4279, 0x437f, 0x4679, 0x467f, 0x3f79, 0x3a7f, 0x2e7b, 0x287f,
    0x2d7b, 0x2e7f, 0x337b, 0x367f, 0x3a7a, 0x3a7f, 0x3a7a, 0x3b7f, 0x3b79, 0x3a7f, 0x3a79, 0x397f,
    0x3779, 0x377f, 0x3879, 0x377f, 0x377a, 0x367f, 0x357a, 0x357f, 0x257b, 0x257f, 0x277b, 0x287f,
    0x2c7d, 0x307f, 0x357b, 0x3880, 0x5b7a, 0x4c7f, 0x3879, 0x3580, 0x3379, 0x3480, 0x2a78, 0x1f7f,
]


async def reset_module(resets, clk):
    await ClockCycles(clk, 10)
    for rst in resets:
        rst.value = 1
    await ClockCycles(clk, 100)
    for rst in resets:
        rst.value = 0
    await RisingEdge(clk)
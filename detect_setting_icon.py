# from google import genai
# from PIL import Image, ImageDraw
# import io
# import json
# import os
# import logging
# from typing import List, Dict, Tuple, Optional
# from pydantic import BaseModel
#
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class DetectionResult(BaseModel):
#     box_2d: List[int]  # [ymin, xmin, ymax, xmax] 比例坐标(0-1000)
#     label: str
#     mask: str  # base64编码的分割掩码
#
#
# class SettingIconDetector:
#     def __init__(self, api_key: str):
#         self.client = genai.Client(api_key=api_key)
#         self.total_prompt_tokens = 0
#         self.total_candidates_tokens = 0
#         self.total_total_tokens = 0
#
#     def detect_setting_icon(self, image_bytes: bytes) -> Optional[Tuple[List[int], str]]:
#         """
#         检测设置图标
#         返回: (转换后的坐标[x1,y1,x2,y2]原始像素坐标, 标签) 或 None
#         """
#         prompt = """严格检测手机应用中的设置图标（必须是齿轮或六边形图标），要求：
#         1. 只识别标准的设置图标（⚙️或⎔形状）
#         2. 忽略所有包含"设置"文字但不是图标的元素
#         3. 优先检测屏幕四角区域（特别是右上角）
#         4. 图标大小通常在24-48dp范围内
#
#         输出格式（仅当找到真实设置图标时）：
#         [{
#             "box_2d": [y1,x1,y2,x2],  // 归一化坐标0-1000
#             "label": "setting icon",  // 必须包含"setting"
#             "mask": "base64encoded..." // 分割掩码
#         }]
#
#         如果没有设置图标，返回空列表[]"""
#
#         try:
#             image = Image.open(io.BytesIO(image_bytes))
#             width, height = image.size
#             logger.info(f"Image size: {width}x{height}")
#
#             response = self.client.models.generate_content(
#                 model="gemini-2.5-pro-exp-03-25",
#                 contents=[image, prompt],
#                 config={'response_mime_type': 'application/json'}
#             )
#
#             # Token统计
#             if hasattr(response, 'usage_metadata'):
#                 self.total_prompt_tokens += response.usage_metadata.prompt_token_count
#                 self.total_candidates_tokens += response.usage_metadata.candidates_token_count
#                 self.total_total_tokens += response.usage_metadata.total_token_count
#
#             try:
#                 data = json.loads(response.text)
#                 logger.debug(f"Raw Gemini response: {data}")
#
#                 if not isinstance(data, list):
#                     logger.warning("Invalid response format from Gemini")
#                     return None
#
#                 setting_icons = [
#                     item for item in data
#                     if "setting" in item.get("label", "").lower()
#                 ]
#
#                 if not setting_icons:
#                     logger.info("No setting icon detected")
#                     return None
#
#                 # 返回原始像素坐标 [x1,y1,x2,y2]
#                 bbox = setting_icons[0]["box_2d"]
#                 pixel_bbox = [
#                     int(bbox[1] * width / 1000),  # x1
#                     int(bbox[0] * height / 1000),  # y1
#                     int(bbox[3] * width / 1000),  # x2
#                     int(bbox[2] * height / 1000)  # y2
#                 ]
#                 logger.info(f"Detected setting icon at {pixel_bbox}")
#                 return pixel_bbox, setting_icons[0]["label"]
#
#             except json.JSONDecodeError as e:
#                 logger.error(f"JSON decode error: {str(e)}")
#                 return None
#
#         except Exception as e:
#             logger.error(f"Setting icon detection failed: {str(e)}")
#             return None
#
#
# if __name__ == "__main__":
#     # 测试代码
#     detector = SettingIconDetector("YOUR_API_KEY")
#     with open("settings_page.png", "rb") as f:
#         result = detector.detect_setting_icon(f.read())
#         if result:
#             bbox, label = result
#             print(f"Detected: {label} at {bbox}")


from PIL import Image
import io
import json
import logging
import base64
import requests
from typing import List, Tuple, Optional
from pydantic import BaseModel

# 配置 Gemini 接口
GEMINI_API_BASE = "http://jeniya.cn"
GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"
# GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
GEMINI_MAX_TOKENS = 8192

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DetectionResult(BaseModel):
    box_2d: List[int]  # [ymin, xmin, ymax, xmax]
    label: str
    mask: str  # base64编码的掩码图像


class SettingIconDetector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.total_prompt_tokens = 0
        self.total_candidates_tokens = 0
        self.total_total_tokens = 0

    def detect_setting_icon(self, image_bytes: bytes) -> Optional[Tuple[List[int], str]]:
        prompt = """识别手机应用中的“设置”图标或按钮，要求：
        1. 优先识别带有“齿轮形状”、“六边形”或写有“设置”字样的按钮；
        2. 位置通常在右上角，但不限于此；
        3. 可以是图标+文字组合或单独图标；
        4. 如果出现"设置"字样，直接输出"设置"字样所在的区域及标签信息（见下方格式），否则输出设置图标的区域及标签信息（同下方格式）

        输出格式：
        [{
            "box_2d": [y1,x1,y2,x2],
            "label": "setting icon",
            "mask": "base64encoded..."
        }]

        如未识别则返回 []
        """

        try:
            # 图片编码为 base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            payload = json.dumps({
                "model": GEMINI_MODEL,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"}
                             }
                        ]
                    }
                ],
                "temperature": 0.9,
                "max_tokens": GEMINI_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            })

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            response = requests.post(
                f"{GEMINI_API_BASE}/v1/chat/completions",
                headers=headers,
                data=payload
            )

            response_data = response.json()
            if 'usage' in response_data:
                usage = response_data['usage']
                self.total_prompt_tokens += usage.get('prompt_tokens', 0)
                self.total_candidates_tokens += usage.get('completion_tokens', 0)
                self.total_total_tokens += usage.get('total_tokens', 0)

            if 'choices' not in response_data or not response_data['choices']:
                logger.warning("No choices in response")
                return None

            content = response_data['choices'][0]['message']['content']
            if not content:
                logger.warning("Empty content in Gemini response")
                return None

            try:
                detections = json.loads(content)
                if not isinstance(detections, list):
                    logger.warning("Response is not a list")
                    return None

                setting_icons = [
                    d for d in detections
                    if "setting" in d.get("label", "").lower()
                ]

                if not setting_icons:
                    logger.info("No setting icon detected")
                    return None

                image = Image.open(io.BytesIO(image_bytes))
                width, height = image.size
                box = setting_icons[0]["box_2d"]
                pixel_box = [
                    int(box[1] * width / 1000),
                    int(box[0] * height / 1000),
                    int(box[3] * width / 1000),
                    int(box[2] * height / 1000),
                ]
                label = setting_icons[0]["label"]
                logger.info(f"Detected setting icon at {pixel_box}")
                return pixel_box, label

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response JSON: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            return None


if __name__ == "__main__":
    # 示例测试
    detector = SettingIconDetector(api_key="sk-BRmzn9gtHJs1w1S8sDexOjSAp2xSiV0cjGb32rMUCq9l3joS")
    with open("settings_page.png", "rb") as f:
        result = detector.detect_setting_icon(f.read())
        if result:
            bbox, label = result
            print(f"Detected: {label} at {bbox}")
        else:
            print("No setting icon detected.")

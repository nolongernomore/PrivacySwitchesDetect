import uiautomator2 as u2
from PIL import Image, ImageDraw
import io
import json
import os
import re
import time
import base64
import requests
from typing import List, Dict,Optional
from pydantic import BaseModel
from io import BytesIO

class GeminiSegmentationAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.total_prompt_tokens = 0
        self.total_candidates_tokens = 0
        self.total_total_tokens = 0
        self.model = "gemini-2.5-flash-preview-05-20"
        self.api_base = "http://jeniya.cn"

    def detect_ui_elements(self, image_bytes: bytes) -> Optional[Dict]:
        prompt = """请你严格按照以下指示步骤工作：
    你需要完成的工作是：
    （1）检测设置图标（当设置图标没检测出来时，你的任务变为检测菜单图标）
    （2）返回: (转换后的坐标[x1,y1,x2,y2]原始像素坐标, 标签) 或 None
    ### 你的思考过程（此部分仅用于解释，不要放入JSON） ###
    1. 分析界面中所有可能的设置图标候选
    2. 评估每个候选的特征：
       - 形状是否为齿轮/六边形，或写有"设置"字样
       - 位置是否符合常见设置图标位置，比如右上角（不一定会位于右上角，但是优先右上角）
       - 这个图标必须符合单独图标或者"图标+文字"两者其一的特征
    3.假如有设置图标，请你的检查到此结束（注意：你框选的坐标范围不要把设置图标漏在外面，也不要框选过多的空白区域）跳至输出JSON；假如没有，请你开始第4步的工作。
    4.假如页面没有设置图标，你需要开始分析界面中可能的菜单图标
    5.你还是优先查看右上角和左上角。识别是否有"由三条直线组成"的菜单图标（永远记得，优先左上角和右上角的检测，其余位置的可能性要更低）
    6.如果有，处理菜单图标（注意：你框选的坐标范围不要把菜单图标漏在外面，也不要框选过多的空白区域），跳至输出JSON；如果没有，返回空json。

    ### 你必须输出的JSON数据 ###
    [{
        "box_2d": [y1,x1,y2,x2],
        "label": "setting icon 或 menu icon"
    }]
    请先严格按照思考过程进行思考（你的思考过程也要输出！），然后输出正确的JSON数据。"""

        def encode_compressed_image(image_bytes: bytes, quality=20) -> str:
            with Image.open(io.BytesIO(image_bytes)) as img:
                buffered = BytesIO()
                img.save(buffered, format="PNG", quality=quality)
                return base64.b64encode(buffered.getvalue()).decode("utf-8")

        try:
            image_base64 = encode_compressed_image(image_bytes)

            payload = json.dumps({
                "model": self.model,
                "stream": True,
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
                "temperature": 0.3,
                "max_tokens": 10000
            })

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            full_content = ""
            with requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                data=payload,
                timeout=100,
                stream=True
            ) as response:
                if response.status_code != 200:
                    print(f"❌ HTTP错误: {response.status_code}")
                    return None

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data:'):
                            json_str = line_str[5:].strip()
                            if json_str == "[DONE]":
                                continue
                            try:
                                chunk_data = json.loads(json_str)
                                if 'choices' in chunk_data and chunk_data['choices']:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    full_content += content
                                    print(content, end='', flush=True)
                            except json.JSONDecodeError:
                                print(f"❌ 无法解析块: {json_str}")

            print("\n🧠 完整思维链解释内容：")
            print(full_content)

            json_match = re.search(r"```json\s*([\s\S]+?)\s*```", full_content)
            if not json_match:
                print("❌ 没有找到 JSON 代码块")
                return None

            json_str = json_match.group(1).strip()
            print("\n📦 提取的JSON内容:")
            print(json_str)

            try:
                detections = json.loads(json_str)
                if detections and isinstance(detections, list) and len(detections) > 0:
                    return detections[0]
                return None
            except Exception as e:
                print("❌ JSON解析失败:", e)
                return None

        except Exception as e:
            print(f"❌ API调用失败: {str(e)}")
            return None

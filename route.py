# import uiautomator2 as u2
# import json
# import time
# import os
# import logging
# from typing import List, Dict, Optional, Tuple
# from xml.etree import ElementTree as ET
# from detect_personal_icon import PersonalIconDetector
# from detect_setting_icon import SettingIconDetector
#
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# class PrivacySettingsNavigator:
#     def __init__(self, device_serial: str, app_package: str, gemini_api_key: str):
#         self.device = u2.connect(device_serial)
#         self.app_package = app_package
#         self.gemini_api_key = gemini_api_key
#         self.result = {"steps": []}
#         self.screen_width, self.screen_height = self.device.window_size()
#
#     def capture_screenshot(self) -> bytes:
#         """获取当前屏幕截图"""
#         temp_path = "temp_screenshot.png"
#         try:
#             self.device.screenshot(temp_path)
#             with open(temp_path, "rb") as f:
#                 data = f.read()
#             os.remove(temp_path)
#             return data
#         except Exception as e:
#             logger.error(f"Failed to capture screenshot: {str(e)}")
#             raise
#
#     def find_element_by_text(self, root, text_keywords):
#         """查找包含关键词的元素"""
#         for node in root.iter('node'):
#             node_text = node.get('text', '').lower()
#             if any(keyword in node_text for keyword in text_keywords):
#                 return node
#         return None
#
#     def find_and_click_privacy_settings(self, max_swipes: int = 5) -> bool:
#         """
#         在设置页面查找并点击隐私设置
#         返回: 是否成功找到并点击
#         """
#         privacy_keywords = ["隐私", "privacy"]
#
#         for attempt in range(max_swipes):
#             try:
#                 # 获取当前页面XML结构
#                 xml = self.device.dump_hierarchy()
#                 root = ET.fromstring(xml)
#
#                 # 查找隐私设置元素
#                 target_node = self.find_element_by_text(root, privacy_keywords)
#
#                 if target_node is not None:
#                     text = target_node.get('text', '')
#                     bounds = target_node.get('bounds')
#
#                     if not bounds:
#                         continue
#
#                     logger.info(f"找到隐私设置: {text}")
#
#                     # 记录到结果，初始设置 turnback 为 False
#                     self.result["steps"].append({"text": text, "turnback": False})
#
#                     # 解析坐标并点击
#                     bounds = bounds.strip('[]').split('][')
#                     x1, y1 = map(int, bounds[0].split(','))
#                     x2, y2 = map(int, bounds[1].split(','))
#                     center_x = (x1 + x2) // 2
#                     center_y = (y1 + y2) // 2
#
#                     self.device.click(center_x, center_y)
#                     time.sleep(2)
#                     return True
#
#                 # 如果没有找到，向下滑动
#                 if attempt < max_swipes - 1:
#                     logger.info(f"向下滑动查找 (尝试 {attempt + 1}/{max_swipes})")
#                     self.device.swipe(
#                         self.screen_width // 2,
#                         int(self.screen_height * 0.7),
#                         self.screen_width // 2,
#                         int(self.screen_height * 0.3),
#                         0.5
#                     )
#                     time.sleep(2)
#
#             except Exception as e:
#                 logger.error(f"查找隐私设置出错: {str(e)}")
#                 if attempt < max_swipes - 1:
#                     time.sleep(2)
#                 continue
#
#         logger.warning(f"滑动{max_swipes}次后仍未找到隐私设置")
#         return False
#
#     def find_and_click_personalization_settings(self, max_swipes: int = 5) -> bool:
#         """
#         在设置页面查找并点击个性化设置
#         返回: 是否成功找到并点击
#         """
#         personalization_keywords = ["个性化", "personalization"]
#
#         for attempt in range(max_swipes):
#             try:
#                 # 获取当前页面XML结构
#                 xml = self.device.dump_hierarchy()
#                 root = ET.fromstring(xml)
#
#                 # 查找个性化设置元素
#                 target_node = self.find_element_by_text(root, personalization_keywords)
#
#                 if target_node is not None:
#                     text = target_node.get('text', '')
#                     bounds = target_node.get('bounds')
#
#                     if not bounds:
#                         continue
#
#                     logger.info(f"找到个性化设置: {text}")
#
#                     # 记录到结果，turnback 恒为 False
#                     self.result["steps"].append({"text": text, "turnback": False})
#
#                     # 解析坐标并点击
#                     bounds = bounds.strip('[]').split('][')
#                     x1, y1 = map(int, bounds[0].split(','))
#                     x2, y2 = map(int, bounds[1].split(','))
#                     center_x = (x1 + x2) // 2
#                     center_y = (y1 + y2) // 2
#
#                     self.device.click(center_x, center_y)
#                     time.sleep(2)
#                     return True
#
#                 # 如果没有找到，向下滑动
#                 if attempt < max_swipes - 1:
#                     logger.info(f"向下滑动查找 (尝试 {attempt + 1}/{max_swipes})")
#                     self.device.swipe(
#                         self.screen_width // 2,
#                         int(self.screen_height * 0.7),
#                         self.screen_width // 2,
#                         int(self.screen_height * 0.3),
#                         0.5
#                     )
#                     time.sleep(2)
#
#             except Exception as e:
#                 logger.error(f"查找个性化设置出错: {str(e)}")
#                 if attempt < max_swipes - 1:
#                     time.sleep(2)
#                 continue
#
#         logger.warning(f"滑动{max_swipes}次后仍未找到个性化设置")
#         return False
#
#     def navigate(self) -> Dict:
#         """执行完整的导航流程"""
#         try:
#             # 1. 启动应用
#             logger.info(f"启动应用: {self.app_package}")
#             self.device.app_start(self.app_package)
#             time.sleep(5)
#
#             # 2. 查找并点击个人中心
#             logger.info("检测个人图标...")
#             personal_detector = PersonalIconDetector(self.gemini_api_key)
#             screenshot = self.capture_screenshot()
#             personal_result = personal_detector.detect_personal_icon(screenshot)
#
#             if not personal_result:
#                 logger.error("未检测到个人图标")
#                 return self.result
#
#             bbox, label = personal_result
#             logger.info(f"检测到个人图标位置: {bbox}")
#
#             # 记录归一化坐标
#             norm_bbox = [
#                 bbox[0] / self.screen_width,
#                 bbox[1] / self.screen_height,
#                 bbox[2] / self.screen_width,
#                 bbox[3] / self.screen_height
#             ]
#             self.result["steps"].append({
#                 "bounds": f"[{norm_bbox[0]:.3f},{norm_bbox[1]:.3f}][{norm_bbox[2]:.3f},{norm_bbox[3]:.3f}]",
#                 "turnback": False
#             })
#
#             # 点击个人中心
#             center_x = (bbox[0] + bbox[2]) // 2
#             center_y = (bbox[1] + bbox[3]) // 2
#             self.device.click(center_x, center_y)
#             time.sleep(3)
#
#             # 3. 查找并点击设置图标
#             logger.info("检测设置图标...")
#             setting_detector = SettingIconDetector(self.gemini_api_key)
#             screenshot = self.capture_screenshot()
#             setting_result = setting_detector.detect_setting_icon(screenshot)
#
#             if not setting_result:
#                 logger.error("未检测到设置图标")
#                 return self.result
#
#             bbox, label = setting_result
#             logger.info(f"检测到设置图标位置: {bbox}")
#
#             # 记录归一化坐标
#             norm_bbox = [
#                 bbox[0] / self.screen_width,
#                 bbox[1] / self.screen_height,
#                 bbox[2] / self.screen_width,
#                 bbox[3] / self.screen_height
#             ]
#             self.result["steps"].append({
#                 "bounds": f"[{norm_bbox[0]:.3f},{norm_bbox[1]:.3f}][{norm_bbox[2]:.3f},{norm_bbox[3]:.3f}]",
#                 "turnback": False
#             })
#
#             # 点击设置图标
#             center_x = (bbox[0] + bbox[2]) // 2
#             center_y = (bbox[1] + bbox[3]) // 2
#             self.device.click(center_x, center_y)
#             time.sleep(3)
#
#             # 4. 查找并点击隐私设置
#             logger.info("查找隐私设置...")
#             found_privacy = self.find_and_click_privacy_settings()
#
#             if not found_privacy:
#                 logger.error("未找到隐私设置，退出应用...")
#                 return self.result
#
#             # 回滚到设置页面
#             logger.info("回滚到设置页面...")
#             self.device.press("back")
#             time.sleep(2)
#
#             # 5. 查找并点击个性化设置
#             logger.info("查找个性化设置...")
#             found_personalization = self.find_and_click_personalization_settings()
#
#             # 6. 更新隐私设置步骤的turnback值
#             for step in reversed(self.result["steps"]):
#                 if "text" in step and ("隐私" in step["text"] or "privacy" in step["text"].lower()):
#                     step["turnback"] = found_personalization
#                     break
#
#             return self.result
#
#         except Exception as e:
#             logger.error(f"导航流程出错: {str(e)}")
#             return self.result
#         finally:
#             try:
#                 self.device.app_stop(self.app_package)
#             except Exception as e:
#                 logger.error(f"停止应用失败: {str(e)}")
#
#
# if __name__ == "__main__":
#     # 配置参数
#     CONFIG = {
#         "device_serial": "9C18158BBFC354",
#         "app_package": "com.mt.mtxx.mtxx",
#         "gemini_api_key": "AIzaSyAU7nPP6EeG5U9JtZiEfvj0NgcXfhhNRZc"
#     }
#
#     navigator = PrivacySettingsNavigator(
#         CONFIG["device_serial"],
#         CONFIG["app_package"],
#         CONFIG["gemini_api_key"]
#     )
#
#     result = navigator.navigate()
#     print("导航结果:")
#     print(json.dumps(result, indent=2, ensure_ascii=False))
#
#     # 保存结果到文件
#     with open("navigation_result.json", "w", encoding="utf-8") as f:
#         json.dump(result, f, indent=2, ensure_ascii=False)
#     print("结果已保存到 navigation_result.json")

import uiautomator2 as u2
import json
import time
import os
import logging
from typing import Dict, List

from CoT_personal_version import PersonalIconDetector
from CoT_setting_version import GeminiSegmentationAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleNavigator:
    def __init__(self, device_serial: str, app_package: str, gemini_api_key: str):
        self.device = u2.connect(device_serial)
        self.app_package = app_package
        self.gemini_api_key = gemini_api_key
        self.screen_width, self.screen_height = self.device.window_size()

    def capture_screenshot(self) -> bytes:
        """获取当前屏幕截图"""
        temp_path = "temp_screenshot.png"
        try:
            self.device.screenshot(temp_path)
            with open(temp_path, "rb") as f:
                data = f.read()
            os.remove(temp_path)
            return data
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise

    def normalize_bounds(self, bbox: List[int]) -> str:
        """将检测到的坐标归一化为[0,1]范围并格式化"""
        norm_bbox = [
            bbox[1] / 1000,  # x1
            bbox[0] / 1000,  # y1
            bbox[3] / 1000,  # x2
            bbox[2] / 1000   # y2
        ]
        return f"[{norm_bbox[0]:.3f},{norm_bbox[1]:.3f}][{norm_bbox[2]:.3f},{norm_bbox[3]:.3f}]"

    def get_click_coordinates(self, bbox: List[int]) -> (int, int):
        """根据归一化坐标和屏幕大小计算点击坐标"""
        norm_x1 = bbox[1] / 1000
        norm_y1 = bbox[0] / 1000
        norm_x2 = bbox[3] / 1000
        norm_y2 = bbox[2] / 1000

        center_x = int((norm_x1 + norm_x2) / 2 * self.screen_width)
        center_y = int((norm_y1 + norm_y2) / 2 * self.screen_height)
        return center_x, center_y

    def navigate(self) -> List[Dict]:
        """执行简化的导航流程，检测图标并点击验证"""
        result = []
        try:
            # # 1. 启动应用
            # logger.info(f"启动应用: {self.app_package}")
            # self.device.app_start(self.app_package)
            # time.sleep(5)

            # 创建结果目录
            os.makedirs("results", exist_ok=True)

            # 2. 查找并记录个人图标
            logger.info("检测个人图标...")
            personal_detector = PersonalIconDetector(self.gemini_api_key)
            screenshot = self.capture_screenshot()
            personal_result = personal_detector.detect_ui_elements(screenshot)

            if personal_result:
                logger.info(f"检测到个人图标: {personal_result}")
                result.append({
                    "bounds": self.normalize_bounds(personal_result["box_2d"]),
                    "text": "我的"
                })

                # 计算点击坐标
                center_x, center_y = self.get_click_coordinates(personal_result["box_2d"])
                logger.info(f"点击个人图标: ({center_x}, {center_y})")
                self.device.click(center_x, center_y)
                time.sleep(2)

                # 保存点击后的截图用于验证
                post_click_screenshot = self.capture_screenshot()
                with open(f"results/personal_clicked_{int(time.time())}.png", "wb") as f:
                    f.write(post_click_screenshot)

                time.sleep(2)

            # 3. 查找并记录设置图标
            logger.info("检测设置图标...")
            setting_detector = GeminiSegmentationAPI(self.gemini_api_key)
            screenshot = self.capture_screenshot()
            setting_result = setting_detector.detect_ui_elements(screenshot)

            if setting_result:
                logger.info(f"检测到设置图标: {setting_result}")
                result.append({
                    "bounds": self.normalize_bounds(setting_result["box_2d"]),
                    "text": "设置"
                })

                # 计算点击坐标
                center_x, center_y = self.get_click_coordinates(setting_result["box_2d"])
                logger.info(f"点击设置图标: ({center_x}, {center_y})")
                self.device.click(center_x, center_y)
                time.sleep(2)

                # 保存点击后的截图用于验证
                post_click_screenshot = self.capture_screenshot()
                with open(f"results/setting_clicked_{int(time.time())}.png", "wb") as f:
                    f.write(post_click_screenshot)

                # # 返回上一页
                # self.device.press("back")
                # time.sleep(2)

            return result

        except Exception as e:
            logger.error(f"导航流程出错: {str(e)}")
            return result
        # finally:
        #     try:
        #         self.device.app_stop(self.app_package)
        #     except Exception as e:
        #         logger.error(f"停止应用失败: {str(e)}")

if __name__ == "__main__":
    # 配置参数
    CONFIG = {
        "device_serial": "9C18158BBFC354",
        # "app_package": "com.kmxs.reader",#（七毛5次均通过）
        # "app_package": "com.mt.mtxx.mtxx",#（美图秀秀没问题）
        # "app_package": "com.tencent.qqmusic",#（qq音乐测了几次，失败了一次，是稍微偏了一点没点进我的页面）
        "app_package": "ctrip.android.view",#（携程旅行没有成功过，不知道为什么一直有偏差，感觉这个app一直有点问题）
        "gemini_api_key": "sk-BRmzn9gtHJs1w1S8sDexOjSAp2xSiV0cjGb32rMUCq9l3joS"
    }

    navigator = SimpleNavigator(
        CONFIG["device_serial"],
        CONFIG["app_package"],
        CONFIG["gemini_api_key"]
    )

    result = navigator.navigate()
    print("\n最终检测结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存结果到文件
    with open("detection_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("\n结果已保存到 detection_result.json")
    print("点击验证截图已保存到 results 目录")

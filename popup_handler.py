# popup_handler.py
import time
import uiautomator2 as u2
import json
import logging

logger = logging.getLogger(__name__)

# 弹窗配置示例，可放在 popup_config.json 中
DEFAULT_POPUP_CONFIG = [
    {
        "name": "系统权限—相机",
        "match": [{"text": ["允许", "拒绝"]}],
        "close_buttons": [{"text": "拒绝"}, {"text": "允许"}]
    },
    {
        "name": "内置广告弹窗",
        "match": [{"resourceId": "com.xxx:id/close"}],
        "close_buttons": [{"resourceId": "com.xxx:id/close"}]
    },
    {
        "name": "自定义遮罩层",
        "match": [{"className": "android.widget.FrameLayout", "depth": 0}],
        "close_buttons": [{"clickable": True, "bounds_within": [0.9, 0.05, 1.0, 0.2]}]
    }
]

def load_popup_config(path: str = None):
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_POPUP_CONFIG

def handle_popups(device: u2.Device, config: list = None, timeout: float = 5.0) -> bool:
    """
    自动检测并关闭弹窗。
    返回 True 表示检测到并至少尝试一次关闭，False 表示无弹窗或超时未检测到。
    """
    cfg = config or load_popup_config()
    start = time.time()
    while time.time() - start < timeout:
        xml = device.dump_hierarchy()
        for popup in cfg:
            matched = False
            # 检查是否匹配该弹窗
            for rule in popup["match"]:
                selector = device(**rule)
                if selector.exists:
                    matched = True
                    break
            if not matched:
                continue

            logger.info(f"检测到弹窗：{popup['name']}，尝试关闭…")
            # 依次尝试关闭按钮列表
            for btn_rule in popup["close_buttons"]:
                btn = device(**btn_rule)
                if btn.exists:
                    btn.click()
                    time.sleep(1)
                    break
            else:
                # 如果没有明确按钮，可尝试点击中间空白
                w, h = device.window_size()
                device.click(w//2, h//2)
                time.sleep(1)
            break  # 本轮只处理一个弹窗
        else:
            # 本轮未检测到任何配置弹窗
            return False
    logger.warning("弹窗处理超时，仍有剩余弹窗")
    return True

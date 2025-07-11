import uiautomator2 as u2 
import time
import copy
import json
import os
import hashlib
from typing import List, Dict
from route import SimpleNavigator

# from helpers import navigate_to_settings, model_inspect_page
from qwen_privacy_inspector import run_inspection

# 封装滑动逻辑
class ScrollStrategy:
    def __init__(self, start_ratio=0.9, end_ratio=0.25, duration=0.3, swipe_delay=0.5, max_swipes=10):
        self.start_ratio = start_ratio
        self.end_ratio = end_ratio
        self.duration = duration
        self.swipe_delay = swipe_delay
        self.max_swipes = max_swipes

    def swipe_until_no_change(self, device: u2.Device) -> bool:
        """
        滑动直到页面不再变化或达到最大滑动次数。
        返回 True 表示滑动过，False 表示无需滑动或已滑到底。
        """
        w, h = device.window_size()
        for _ in range(self.max_swipes):
            before_hash = self._dump_hierarchy_hash(device)
            device.swipe(
                w // 2, int(h * self.start_ratio),
                w // 2, int(h * self.end_ratio),
                self.duration
            )
            time.sleep(self.swipe_delay)
            after_hash = self._dump_hierarchy_hash(device)

            if before_hash == after_hash:
                return False  # 已滑到底
        return True  # 达到最大滑动次数仍未停

    def _dump_hierarchy_hash(self, device: u2.Device) -> str:
        xml = device.dump_hierarchy()
        return hashlib.md5(xml.encode("utf-8")).hexdigest()

# 全局结果容器，分别存普通隐私开关、个性化开关、个性化布局
privacy_switches: List[List[Dict]] = []
personality_switches: List[List[Dict]] = []
personality_layouts: List[List[Dict]] = []
enable_personalization_layout_dfs = True
def find_node_with_scroll(device: u2.Device, text: str, scroll_strategy: ScrollStrategy = None):
    """
    在可滚动界面中查找 text 对应的节点，支持滑动策略。
    """
    if scroll_strategy is None:
        scroll_strategy = ScrollStrategy()

    for _ in range(scroll_strategy.max_swipes + 1): # +1 是为了确保在不滑动的情况下也检查一次
        node = device(text=text)
        if not node.exists:
            node = device(description=text)
        if node.exists:
            return node

        # 如果没找到，尝试滑动并再次查找
        scrolled = scroll_strategy.swipe_until_no_change(device)
        if not scrolled:
            break # 如果没有滑动或者滑到底了，就停止查找
    return None


def safe_click_by_hierarchy(device: u2.Device, cx: int, cy: int,
                            max_retries: int = 2, wait_time: float = 1.0) -> bool:
    """
    通过对比 dump_hierarchy 前后 XML，判断点击是否切换了界面。
    返回 True 表示成功切换（或至少 XML 变化），False 表示失败。
    """
    prev_xml = device.dump_hierarchy()
    for attempt in range(1, max_retries + 1):
        device.click(cx, cy)
        time.sleep(wait_time)
        new_xml = device.dump_hierarchy()
        if new_xml != prev_xml:
            return True
        else:
            print(f"第 {attempt} 次点击后 XML 未变化，重试……")
    return False

def dfs_explore(device: u2.Device, curr_path: List[Dict]):
    # 先调用隐私检查
    result = run_inspection(device)
    time.sleep(0.5)

    if not result:  # None 或空列表都算失败
        return False, False
    # 新增：滑动至屏幕顶部，保证下次查找／截图从顶端开始

    is_current_page_popup = result.get("isPopup")


#     w, h = device.window_size()
#     device.swipe(w//2, int(h * 0.25), w//2, int(h * 0.9), duration=0.3)
#     time.sleep(1)#wait时间不够长
# # start_y = int(height * 0.75)
#         # end_y = int(height * 0.25)
#         # d.swipe(width // 2, start_y, width // 2, end_y, 0.1)
#         # time.sleep(wait_time)
#     # 1) switches 处理（普通隐私开关，只记录到 privacy_switches）
# 确保滑动到顶部（更可靠的滑动）
#     w, h = device.window_size()
#     for _ in range(3):  # 滑动3次确保到顶部
#         device.swipe(w//2, int(h*0.3), w//2, int(h*0.8), 0.5)
#         time.sleep(0.8)

    # 确保滑动到顶部（使用 scroll_to_top 方法）
    scroll_strategy = ScrollStrategy()
    scroll_strategy.scroll_to_top(device)
    time.sleep(1)

    for sw in result.get("switches", []):
        curr_path.append({
            "text": sw["text"],
            "current_state": sw["current_state"],
            "recommended_state": sw["recommended_state"],
            "analysis": sw["analysis"]
        })
        privacy_switches.append(copy.deepcopy(curr_path))
        print("记录 switch 路径：",
              " → ".join(n["text"] for n in curr_path),
              "=", sw["recommended_state"])
        curr_path.pop()

    # 1.5) personalization 处理
    personalization = result.get("personalization", {})

    # 1.5.1) personalization 中的 switches
    for psw in personalization.get("switches", []):
        curr_path.append({
            "text": psw["text"],
            "current_state": psw["current_state"],
            "recommended_state": psw["recommended_state"],
            "analysis": psw["analysis"]
        })
        personality_switches.append(copy.deepcopy(curr_path))
        print("记录 personalization switch 路径：",
              " → ".join(n["text"] for n in curr_path),
              "=", psw["recommended_state"])
        curr_path.pop()

    # 2) layouts：使用 bounds 中心点点击（普通隐私布局项，不在最终 JSON 单独输出）
    for layout in result.get("layouts", []):
        text = layout["text"]
        node = find_node_with_scroll(device, text)
        if not node:
            print(f"未找到布局项控件：{text}，跳过")
            # 滑动至屏幕顶部
            # w, h = device.window_size()
            # device.swipe(w // 2, int(h * 0.8), w // 2, int(h * 0.1), duration=0.3)
            # time.sleep(0.5)
            continue

        # 拿 bounds
        info = node.info.get("bounds", {})
        left, top = info["left"], info["top"]
        right, bottom = info["right"], info["bottom"]
        cx = (left + right) // 2
        cy = (top + bottom) // 2

        # 记录路径并安全点击
        curr_path.append({"text": text})
        if not safe_click_by_hierarchy(device, cx, cy):
            print(f"点击 “{text}” 失败，跳过此节点")
            curr_path.pop()
            continue

        print(f"点击布局项 “{text}” 中心点：({cx},{cy})")
        time.sleep(1)

        sub_explore_success, is_popup_after_sub_explore = dfs_explore(device, curr_path)

        # 根据子函数返回的弹窗状态决定返回方式
        if is_popup_after_sub_explore:
            print("子探索结束后检测到弹窗，点击屏幕上半部分返回")
            old_page_hierarchy = device.dump_hierarchy()
            w, h = device.window_size()
            device.click(w / 2, h / 9)
            time.sleep(1)
            new_page_hierarchy = device.dump_hierarchy()
            if old_page_hierarchy == new_page_hierarchy:
                print("检测到页面未变化，执行press back")
                device.press("back")
            time.sleep(1)
        else:
            print("子探索结束后非弹窗页面，执行 press back")
            device.press("back")
            time.sleep(1)

        # 如果子探索失败，则当前探索也应视为失败
        if not sub_explore_success:
            curr_path.pop()
            return False, False  # 提前返回，表示探索失败

        curr_path.pop()


    # 1.5.2) personalization 中的 layouts
    for playout in personalization.get("layouts", []):
        text = playout["text"]
        node = find_node_with_scroll(device, text)
        if not node:
            print(f"未找到个性化布局项控件：{text}，跳过")
            continue

        curr_path.append({"text": text})
        personality_layouts.append(copy.deepcopy(curr_path))
        print("记录 personalization layout 路径：",
              " → ".join(n["text"] for n in curr_path))

        # 新增探索个性化layout部分，控制变量为全局变量enable_personalization_layout_dfs
        if enable_personalization_layout_dfs:
            info = node.info.get("bounds", {})
            left, top = info["left"], info["top"]
            right, bottom = info["right"], info["bottom"]
            cx = (left + right) // 2
            cy = (top + bottom) // 2

            success = safe_click_by_hierarchy(device, cx, cy)
            if success:
                dfs_explore(device, curr_path)
                device.press("back")
                time.sleep(0.5)

        curr_path.pop()
    return True, is_current_page_popup

def main():
    device = u2.connect("9FK0219511000829")
    device.settings["wait_timeout"] = 20.0

    # 1) 前两级前缀
    curr_path: List[Dict] = []
    APP_PACKAGE = "com.kmxs.reader"       # 示例：实际改成你的目标包名
    GEMINI_API_KEY = "sk-BRmzn9gtHJs1w1S8sDexOjSAp2xSiV0cjGb32rMUCq9l3joS"

    # 2. 实例化并导航到设置页面
    navigator = SimpleNavigator(
        device_serial="9FK0219511000829",
        app_package=APP_PACKAGE,
        gemini_api_key=GEMINI_API_KEY
    )
    # 这会返回一个列表，包含“个人”和“设置”两步各自的 {"bounds": ..., "text": ...}
    prefix = navigator.navigate()
    for node in prefix:
        curr_path.append({"text": node["text"], "bounds": node["bounds"]})

    # 2) 若 prefix 中无 “设置”，则主动点击“设置”
    if not any(item["text"] == "设置" for item in curr_path):
        print("***************************************************")
        node = device(text="设置")
        if node.exists:
            info = node.info["bounds"]
            l, t, r, b = info["left"], info["top"], info["right"], info["bottom"]
            cx, cy = (l + r)//2, (t + b)//2
            curr_path.append({"text": "设置", "bounds": f"[{l},{t}][{r},{b}]"})
            device.click(cx, cy)
            print(f"点击“设置”节点中心：({cx},{cy})")
            time.sleep(1)
        else:
            print("前缀已包含“设置”或未找到“设置”节点，跳过点击")

    success, _ = dfs_explore(device, curr_path)
    if not success:
        print("判断裸标检测失败或json解析失败，程序即将终止")
        exit(1)

    # 判断是否有检测到任何路径
    if not privacy_switches and not personality_switches and not personality_layouts:
        print("未检测到任何设置开关，判断检测失败")
        return  # 直接返回，不写文件

    # 输出结果
    print("\n=== 全部隐私设置路径及推荐状态 ===")
    for path in privacy_switches:
        parts = []
        for node in path:
            text = node["text"]
            if "recommended_state" and "current_state" in node:
                parts.append(f"{text} = {node["current_state"]}/{node["recommended_state"]}")
            else:
                parts.append(text)
        print(" → ".join(parts))

    if personality_layouts:
        print("\n=== 个性化设置隐私路径 ===")
        for path in personality_switches:
            parts = []
            for node in path:
                text = node["text"]
                if "recommended_state" and "current_state" in node:
                    parts.append(f"{text} = {node["current_state"]}/{node["recommended_state"]}")
                else:
                    parts.append(text)
            print(" → ".join(parts))

    # 写入本地文件，改为每次生成一个不重复的 json 文件
    # 先在当前目录下创建一个文件夹存放所有结果
    output_dir = "all_paths_results"
    os.makedirs(output_dir, exist_ok=True)

    # 用包名+时间戳命名，避免覆盖
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_pkg = APP_PACKAGE.replace(".", "_")  # 将“.”替换，以做文件名安全处理
    output_file = os.path.join(output_dir, f"{safe_pkg}_{timestamp}.json")

    # 按要求组织最终 JSON 结构
    final_output = {
        "privacy_switches": [
            {
                **({"bounds": node.get("bounds")} if "bounds" in node else {}),
                **({"text": node["text"]} if "text" in node else {}),
                **({"current_state": node["current_state"],
                    "recommended_state": node["recommended_state"],
                    "analysis": node["analysis"]}
                   if "recommended_state" in node else {})
            }
            for path in privacy_switches
            for node in path
        ],
        "personality": {
            "personality_switches": [
                {
                    **({"bounds": node.get("bounds")} if "bounds" in node else {}),
                    **({"text": node["text"]} if "text" in node else {}),
                    **({"current_state": node["current_state"],
                        "recommended_state": node["recommended_state"],
                        "analysis": node["analysis"]}
                       if "recommended_state" in node else {})
                }
                for path in personality_switches
                for node in path
            ],
            "personality_layouts": [
                {"text": node["text"], **({"bounds": node.get("bounds")} if "bounds" in node else {})}
                for path in personality_layouts
                for node in path
            ]
        }
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(f"\n已将所有路径写入本地文件: {output_file}")

if __name__ == "__main__":
    main()

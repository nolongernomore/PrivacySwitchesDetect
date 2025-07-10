import time
import uiautomator2 as u2
from PIL import Image
import json
import datetime
import os
import qvq



# 创建保存截图文件的文件夹
save_dir = "screenshot"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)


def find_overlap(img1: Image.Image, img2: Image.Image, check_height: int = 100) -> int:
    """
    检测 img1 底部 与 img2 顶部 是否重复，返回重叠高度（像素）
    """
    width = img1.width
    for i in range(check_height, 0, -10):  # 每次减少10像素，逐步匹配
        box1 = (0, img1.height - i, width, img1.height)
        box2 = (0, 0, width, i)

        region1 = img1.crop(box1)
        region2 = img2.crop(box2)

        if region1.tobytes() == region2.tobytes():
            return i  # 找到重叠高度
    return 0  # 没有重叠

def take_long_screenshot(d: u2.Device, save_path: str = None, wait_time: float = 0.5):
    width, height = d.window_size()
    scroll_height = height - 150

    screenshots = []
    last_screenshot = None
    max_scrolls = 10  # 限制最大滑动次数
    reached_bottom = False

    for i in range(max_scrolls):
        img = d.screenshot(format='pillow').convert("RGB")
        if last_screenshot and img.tobytes() == last_screenshot.tobytes():
            reached_bottom = True
            break
        screenshots.append(img)
        last_screenshot = img

        start_y = int(height * 0.75)
        end_y = int(height * 0.25)
        d.swipe(width // 2, start_y, width // 2, end_y, 0.1)
        time.sleep(wait_time)

    if len(screenshots) >= 2:
        img1 = screenshots[-2]
        img2 = screenshots[-1]
        overlap = find_overlap(img1, img2)
        if overlap > 0:
            screenshots[-1] = img2.crop((0, overlap, img2.width, img2.height))

    total_height = sum(img.height for img in screenshots)
    long_img = Image.new("RGB", (width, total_height))
    y = 0
    for img in screenshots:
        long_img.paste(img, (0, y))
        y += img.height

    if not save_path:
        info = d.info
        package = info.get("currentPackageName", "unknown")
        activity = d.app_current().get('activity', '').split('.')[-1]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{package}.{activity}_{timestamp}.png"
        save_path = os.path.join(save_dir, filename)

    long_img.save(save_path)
    print(f"长图保存成功：{save_path}")
    return save_path, reached_bottom




def run_inspection(d: u2.Device) -> list:
    """统一入口：运行截图 + 提取隐私设置 """
    screenshot_path, reached_bottom = take_long_screenshot(d)
    if not reached_bottom:
        print("未滑到底部，判断裸标点击失败，结果无效")
        return None

    result = qvq.analyze_privacy_switches(
        image_path= screenshot_path,
        api_key="sk-583dd10e42854f8cac57e5ed5e65b1c4",
        prompt_path="prompt.txt",
        system_path="system.txt",
    )
    return result



if __name__ == "__main__":
    d = u2.connect("MKB4C20622028844")  # 修改为你实际的设备 ID
    result = run_inspection(d)
    print(json.dumps(result, ensure_ascii=False, indent=4))

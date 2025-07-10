import uiautomator2 as u2
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
from detect_setting_icon import SettingIconDetector
from detect_personal_icon import PersonalIconDetector


def get_xml_tree(device) -> Optional[ET.Element]:
    """
    抓取设备当前页面的 XML 树
    :param device: uiautomator2 设备对象
    :return: XML 树的根节点，如果抓取失败返回 None
    """
    try:
        xml_content = device.dump_hierarchy()
        root = ET.fromstring(xml_content)
        return root
    except Exception as e:
        print(f"Failed to get XML tree: {e}")
        return None


def parse_bounds(bounds_str: str) -> List[int]:
    """
    解析 bounds 字符串为坐标列表
    :param bounds_str: bounds 字符串，格式为 "[x1,y1][x2,y2]"
    :return: 坐标列表 [x1, y1, x2, y2]
    """
    bounds = bounds_str.strip('[]').split('][')
    x1, y1 = map(int, bounds[0].split(','))
    x2, y2 = map(int, bounds[1].split(','))
    return [x1, y1, x2, y2]


def calculate_overlap(box1: List[int], box2: List[int]) -> float:
    """
    计算两个边界框的重合程度
    :param box1: 边界框 1，格式为 [x1, y1, x2, y2]
    :param box2: 边界框 2，格式为 [x1, y1, x2, y2]
    :return: 重合程度，范围为 0 到 1
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    if x2 < x1 or y2 < y1:
        return 0

    intersection_area = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - intersection_area

    return intersection_area / union_area if union_area > 0 else 0


def find_best_match(xml_root: ET.Element, model_bounds: List[int]) -> Optional[Tuple[ET.Element, float]]:
    """
    找到与大模型识别出的边界框重合程度最高的 XML 元素
    :param xml_root: XML 树的根节点
    :param model_bounds: 大模型识别出的边界框，格式为 [x1, y1, x2, y2]
    :return: 重合程度最高的元素及其重合程度，如果未找到匹配元素返回 None
    """
    best_match = None
    best_overlap = 0

    for element in xml_root.iter():
        if 'bounds' in element.attrib:
            xml_bounds = parse_bounds(element.attrib['bounds'])
            overlap = calculate_overlap(model_bounds, xml_bounds)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = element

    if best_match is not None:
        return best_match, best_overlap
    return None


def main():
    # 连接设备
    device = u2.connect()

    # 获取屏幕截图
    screenshot = device.screenshot()
    with open('screenshot.png', 'wb') as f:
        screenshot.save(f)

    # 初始化检测器
    setting_api_key = "sk-BRmzn9gtHJs1w1S8sDexOjSAp2xSiV0cjGb32rMUCq9l3joS"
    personal_api_key = "sk-BRmzn9gtHJs1w1S8sDexOjSAp2xSiV0cjGb32rMUCq9l3joS"
    setting_detector = SettingIconDetector(setting_api_key)
    personal_detector = PersonalIconDetector(personal_api_key)

    # 读取截图字节数据
    with open('screenshot.png', 'rb') as f:
        image_bytes = f.read()

    # 检测设置图标
    setting_result = setting_detector.detect_setting_icon(image_bytes)
    if setting_result:
        setting_bbox, _ = setting_result
        print(f"Detected setting icon at {setting_bbox}")

        # 抓取 XML 树
        xml_root = get_xml_tree(device)
        if xml_root is not None:
            # 找到最佳匹配元素
            result = find_best_match(xml_root, setting_bbox)
            if result is not None:
                best_element, overlap = result
                print(f"找到设置图标最佳匹配元素，重合程度: {overlap}")
                print(f"元素属性: {best_element.attrib}")
            else:
                print("未找到设置图标匹配元素")

    # 检测个人中心图标
    personal_result = personal_detector.detect_personal_icon(image_bytes)
    if personal_result:
        personal_bbox, _ = personal_result
        print(f"Detected personal icon at {personal_bbox}")

        # 抓取 XML 树
        xml_root = get_xml_tree(device)
        if xml_root is not None:
            # 找到最佳匹配元素
            result = find_best_match(xml_root, personal_bbox)
            if result is not None:
                best_element, overlap = result
                print(f"找到个人中心图标最佳匹配元素，重合程度: {overlap}")
                print(f"元素属性: {best_element.attrib}")
            else:
                print("未找到个人中心图标匹配元素")


if __name__ == "__main__":
    main()
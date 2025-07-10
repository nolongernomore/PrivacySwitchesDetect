from openai import OpenAI
import base64
from PIL import Image
from io import BytesIO
import json

def analyze_privacy_switches(image_path: str, api_key: str, prompt_path: str, system_path: str) -> dict:
    def encode_compressed_image(image_path, quality=40, max_size=9 * 1024 * 1024):
        with Image.open(image_path) as img:
            img = img.convert("RGB")  # JPEG 不支持透明通道
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=quality)
            img_data = buffered.getvalue()
            # 若超出最大限制则继续压缩
            while len(img_data) > max_size and quality > 10:
                quality -= 5
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=quality)
                img_data = buffered.getvalue()
            print(f"压缩后图片大小：{len(img_data) / 1024:.2f} KB，使用质量：{quality}")
            return base64.b64encode(img_data).decode("utf-8")

    # 读取提示词文件
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    with open(system_path, "r", encoding="utf-8") as f:
        system_text = f.read()

    base64_image = encode_compressed_image(image_path)

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""  # 定义完整回复
    is_answering = False  # 判断是否结束思考过程并开始回复

    client = OpenAI(
        api_key= api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="qvq-max",  # 此处以 qvq-max 为例，可按需更换模型名称
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                    {"type": "text", "text":prompt_text},
                ],
            },
            {
                "role": "system",
                "content":system_text,
            },
        ],
        stream=True,
        seed=1234,
        temperature=0,
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )

    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")

    for chunk in completion:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if delta.content != "" and is_answering is False:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                print(delta.content, end='', flush=True)
                answer_content += delta.content

    # print("=" * 20 + "完整思考过程" + "=" * 20 + "\n")
    # print(reasoning_content)
    # print("=" * 20 + "完整回复" + "=" * 20 + "\n")
    # print(answer_content)

    cleaned_text = answer_content.strip()
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[len("```json"):].strip()
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-len("```")].strip()

    # 尝试解析为 JSON
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("无法解析返回的内容为 JSON 格式.")
        return {}



if __name__ == "__main__":
    result = analyze_privacy_switches(
        image_path=r"D:\study\code\Python\geminiText\long_screenshot.png",
        api_key="sk-583dd10e42854f8cac57e5ed5e65b1c4",
        prompt_path="prompt.txt",
        system_path="system.txt"
    )

    print("\n最终解析结果为：\n", result["answer"])

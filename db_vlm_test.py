import os
from volcenginesdkarkruntime import Ark
import cv2
import base64


# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
    api_key=os.environ.get("ARK_API_KEY"),
)

get_vlm_response = lambda img, vlm_prompt: client.chat.completions.create(
    # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
    model="doubao-1-5-vision-pro-32k-250115",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": vlm_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}"
                    },
                },
            ],
        }
    ],
    
)


image_path = "./office.jpg"
image = cv2.imread(image_path)

vlm_prompt = "我是一个机器人，当前是我眼睛看到的场景，我想完成面前这张桌子的清理。我会的技能有：1）移动本体；2）抓取桌上的东西并放到目标地点，帮我生成我的子动作，达到完成任务的目的"

# 将图片编码为 jpg 格式的 buffer   
_, buffer = cv2.imencode('.jpg', image)
encoded_image = base64.b64encode(buffer).decode('utf-8')
vlm_response = get_vlm_response(encoded_image, vlm_prompt)

print(vlm_response.choices[0])

# print(response.choices[0])
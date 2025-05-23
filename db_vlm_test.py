import os
from volcenginesdkarkruntime import Ark
import cv2
import base64
import time
import re

def get_vlm_response(img, vlm_prompt):
    client = Ark(
        # 此为默认路径，您可根据业务所在地域进行配置
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
        api_key=os.environ.get("ARK_API_KEY"),
    )
    vlm_response = client.chat.completions.create(
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
    return vlm_response


def get_figure_dict():
    def image_encode(image_path):
        image = cv2.imread(image_path)
        _, buffer = cv2.imencode('.jpg', image)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        return encoded_image
    image_path = ['./figure/step0.jpg', './figure/step1.jpg', './figure/step1_2.jpg', './figure/step2.jpg']

    dict = {"0": image_encode(image_path[0]), "1": image_encode(image_path[1]), "2": image_encode(image_path[2]), "3": image_encode(image_path[3])}
    return dict

def split_tasks_camera(vlm_prompt):
    for _ in range(3):
        cap.read()
        time.sleep(0.05)
    ret, frame = cap.read()
    _, buffer = cv2.imencode('.jpg', frame)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    vlm_response = get_vlm_response(encoded_image, vlm_prompt)

def split_tasks_figure(encoded_image, vlm_prompt):
    vlm_response = get_vlm_response(encoded_image, vlm_prompt)
    return vlm_response.choices[0].message.content
    


def send_task(tasks):
    for task in tasks:
        print(task)
        next_task = False
        while(not next_task):
            for _ in range(3):
                cap.read()
                time.sleep(0.05)

            ret, frame = cap.read()

            # print(frame.shape)

            # vlm_prompt = "我是一个机器人，当前是我眼睛看到的场景，我想完成面前这张桌子的清理。我会的技能有：1）移动本体；2）抓取桌上的东西并放到目标地点，帮我生成我的子动作，达到完成任务的目的"
            vlm_prompt = task + "If true, just return True."
            # 将图片编码为 jpg 格式的 buffer   
            _, buffer = cv2.imencode('.jpg', frame)
            # cv2.imwrite("camera"+str(time.time())+".jpg", frame)

            encoded_image = base64.b64encode(buffer).decode('utf-8')
            # print(len(encoded_image))
            vlm_response = get_vlm_response(encoded_image, vlm_prompt)

            print(vlm_response.choices[0].message.content)
            if vlm_response.choices[0].message.content == "True":
                next_task = True
            else:
                next_task = False
            time.sleep(CAMERA_INTERVAL)

    print("all tasks done!")


def main():

    camera_index = 0
    cap = cv2.VideoCapture(camera_index)
    CAMERA_INTERVAL = 5 # seconds

    vlm_prompt = "Assume you are a robot, the desk in this picture needs to be cleaned. You have two skills, one is to pick something into the box, the other one is to wipe the table with a sponge. Please give me the sub-actions to complete the desk cleaning task. The sub-actions should be in the form of a list."
    figure_dict = get_figure_dict()
    response = split_tasks_figure(figure_dict["0"], vlm_prompt)
    # 使用正则表达式按数字加点分割
    spilted_response = re.split(r'\d+\.\s*', response)

    # 去除空字符串，得到真正的内容列表
    sub_task_list = [p.strip() for p in spilted_response if p.strip()]
    print(sub_task_list)

    # 发送任务
    send_task(sub_task_list)


if __name__ == "__main__":
    main()

import os
from volcenginesdkarkruntime import Ark
import cv2
import base64
import time
import re
import subprocess
import signal

# export ARK_API_KEY='3db64cd1-9134-44ea-ba16-2eb83d6e7d6a' # yijia的key，需要时常看这个key是否用完，用完了就换一个免费的
# export ARK_API_KEY='080e47d2-2b23-4899-a2e9-68f22cef56a3' # weigang的key，需要时常看这个key是否用完，用完了就换一个免费的


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

def image_encode(image_path):
    image = cv2.imread(image_path)
    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image


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









def send_task(task):
    print()
    print("@@ send task: ", task)
    if "sandbag" in task:
        # 启动一个新的进程组
        process = subprocess.Popen(
            ['source', 'xxx.sh'],
            preexec_fn=os.setsid  # 在一个新的进程组中运行
        ) # 调用抓沙包的script
    elif "sponge" in task:
        # 启动一个新的进程组
        process = subprocess.Popen(
            ['source', 'xxx.sh'],
            preexec_fn=os.setsid  # 在一个新的进程组中运行
        )  # 调用海绵清桌子的script
    return process



def send_tasks(tasks):
    num = 0
    CAMERA_INTERVAL = 2 # 需要测量一下摄像头保存照片的间隔
    for task in tasks:
        robot_process = send_task(task)
        # print(task)
        next_task = False
        while(not next_task):
            vlm_prompt = task + " If the subtask finished in this picture, just return one word \"True\"."
            print("========================")
            print("prompt sent to vlm: ", vlm_prompt)
            print("current camera state: ", str(num))
            encoded_image = image_encode('path2fig')
            num += 1
            vlm_response = get_vlm_response(encoded_image, vlm_prompt)

            print("vlm response: ", vlm_response.choices[0].message.content)
            if vlm_response.choices[0].message.content == "True":
                next_task = True
                # 杀掉整个进程组
                os.killpg(os.getpgid(robot_process.pid), signal.SIGTERM)
                time.sleep(3)
            else:
                next_task = False
            time.sleep(CAMERA_INTERVAL)

    print("all tasks done!")


def main():
    vlm_prompt = "Assume you are a robot, the desk in this picture needs to be cleaned. You have two skills, one is to pick something into the box, the other one is to wipe the table with a sponge. Please give me the sub-actions to complete the desk cleaning task. The sub-actions should be in the form of a list."
    # figure_dict = get_figure_dict()
    response = split_tasks_figure(figure_dict["0"], vlm_prompt)
    # 使用正则表达式按数字加点分割
    spilted_response = re.split(r'\d+\.\s*', response)

    # 去除空字符串，得到真正的内容列表
    sub_task_list = [p.strip() for p in spilted_response if p.strip()]
    print("The prompt has been spilted into several sub-task: ",sub_task_list)

    # desk_state_figure = [figure_dict["0"], figure_dict["0"], figure_dict["1"], figure_dict["1"], figure_dict["1"], figure_dict["3"], figure_dict["3"]]

    # 发送任务
    send_tasks(sub_task_list)


if __name__ == "__main__":
    main()

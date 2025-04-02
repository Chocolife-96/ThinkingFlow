import os
from volcenginesdkarkruntime import Ark
import base64
import cv2
import time

from test_db_tts import *
from test_db_stream_asr import *



# Official
api_key = "c5536845-bb24-47e5-bb4e-31076d88b831"
vlm_model = "ep-20241220200741-8267s"
llm_model = "ep-20241220210317-m7vsf"



CAMERA_INTERVAL = 1 # seconds

# 初始化Ark客户端
client = Ark(api_key=api_key)


# Initialize the camera
camera_index = 1  # Change this to the index of the camera you want to use
cap = cv2.VideoCapture(camera_index)



# Define a prompt for the VLM model
vlm_prompt_heading = """
你需要首先描述这张照片里的场景信息，有哪些物品和人员等，然后结合场景回答问题。
回答需要按下面的格式给出输出：
[Scene]: ...整体场景描述...
[Answer]: ...你的回答...

问题如下：
"""
vlm_prompt = vlm_prompt_heading + "请分辨这张照片是什么环境"


# Define a template to get the response from the vlm model
get_vlm_response = lambda img, vlm_prompt: client.chat.completions.create(
        model=vlm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": vlm_prompt,
                    },
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

# process the output of VLM model and split the scene and answer
def process_vlm_response(vlm_response_text):
    scene = ""
    answer = ""
    scene_start = vlm_response_text.find("[Scene]:") + len("[Scene]:")
    answer_start = vlm_response_text.find("[Answer]:") + len("[Answer]:")

    if scene_start != -1:
        scene = vlm_response_text[scene_start:].split("[Answer]:")[0].strip()
    if answer_start != -1:
        answer = vlm_response_text[answer_start:].strip()

    return scene, answer

# define a template to get the response from the llm model
get_llm_response = lambda oldscene, currentscene: client.chat.completions.create(
        model=llm_model,
        messages = [
            {"role": "system",
             "content": f"""
             你是一个提问者，接收到两个由照片产生的场景描述文字，你需要
             首先，对这两个场景做对比，分辨其中的变化。
             其次，然后再结合当前场景，以及场景的变化问一个问题，问题要简洁。
             如果没有旧场景，则只针对当前场景提问。
             """},
            {"role": "user", "content": f"""
             [旧场景]: {oldscene}
             [当前场景]: {currentscene}
             """},
        ],
    )


oldscene = ""
currentscene = ""

steps = 0
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Encode the frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)

    # ======= load from local ===========
    # image_path = "office.jpg"
    # image = cv2.imread(image_path)

    # # 将图片编码为 jpg 格式的 buffer   
    # _, buffer = cv2.imencode('.jpg', image)
    # ======= end =======================

    encoded_image = base64.b64encode(buffer).decode('utf-8')

    # Use the encoded image and the prompt to get the response from the VLM model
    vlm_response = get_vlm_response(encoded_image, vlm_prompt)
    vlm_resp_text = vlm_response.choices[0].message.content
    oldscene = currentscene
    currentscene, vlm_answer = process_vlm_response(vlm_resp_text)
    print(f"\033[92m\n#{steps} VLM explains current scene: {currentscene}\033[0m")
    print(f"\033[92m\n#{steps} VLM answers question: {vlm_answer}\033[0m")

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(tts_request_submit(vlm_answer))
    asyncio.run(tts_request_submit(vlm_answer))

    # # Use the current scene and the old scene to get the response from the LLM model
    # llm_response = get_llm_response(oldscene, currentscene)
    # llm_resp_text = llm_response.choices[0].message.content
    # print(f"\033[96m\n#{steps} LLM generated question: {llm_resp_text}\033[0m")
    # question_to_vlm = llm_resp_text

    # Use ASR to get the question from the user
    asr_text = fixed_length_audio()
    if any(keyword in asr_text for keyword in ["退出", "结束", "exit", "bye", "挂断"]):
        break
    elif asr_text == "":
        question_to_vlm = "描述一下这张照片里的场景"
    else:
        print(f"\033[96m\n#{steps} ASR detected question: {asr_text}\033[0m")
        question_to_vlm = asr_text



    # Use LLM response as the prompt for the next VLM model
    vlm_prompt = f"{vlm_prompt_heading} 请回答以下问题：\n{question_to_vlm}"
    
    # Wait for several seconds
    time.sleep(CAMERA_INTERVAL)

# Release the camera
cap.release()
cv2.destroyAllWindows()
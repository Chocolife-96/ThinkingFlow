# from gtts import gTTS
# import os
# from playsound import playsound
# from pydub import AudioSegment
# from pydub.playback import play

# text = "hello, what are you doing? Are you ok?"
# tts = gTTS(text=text, lang='zh')
# tts.save("output.mp3")

# # 播放（Windows）
# # os.system("start output.mp3")
# # playsound("output.mp3")
# # 

# sound = AudioSegment.from_file("output.mp3")
# # 修改播放速度（通过更改 frame_rate 实现）
# def change_speed(sound, speed=1.0):
#     new_frame_rate = int(sound.frame_rate * speed)
#     return sound._spawn(sound.raw_data, overrides={'frame_rate': new_frame_rate}).set_frame_rate(sound.frame_rate)

# # 加速 1.5 倍
# faster_sound = change_speed(sound, 2.0)

# # 播放
# play(faster_sound)


import asyncio
import edge_tts
from playsound import playsound


# 文本内容
text = "Assume you are a robot, the desk in this picture needs to be cleaned. You have two skills, one is to pick something into the box, the other one is to wipe the table with a sponge. Please give me the sub-actions to complete the desk cleaning task. The sub-actions should be in the form of a list."

# 配置参数
voice = "zh-CN-YunyangNeural"  # 中文女声（还有 Xiaoyi、Yunjian 等）
rate = "+20%"                   # 语速加快20%，可用 -20%、+0%、+50% 等
volume = "+0%"                  # 音量，支持 -100% 到 +100%

# 异步朗读函数
async def tts():
    communicate = edge_tts.Communicate(
        text, voice=voice, rate=rate, volume=volume
    )
    await communicate.save("output.mp3")

# 运行
asyncio.run(tts())

playsound("output.mp3")
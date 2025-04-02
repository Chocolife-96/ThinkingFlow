#coding=utf-8

'''
requires Python 3.6 or later

pip install asyncio
pip install websockets

'''

import asyncio
import websockets
import uuid
import json
import gzip
import copy
import pyaudio
from io import BytesIO
from pydub import AudioSegment

MESSAGE_TYPES = {11: "audio-only server response", 12: "frontend server response", 15: "error message from server"}
MESSAGE_TYPE_SPECIFIC_FLAGS = {0: "no sequence number", 1: "sequence number > 0",
                               2: "last message from server (seq < 0)", 3: "sequence number < 0"}
MESSAGE_SERIALIZATION_METHODS = {0: "no serialization", 1: "JSON", 15: "custom type"}
MESSAGE_COMPRESSIONS = {0: "no compression", 1: "gzip", 15: "custom compression method"}

appid = "6372825325"
token = "CJeZd0ctydxB5m3kDSBtxByLbKDVQbsz"
cluster = "volcano_tts"
# voice_type = "zh_male_beijingxiaoye_moon_bigtts"
# voice_type = "zh_male_yangguangqingnian_moon_bigtts"
voice_type = "zh_male_tiancaitongsheng_mars_bigtts"
host = "openspeech.bytedance.com"
api_url = f"wss://{host}/api/v1/tts/ws_binary"

# version: b0001 (4 bits)
# header size: b0001 (4 bits)
# message type: b0001 (Full client request) (4bits)
# message type specific flags: b0000 (none) (4bits)
# message serialization method: b0001 (JSON) (4 bits)
# message compression: b0001 (gzip) (4bits)
# reserved data: 0x00 (1 byte)
default_header = bytearray(b'\x11\x10\x11\x00')

request_json = {
    "app": {
        "appid": appid,
        "token": "access_token",
        "cluster": cluster
    },
    "user": {
        "uid": "388808087185088"
    },
    "audio": {
        "voice_type": "xxx",
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": "xxx",
        "text": """
        """,
        "text_type": "plain",
        "operation": "xxx"
    }
}


    





async def tts_request_submit(text="辉羲智能，你好"):
    submit_request_json = copy.deepcopy(request_json)
    submit_request_json["audio"]["voice_type"] = voice_type
    submit_request_json["request"]["reqid"] = str(uuid.uuid4())
    submit_request_json["request"]["operation"] = "submit"
    submit_request_json["request"]["text"] = text
    payload_bytes = str.encode(json.dumps(submit_request_json))
    payload_bytes = gzip.compress(payload_bytes)  # if no compression, comment this line
    full_client_request = bytearray(default_header)
    full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))  # payload size(4 bytes)
    full_client_request.extend(payload_bytes)  # payload
    print("request json: ", submit_request_json)
    print("\nrequest bytes: ", full_client_request)

    # PyAudio setup
    p = pyaudio.PyAudio()
    stream = None

    header = {"Authorization": f"Bearer; {token}"}
    async with websockets.connect(api_url, extra_headers=header, ping_interval=None) as ws:
        await ws.send(full_client_request)
        # Buffer for MP3 data
        mp3_buffer = BytesIO()
        while True:
            res = await ws.recv()
            done, chunk = parse_response(res)
            # Append the chunk to the buffer
            if chunk:
                mp3_buffer.write(chunk)            
            if done:
                try:
                    mp3_buffer.seek(0)  # Rewind the buffer
                    audio = AudioSegment.from_file(mp3_buffer, format="mp3")
                    raw_data = audio.raw_data
                    # Initialize PyAudio stream if not already done
                    if stream is None:
                        stream = p.open(
                            format=p.get_format_from_width(audio.sample_width),
                            channels=audio.channels,
                            rate=audio.frame_rate,
                            output=True
                        )
                    # Play the raw audio data
                    stream.write(raw_data)
                    # mp3_buffer = BytesIO()
                except Exception as e:
                    print(f"Error decoding MP3 chunk: {e}")
                break

        print("\nClosing the connection...")

    # Close PyAudio stream
    if stream:
        stream.stop_stream()
        stream.close()
    p.terminate()



def parse_response(res):
    print("--------------------------- response ---------------------------")
    # print(f"response raw bytes: {res}")
    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0f
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0f
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0f
    reserved = res[3]
    header_extensions = res[4:header_size*4]
    payload = res[header_size*4:]
    print(f"            Protocol version: {protocol_version:#x} - version {protocol_version}")
    print(f"                 Header size: {header_size:#x} - {header_size * 4} bytes ")
    print(f"                Message type: {message_type:#x} - {MESSAGE_TYPES[message_type]}")
    print(f" Message type specific flags: {message_type_specific_flags:#x} - {MESSAGE_TYPE_SPECIFIC_FLAGS[message_type_specific_flags]}")
    print(f"Message serialization method: {serialization_method:#x} - {MESSAGE_SERIALIZATION_METHODS[serialization_method]}")
    print(f"         Message compression: {message_compression:#x} - {MESSAGE_COMPRESSIONS[message_compression]}")
    print(f"                    Reserved: {reserved:#04x}")
    if header_size != 1:
        print(f"           Header extensions: {header_extensions}")
    
    audio_segment = None
    if message_type == 0xb:  # audio-only server response
        if message_type_specific_flags == 0:  # no sequence number as ACK
            print("                Payload size: 0")
            return False, audio_segment
        else:
            sequence_number = int.from_bytes(payload[:4], "big", signed=True)
            payload_size = int.from_bytes(payload[4:8], "big", signed=False)
            payload = payload[8:]
            print(f"             Sequence number: {sequence_number}")
            print(f"                Payload size: {payload_size} bytes")
        audio_segment = payload
        if sequence_number < 0:
            return True, audio_segment
        else:
            return False, audio_segment
    elif message_type == 0xf:
        code = int.from_bytes(payload[:4], "big", signed=False)
        msg_size = int.from_bytes(payload[4:8], "big", signed=False)
        error_msg = payload[8:]
        if message_compression == 1:
            error_msg = gzip.decompress(error_msg)
        error_msg = str(error_msg, "utf-8")
        print(f"          Error message code: {code}")
        print(f"          Error message size: {msg_size} bytes")
        print(f"               Error message: {error_msg}")
        return True, audio_segment
    elif message_type == 0xc:
        msg_size = int.from_bytes(payload[:4], "big", signed=False)
        payload = payload[4:]
        if message_compression == 1:
            payload = gzip.decompress(payload)
        print(f"            Frontend message: {payload}")
    else:
        print("undefined message type!")
        return True, audio_segment


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tts_request_submit("这是一条测试语音，用于测试语音合成功能。"))

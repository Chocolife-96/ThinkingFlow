import cv2
import tkinter as tk
from PIL import Image, ImageTk

class CameraApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # 打开摄像头（0 是默认设备编号）
        self.vid = cv2.VideoCapture(0)
        if not self.vid.isOpened():
            raise RuntimeError("无法打开摄像头。")

        self.label = tk.Label(window)
        self.label.pack()

        self.update()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            # 转换 BGR 到 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)

            self.label.configure(image=photo)
            self.label.image = photo

        # 每 15 毫秒更新一次画面
        self.window.after(15, self.update)

    def on_closing(self):
        self.vid.release()
        self.window.destroy()

# 启动应用
CameraApp(tk.Tk(), "摄像头实时显示")

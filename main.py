import tkinter as tk
from left_canvas import LeftCanvas
from results.build.gui import ResultCanvas
from sessions.gui import SessionCanvas
import cv2
from PIL import Image, ImageTk
import uuid, requests
import os, json
from toggle import ToggleButton
import asyncio, httpx

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sliding Canvas Example")
        self.width, self.height = 1280, 832
        self.geometry(f"{self.width}x{self.height}")
        self.canvas = tk.Canvas(self, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.left_canvas = LeftCanvas(self.canvas, width=self.width, height=self.height - 75)
        self.left_canvas.pack(fill="both", expand=True)
        
        self.panel_open = False
        self.left_window = self.canvas.create_window(0, 0, anchor="nw",
                                                     window=self.left_canvas,
                                                     width=self.width, height=self.height - 75)
        
        self.result_canvas = ResultCanvas(self.canvas, width=0, height=self.height - 75)
        self.session_canvas = SessionCanvas(self.canvas, width=0, height=self.height - 75)
        self.result_window = self.canvas.create_window(self.width, 0, anchor="nw",
                                                       window=self.result_canvas,
                                                       width=0, height=self.height - 75)
        self.session_window = self.canvas.create_window(self.width, 0, anchor="nw",
                                                        window=self.session_canvas,
                                                        width=0, height=self.height - 75)
        self.left_width = self.width
        self.right_width = 0
        self.right_window = None

        self.canvas.bind("<Configure>", self.on_configure)

        self.ip_address = "http://100.86.165.5:8002/all"
        self.camera_type = "0"
        if self.camera_type == "0":
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture('rtsp://admin:DVYMYI@10.10.126.122/camera/h264/ch1/main/av_stream')

        self.create_button()
        self.render_text()


    def get_results(self):
        session_id = uuid.uuid4()
        ims = {}
        def capture_image():
            _, frame, _, _, _, _ = self.left_canvas.get_capture()
            if frame is not None:
                return frame
            return None
        frame = capture_image()
        _, im_encoded = cv2.imencode(".png", frame)
        im_bytes = im_encoded.tobytes()
        ims["front"] = ("im_1.png", im_bytes, 'image/png')
        ims["back"] = ("im_2.png", im_bytes, 'image/png')
        ims["left"] = ("im_3.png", im_bytes, 'image/png')
        ims["right"] = ("im_4.png", im_bytes, 'image/png')

        res = requests.post(self.ip_address, files=ims, data={"session_id": session_id})
        res_json = res.json() 
        self.result_canvas.render_result(res_json)

        # write image and data.json into gallery
        os.makedirs(f"{os.path.dirname(__file__)}/sessions/gallery/{session_id}", exist_ok=True)
        with open(f"{os.path.dirname(__file__)}/sessions/gallery/{session_id}/data.json", "w") as file:
            file.write(json.dumps(res_json, indent=4))
        cv2.imwrite(f"{os.path.dirname(__file__)}/sessions/gallery/{session_id}/im.png", frame)
        cv2.imwrite(f"{os.path.dirname(__file__)}/sessions/gallery/{session_id}/result.png", frame)
        self.left_canvas.stop_(session_id, res_json, frame)
        self.open_panel(right_canvas="result")
                                                                                                                                                                                                                                                                                                                                                                                                                                                        

    def on_configure(self, event):
        self.canvas.itemconfigure(self.left_window, height=event.height - 75)
        self.canvas.itemconfigure(self.right_window, height=event.height - 75)

        if not self.panel_open:
            self.left_width = event.width
            self.canvas.itemconfigure(self.left_window, width=self.left_width)

    def render_text(self):
        self.canvas.create_text(50, 785, anchor="nw", text="Automatically Idenfication",
                                fill="#FFFFFF", font=("Mulish Bold", 12, "bold"))
    
    def create_button(self):
        self.capture_icon = ImageTk.PhotoImage(Image.open("./assets/capture_icon.png").resize((50,50)))
        self.capture_icon_button = self.canvas.create_image(570, 792, image=self.capture_icon)
        self.canvas.tag_bind(
            self.capture_icon_button,
            "<Button-1>",
            lambda e: self.get_results()  # Pass the event as 'e'
        )

        self.upload_icon = ImageTk.PhotoImage(Image.open("./assets/upload_icon.png").resize((50,50)))
        self.upload_icon_button = self.canvas.create_image(640, 792, image=self.upload_icon)
        self.canvas.tag_bind(
            self.upload_icon_button,
            "<Button-1>",
            lambda e: self.open_panel(right_canvas="result")
        )

        self.reload_icon = ImageTk.PhotoImage(Image.open("./assets/reload_icon.png").resize((50,50)))
        self.reload_icon_button = self.canvas.create_image(710, 792, image=self.reload_icon)
        self.canvas.tag_bind(
            self.reload_icon_button,
            "<Button-1>",
            lambda e: self.open_panel(right_canvas="result")
        )

        self.result_icon = ImageTk.PhotoImage(Image.open("./assets/result_icon.png").resize((50,50)))
        self.result_icon_button = self.canvas.create_image(1150, 792, image=self.result_icon)
        self.canvas.tag_bind(
            self.result_icon_button,
            "<Button-1>",
            lambda e: self.open_panel(right_canvas="result")
        )

        self.session_icon = ImageTk.PhotoImage(Image.open("./assets/session_icon.png").resize((50,50)))
        self.session_icon_button = self.canvas.create_image(1220, 792, image=self.session_icon)
        self.canvas.tag_bind(
            self.session_icon_button,
            "<Button-1>",
            lambda e: self.open_panel(right_canvas="session")
        )

        self.auto_toggle_canvas = ToggleButton(self.canvas, width=45, height=30, command=self.test)
        self.auto_toggle_window = self.canvas.create_window(260, 780, anchor="nw",
                                                            window=self.auto_toggle_canvas,
                                                            width=45, height=30)
        
        self.result_canvas.asign_button(self.close_panel)
        self.session_canvas.asign_button(self.close_panel)

    def test(self, event="Nooo"):
        print("ok")

    def open_panel(self, right_canvas):
        if right_canvas == "result":
            new_canvas = self.result_canvas
        elif right_canvas == "session":
            new_canvas = self.session_canvas
        
        if not hasattr(self, "right_window") or self.right_window is None:
            self.right_window = self.canvas.create_window(
                self.width, 0, anchor="nw", window=new_canvas, width=0, height=self.height - 75
            )
        else:
            self.canvas.itemconfigure(self.right_window, window=new_canvas)
        # No trailing colon here
        self.animate_panel_open()

    
    def close_panel(self):
        self.left_canvas.start_()
        step = 40
        if self.right_width > 0:
            self.right_width -= step
            if self.right_width < 0:
                self.right_width = 0
            self.canvas.itemconfigure(self.right_window, width=self.right_width)
            self.left_width = self.canvas.winfo_width() - self.right_width
            self.canvas.itemconfigure(self.left_window, width = self.left_width)
            self.canvas.coords(self.right_window, self.left_width, 0)
            self.after(5, self.close_panel)
        
    def animate_panel_open(self):
        target_width = 429
        step = 90

        if self.right_width < target_width:
            self.right_width += step
            if self.right_width > target_width:
                self.right_width = target_width
            self.canvas.itemconfigure(self.right_window, width=self.right_width)
            self.left_width = self.canvas.winfo_width() - self.right_width
            self.canvas.itemconfigure(self.left_window, width = self.left_width)
            self.canvas.coords(self.right_window, self.left_width, 0)
            self.after(10, self.animate_panel_open)


if __name__ == "__main__":
    app = App()
    app.mainloop()

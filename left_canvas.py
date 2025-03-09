import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np

class LeftCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.camera_type = "0"
        if self.camera_type == "0":
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture('rtsp://admin:DVYMYI@10.10.126.122/camera/h264/ch1/main/av_stream')

        self.update_video()

    def get_capture(self):

        def draw_rounded_rectangle(img, pt1, pt2, color, thickness, radius):

            x1, y1 = pt1
            x2, y2 = pt2

            cv2.line(img, (x1+radius, y1), (x2-radius, y1), color, thickness)
            cv2.line(img, (x1+radius, y2), (x2-radius, y2), color, thickness)
            cv2.line(img, (x1, y1+radius), (x1, y2-radius), color, thickness)
            cv2.line(img, (x2, y1+radius), (x2, y2-radius), color, thickness)

            cv2.ellipse(img, (x1+radius, y1+radius), (radius, radius), 0, 180, 270, color, thickness)
            cv2.ellipse(img, (x2-radius, y1+radius), (radius, radius), 0, 270, 360, color, thickness)
            cv2.ellipse(img, (x1+radius, y2-radius), (radius, radius), 0, 90, 180, color, thickness)
            cv2.ellipse(img, (x2-radius, y2-radius), (radius, radius), 0, 0, 90, color, thickness)

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            h, w, _ = frame.shape
            frame = cv2.resize(frame, (w*2, h*2))
            
            blurred = cv2.GaussianBlur(frame, (31, 31), 20)
            blurred = cv2.addWeighted(blurred, 1.0, np.zeros(blurred.shape, blurred.dtype), 0, -100)

            h, w, _ = frame.shape

            focus_w, focus_h = int(640*1.2), int(480*1.2)
            x1 = int(w // 2 - focus_w // 2)
            y1 = int(h // 2 - focus_h // 2)
            x2 = int(x1 + focus_w)
            y2 = int(y1 + focus_h)

            blurred[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

            border_color = (100, 100, 100)   
            border_thickness = 5           
            radius = 40                  
            draw_rounded_rectangle(blurred, (x1, y1), (x2, y2), border_color, border_thickness, radius)

            return blurred
        return None


    
    def update_video(self):
        frame = self.get_capture()
        
        if frame is not None:
            img = Image.fromarray(frame)
            self.imgtk = ImageTk.PhotoImage(img)
            center_x = self.winfo_width() // 2
            center_y = self.winfo_height() // 2
            self.create_image(center_x, center_y, image=self.imgtk, anchor="center")
        
        # Draw the text AFTER the image so it is on top.
        self.create_text(center_x-185, center_y+320, anchor="nw", 
                        text="Please stay in the center of the frame and click take photo",
                        fill="#FFFFFF", font=("Mulish", 12))
        
        self.after(10, self.update_video)



# Demo sử dụng
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1280x960")
    left_canvas = LeftCanvas(root, bg="white")
    left_canvas.pack(fill="both", expand=True)
    root.mainloop()

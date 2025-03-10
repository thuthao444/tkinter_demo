import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np
from tkinter import messagebox, filedialog

class LeftCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.is_uploading_images = False
        self.camera_type = "1"
        if self.camera_type == "0":
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture('rtsp://admin:DVYMYI@192.168.1.4/camera/h264/ch1/main/av_stream')

        self.session_id = None
        self.update_video()

    def get_capture(self, is_upload=False):

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
        if is_upload is False:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (1320, 832-75))
                
                # blurred = cv2.GaussianBlur(frame, (31, 31), 20)
                blurred = cv2.addWeighted(frame, 1.0, np.zeros(frame.shape, frame.dtype), 0, -200)

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

                return blurred, blurred[y1:y2, x1:x2], x1, x2, y1, y2
        else:
            filetypes = [("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
            im_path = filedialog.askopenfilename(title="Choose Image", filetypes=filetypes)
            frame = cv2.imread(im_path)
            if frame is not None:
                # Chuyển sang RGB và resize khung hình
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bg = cv2.resize(frame, (1320, 832-75))
                
                h, w, _ = bg.shape

                focus_w, focus_h = int(640*1.2), int(480*1.2)
                x1 = int(w // 2 - focus_w // 2)
                y1 = int(h // 2 - focus_h // 2)
                x2 = int(x1 + focus_w)
                y2 = int(y1 + focus_h)
                
                inner_roi = cv2.resize(frame, (x2-x1, y2-y1))                
                background = cv2.addWeighted(bg, 1.0, np.zeros(bg.shape, bg.dtype), 0, -200)
                
                background[y1:y2, x1:x2] = inner_roi
                
                # Vẽ viền bo tròn quanh ảnh trong
                border_color = (100, 100, 100)
                border_thickness = 5
                radius = 40
                draw_rounded_rectangle(background, (x1, y1), (x2, y2), border_color, border_thickness, radius)

                return background, inner_roi, x1, x2, y1, y2
        return None


    
    def update_video(self):
        # Xóa tất cả các đối tượng trên canvas để tránh chồng hình
        self.delete("all")
        
        frame, _, x1, x2, y1, y2 = self.get_capture()
        center_x = self.winfo_width() // 2
        center_y = self.winfo_height() // 2
        print("center_x, center_y", center_x, center_y)
        if frame is not None:
            img_ = Image.fromarray(frame)
            
            if not self.is_uploading_images:
                self.imgtk = ImageTk.PhotoImage(img_)
                self.create_image(center_x, center_y, image=self.imgtk, anchor="center")
            else:
                img = cv2.imread(f"./sessions/gallery/{self.session_id}/result.png")
                frame[y1:y2, x1:x2] = img
                self.imgtk = ImageTk.PhotoImage(Image.fromarray(frame))
                self.create_image(center_x, center_y, image=self.imgtk, anchor="center")
            
        self.create_text(center_x-185, center_y+320, anchor="nw", 
                        text="Please stay in the center of the frame and click take photo",
                        fill="#FFFFFF", font=("Mulish", 12))
        
        self.loop = self.after(20, self.update_video)

    def stop_(self, session_id, res_json, frame):
        self.session_id = session_id
        print("res_json:", res_json)
        def draw_bounding_box(label, x1, y1, x2, y2):
            if label == "Không tìm thấy trong cơ sở dữ liệu":
                label = "Khong tim thay trong CSDL"
            im = cv2.imread(f"./sessions/gallery/{session_id}/result.png")
            im_result = cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if label is not None:
                im_result = cv2.putText(im_result, f"{label}", (x1,y1-20), cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5, (255,0,0), 2, cv2.LINE_AA)
            cv2.imwrite(f"./sessions/gallery/{session_id}/result.png", im_result)
        
        ######## Faceid #######
        if "face_id" in res_json:
            draw_bounding_box(res_json["face_id"]["im_name"], res_json["face_id"]["x"], res_json["face_id"]["y"],
                            res_json["face_id"]["x"] + res_json["face_id"]["w"], 
                            res_json["face_id"]["y"] + res_json["face_id"]["h"])

        ######## Glasses #######
        if len(res_json["glasses"]) > 0:
            draw_bounding_box(None, *map(int, res_json["glasses"][0]["bounding_box"]))

        ######## Nametag ########
        if len(res_json["nametag"]) > 0:
            draw_bounding_box(None, *map(int, [res_json["nametag"][0]["x1"], res_json["nametag"][0]["y1"],res_json["nametag"][0]["x2"], res_json["nametag"][0]["y2"]]))

        ######## Tie ########
        if len(res_json["tie"]) > 0:
            draw_bounding_box(None, *map(int, [res_json["tie"][0]["x1"], res_json["tie"][0]["y1"],res_json["tie"][0]["x2"], res_json["tie"][0]["y2"]]))

        self.is_uploading_images = True
    def start_(self):
        self.is_uploading_images = False

# Demo sử dụng
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1280x960")
    left_canvas = LeftCanvas(root, bg="white")
    left_canvas.pack(fill="both", expand=True)
    root.mainloop()

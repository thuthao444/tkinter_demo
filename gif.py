import tkinter as tk
from PIL import Image, ImageTk

class GifCanvas(tk.Canvas):
    def __init__(self, parent, delay=100, size=(60,60), **kwargs):
        # Set canvas background and border options.
        kwargs.setdefault("bg", parent["bg"])  # match parent's bg for "transparency"
        kwargs.setdefault("highlightthickness", 2)
        kwargs.setdefault("highlightbackground", "black")
        super().__init__(parent, **kwargs)
        self.delay = delay  # delay between frames in milliseconds
        self.frames = []
        self.frame_index = 0
        self.size = size

        pil_image = Image.open("./gif.gif")
        try:
            while True:
                # Copy current frame, convert to RGBA (to support alpha),
                # and resize to the desired dimensions.
                frame = pil_image.copy().convert("RGBA").resize(self.size)
                # Process each pixel: if nearly white, set its alpha to 0 (transparent).
                new_data = []
                for item in frame.getdata():
                    if item[0] > 240 and item[1] > 240 and item[2] > 240:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                frame.putdata(new_data)
                photo = ImageTk.PhotoImage(frame)
                self.frames.append(photo)
                pil_image.seek(len(self.frames))  # move to next frame
        except EOFError:
            pass

        # Display the first frame on the canvas.
        self.canvas_image = self.create_image(0, 0, image=self.frames[0], anchor="nw")

    def animate(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.itemconfig(self.canvas_image, image=self.frames[self.frame_index])
        self.loop = self.after(self.delay, self.animate)

    def stop_animation(self):
        if hasattr(self, 'loop'):
            self.after_cancel(self.loop)

if __name__ == "__main__":
    root = tk.Tk()
    # Set a background color for the root so that transparent areas are visible.
    root.configure(bg="gray")
    root.geometry("500x500")
    
    # Create a GifCanvas with the desired dimensions.
    gif_canvas = GifCanvas(root, gif_path="./gif.gif", delay=100, size=(60, 60), width=60, height=60)
    gif_canvas.pack(pady=20)
    
    gif_canvas.animate()  # Start the animation
    
    root.mainloop()

import tkinter as tk

class ToggleButton(tk.Canvas):
    def __init__(self, master, command=None, fg='white', bg='yellow', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(background="black", width=100, height=50, borderwidth=0, highlightthickness=0)
        self.command = command
        self.fg = fg
        self.bg = bg
        self.state = False
        
        init_bg = "gray" if not self.state else self.bg
        
        self.left_arc = self.create_arc(0, 0, 0, 0, start=90, extent=180, fill=init_bg, outline='')
        self.right_arc = self.create_arc(0, 0, 0, 0, start=-90, extent=180, fill=init_bg, outline='')
        self.center_rect = self.create_rectangle(0, 0, 0, 0, fill=init_bg, outline='')
        self.btn = self.create_oval(0, 0, 0, 0, fill=self.fg, outline='')

        self.bind('<Configure>', self._resize)
        self.bind('<Button>', command, add='+')
        self.bind('<Button-1>', self._animate)
    
    def _resize(self, event):
        padding = 5
        height = event.height
        width = event.width
        arc_diameter = height - 2 * padding

        self.coords(self.left_arc, padding, padding, padding + arc_diameter, padding + arc_diameter)
        self.coords(self.right_arc, width - padding - arc_diameter, padding, width - padding, padding + arc_diameter)
        self.coords(self.center_rect, padding + arc_diameter / 2, padding,
                    width - padding - arc_diameter / 2, padding + arc_diameter)
        
        btn_x = width - padding - arc_diameter if self.state else padding
        self.coords(self.btn, btn_x, padding, btn_x + arc_diameter, padding + arc_diameter)
    
    def _animate(self, event):
        self.state = not self.state
        new_bg = self.bg if self.state else "gray"
        self.itemconfig(self.left_arc, fill=new_bg)
        self.itemconfig(self.right_arc, fill=new_bg)
        self.itemconfig(self.center_rect, fill=new_bg)
        self._animate_knob()
        if self.command:
            self.command()
    
    def _animate_knob(self):
        padding = 5
        width = self.winfo_width()
        height = self.winfo_height()
        arc_diameter = height - 2 * padding
        target_x = width - padding - arc_diameter if self.state else padding

        current_coords = self.coords(self.btn)
        current_x = current_coords[0]
        if abs(current_x - target_x) < 2:
            self.moveto(self.btn, target_x, padding)
            return

        step = 2 if target_x > current_x else -2
        new_x = current_x + step
        self.moveto(self.btn, new_x, padding)
        self.after(10, self._animate_knob)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("300x150")
    
    def on_toggle():
        print("Toggle state:", toggle.state)
    
    toggle = ToggleButton(root, command=on_toggle, fg="white", bg="yellow")
    toggle.pack(pady=30)
    
    root.mainloop()

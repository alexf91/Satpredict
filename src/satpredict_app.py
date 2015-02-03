import tkinter as tk

class SatPredictApp(tk.Tk):
    
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        
        self.title('SatPredict by OE5TKM')
        self.resizable(False, False)
        self.geometry('320x240')
        
        self.polar = PolarMap(self)
        self.polar.pack(fill=tk.BOTH)


class PolarMap(tk.Frame):    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        
        self.map = tk.Canvas(self, width=240, height=240, bg='white')
        self.map.grid(column=0)
    
        self.draw_outline()
    
    
    def draw_outline(self):
        circle_color = '#808080'
        circle_width = 1
        axis_color = '#808080'
        axis_width = 1

        self.map.create_oval(0,0,240,240, outline=circle_color, width=circle_width)
        self.map.create_oval(40, 40, 200, 200, outline=circle_color, width=circle_width)
        self.map.create_oval(80, 80, 160, 160, outline=circle_color, width=circle_width)
        self.map.create_line(120, 0, 120, 240, fill=axis_color, width=axis_width)
        self.map.create_line(0, 120, 240, 120, fill=axis_color, width=axis_width)
    
        self.map.create_text(130, 10, text='N')
        self.map.create_text(130, 230, text='S')
        self.map.create_text(10, 112, text='W')
        self.map.create_text(230, 112, text='E')
        
        
        
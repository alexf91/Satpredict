import tkinter as tk

class SatPredictApp(tk.Tk):
    
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        
        self.polar = PolarMap(self)
        self.polar.focus()
        
        menubar = tk.Menu(self)
        
        track_menu = tk.Menu(menubar, tearoff=0)
        track_menu.add_command(label='Satellite')
        track_menu.add_command(label='Transponder')
        menubar.add_cascade(label='Tracking', menu=track_menu)

        self.config(menu=menubar)
        self.grid()
        
    

class PolarMap(tk.Frame):    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        
        self.map = tk.Canvas(width=210, height=210, bg='white')
        self.draw_outline()
        self.map.focus()
        self.map.grid()
    
    
    def draw_outline(self):
        circle_color = '#808080'
        circle_width = 1
        axis_color = '#808080'
        axis_width = 1
        size_x = 210
        size_y = 210
        
        for i in range(0, 3):
            self.map.create_oval(i/6.0*size_x,i/6.0*size_y,(6-i)/6.0*size_x,(6-i)/6.0*size_y, outline=circle_color, width=circle_width)

        self.map.create_line(size_x/2, 0, size_x/2, size_y, fill=axis_color, width=axis_width)
        self.map.create_line(0, size_y/2, size_x, size_y/2, fill=axis_color, width=axis_width)
    
        self.map.create_text(size_x/2 + 7, 10, text='N')
        self.map.create_text(size_x/2 + 7, size_y - 10, text='S')
        self.map.create_text(10, size_y/2 -7, text='W')
        self.map.create_text(size_x-10, size_y/2 -7, text='E')
        
        
def key_cb(event):
    print('event')     


class SatPredictState(object):
    active_sat = None
    db = None
    location = None
    
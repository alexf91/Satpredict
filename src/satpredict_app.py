import tkinter as tk
import os
import subprocess

class SatPredictApp(tk.Tk):
    
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        
        self.state = SatPredictState()
        
        self.initialize_gui()

    
    def initialize_gui(self):
        self.polar = PolarMap(self)
        self.polar.focus()
        
        menubar = tk.Menu(self)
        
        track_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        track_menu.add_command(label='Satellite Info')
        track_menu.add_separator()
        
        self.sat_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.satellite_cb)
        track_menu.add_cascade(label='Satellite', menu=self.sat_menu)
        
        
        self.trsp_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.trsp_cb)
        self.trsp_menu.add_command(label='FM')
        track_menu.add_cascade(label='Transponder', menu=self.trsp_menu)
        
        self.pos_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.pos_cb)
        track_menu.add_cascade(label='Position', menu=self.pos_menu)
        
        menubar.add_cascade(label='Tracking', menu=track_menu)
        
        
        power_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        power_menu.add_command(label='Exit', command=lambda: self.power_cb('EXIT'))
        power_menu.add_command(label='Reboot', command=lambda: self.power_cb('REBOOT'))
        power_menu.add_command(label='Shutdown', command=lambda: self.power_cb('SHUTDOWN'))
        menubar.add_cascade(label='Power', menu=power_menu)
        
        self.menubar = menubar
        
        
        
        self.config(menu=menubar)
        self.grid()
        
        self.bind('<Escape>', self.escape_cb)
        self.bind('<Return>', self.return_cb)            
    
    def escape_cb(self, event):
        self.event_generate('<F10>')

    def return_cb(self, event):
        print('return_cb()')
    
    def satellite_cb(self):
        print('satellite_cb()')
        self.sat_menu.delete(0, tk.END)
        for entry in ['SO-50', 'AO-7', 'FUNCUBE']:
            self.sat_menu.add_command(label=entry)
    
    def trsp_cb(self):
        print('trsp_cb()')
    
    def pos_cb(self):
        print('pos_cb()')
    
    def power_cb(self, cmd):
        if 'RASPBERRY_PI' in os.environ:
            if cmd == 'SHUTDOWN':
                subprocess.call(['sudo', 'shutdown', '-h', 'now'])
            elif cmd == 'REBOOT':
                subprocess.call(['sudo', 'reboot'])
            elif cmd == 'EXIT':
                exit()
        else:
            exit()
        
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


class SatPredictState(object):
    active_sat = None
    db = None
    location = None
    
    
import tkinter as tk
import os
import subprocess
import configuration
import database
import copy

class SatPredictApp(tk.Tk):
    
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        
        self.cfg = configuration.Configuration(os.path.expanduser('~/.satpredict/amateur.conf'))
        self.db = database.Database()
        self.active_sat = None
        self.active_trsp = None
        
        self.initialize_gui()

    
    def initialize_gui(self):
        self.polar = PolarMap(self)
        self.polar.focus()
        
        menubar = tk.Menu(self, activebackground='#F00000')
        
        track_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        track_menu.add_command(label='Satellite Info')
        track_menu.add_separator()
        
        self.sat_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.satellite_dir_cb)
        track_menu.add_cascade(label='Satellite', menu=self.sat_menu)
        
        
        self.trsp_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.transponder_dir_cb)
        self.trsp_menu.add_command(label='FM')
        track_menu.add_cascade(label='Transponder', menu=self.trsp_menu)
        
        self.loc_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.location_dir_cb)
        track_menu.add_cascade(label='Location', menu=self.loc_menu)
        
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
    
    
    def escape_cb(self, event):
        self.event_generate('<F10>')
    
    
    def satellite_dir_cb(self):
        self.sat_menu.delete(0, tk.END)
        
        for sat in self.db.query(self.cfg.satellites):            
            if sat.nick != '':
                entry = '{} ({})'.format(sat.name, sat.nick)
            else:
                entry = sat.name
                
            def make_lambda(sat):
                return lambda: self.satellite_select_cb(sat)
            self.sat_menu.add_command(label=entry, command=make_lambda(sat))

            
    
    def satellite_select_cb(self, sat):
        self.active_sat = sat

    
    def transponder_dir_cb(self):
        self.trsp_menu.delete(0, tk.END)
        
        if not self.active_sat:
            return
        
        for trsp in self.active_sat.transponders:
            def make_lambda(trsp):
                return lambda: self.transponder_select_cb(trsp)
            
            self.trsp_menu.add_command(label=trsp.name, command=make_lambda(trsp))
            
            
    
    def transponder_select_cb(self, trsp):
        self.active_trsp = trsp
    
    
    def location_dir_cb(self):
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
        
        self.map = tk.Canvas(self, width=210, height=210, bg='white')
        self.draw_outline()
        self.map.grid(column=0, row=0, columnspan=8, rowspan=8)
        
        self.sat_name = tk.StringVar(value='')
        self.trsp_name = tk.StringVar(value='')
        self.up_sat = tk.StringVar(value='')
        self.down_sat = tk.StringVar(value='')
        self.up_doppler = tk.StringVar(value='')
        self.down_doppler = tk.StringVar(value='')
        
        font = lambda s: ('Monospace', s)
        color = 'black'
        
        self.label = tk.Label(self, textvar = self.sat_name, fg=color, font=font(9))
        self.label.grid(column=10, row=0)
        self.label = tk.Label(self, textvar = self.trsp_name, fg=color, font=font(9))
        self.label.grid(column=10, row=1)
        
        self.label = tk.Label(self, text='⇧', fg=color, font=font(16))
        self.label.grid(column=9, row=2, sticky=tk.W)
        
        self.label = tk.Label(self, text='⇩', fg=color, font=font(16))
        self.label.grid(column=9, row=3, sticky=tk.W) 
        
        self.label = tk.Label(self, textvar=self.up_sat, fg=color, font=font(16))
        self.label.grid(column=10, row=2)
        
        self.label = tk.Label(self, textvar=self.down_sat, fg=color, font=font(16))
        self.label.grid(column=10, row=3)
        
        self.label = tk.Label(self, text='Doppler:', fg=color, font=font(10))
        self.label.grid(column=10, row=4)
        
        self.label = tk.Label(self, text='⇧', fg=color, font=font(16))
        self.label.grid(column=9, row=5, sticky=tk.W)
        
        self.label = tk.Label(self, text='⇩', fg=color, font=font(16))
        self.label.grid(column=9, row=6, sticky=tk.W) 
        
        self.label = tk.Label(self, textvar=self.up_doppler, fg=color, font=font(16))
        self.label.grid(column=10, row=5)
        
        self.label = tk.Label(self, textvar=self.down_doppler, fg=color, font=font(16))
        self.label.grid(column=10, row=6)
        
        
        self.grid()
    
    
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

    
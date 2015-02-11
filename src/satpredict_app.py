import tkinter as tk
from tkinter import ttk
import os
import subprocess
import fileaccess
import copy
import time
import math
import ephem
import sensors
import numpy
import sys
import collections
import rigctl

class SatPredictApp(tk.Tk):
    
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        
        self.cfg = fileaccess.Configuration(os.path.expanduser('~/.satpredict/default.conf'))
        self.db = fileaccess.Database()
        
        self.active_location = self.cfg.locations[0]
        self.compass = None
        
        self.up_freq = None    # Uplink frequency without doppler shift
        self.down_freq = None  # Downlink frequency without doppler shift
        self.up_doppler_freq = None
        self.down_doppler_freq = None
        
        self.rigctld = rigctl.Daemon('rigctld -m120 -r/dev/ttyUSB0 -s38400')
        self.rig = None

        self.ptt_enabled = False
        
        self.initialize_gui()
        
        self.active_sat = self.db.query(self.cfg.satellites)[0]
        if len(self.active_sat.transponders) > 0:
            self.select_transponder(self.active_sat.transponders[0])
        else:
            self.select_transponder(None)
        
        self.display_timer_interval = 250
        self.display_timer()
        
        self.cat_timer_interval = 1000
        self.cat_timer()
        
        
    def initialize_gui(self):
        
        self.frames = { }
        self.active_frame = None
        
        polar = PolarMap(self)
        self.frames['polar'] = polar
        
        polar.bind('<Up>', lambda e: self.frequency_changed_cb('UP'))
        polar.bind('<Down>', lambda e: self.frequency_changed_cb('DOWN'))
        polar.bind('<KeyPress-BackSpace>', lambda e: self.ptt_cb(True))
        polar.bind('<KeyRelease-BackSpace>', lambda e: self.ptt_cb(False))
        
        polar.grid(column=0, row=0)
        polar.focus()
        
        
        next_passes = NextPasses(self)
        self.frames['next'] = next_passes
        next_passes.grid(column=0, row=0, sticky=tk.NW + tk.SE)
        
                
        
        menubar = tk.Menu(self, activebackground='#F00000')
        
        track_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        
        self.sat_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.satellite_dir_cb)
        track_menu.add_cascade(label='Satellite', menu=self.sat_menu)
        
        
        self.trsp_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.transponder_dir_cb)
        self.trsp_menu.add_command(label='FM')
        track_menu.add_cascade(label='Transponder', menu=self.trsp_menu)
        
        self.loc_menu = tk.Menu(track_menu, activebackground='#F00000', tearoff=0, postcommand=self.location_dir_cb)
        track_menu.add_cascade(label='Location', menu=self.loc_menu)
        
        menubar.add_cascade(label='Tracking', menu=track_menu)
        
        
        self.device_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000', postcommand=self.devices_dir_cb)
        self.device_menu.add_command(label='Enable CAT', command=self.cat_cb)
        
        state = tk.ACTIVE if 'RASPBERRY_PI' in os.environ else tk.DISABLED 
        self.device_menu.add_command(label='Enable Compass', command=self.compass_cb, state=state)
        menubar.add_cascade(label='Devices', menu=self.device_menu)
        
        self.view_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        self.view_menu.add_command(label='Polar Map', command=lambda: self.set_active_layer('polar'))
        self.view_menu.add_command(label='Next Events', command=lambda: self.set_active_layer('next'))
        menubar.add_cascade(label='View', menu=self.view_menu)
        
        self.settings_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        self.settings_menu.add_command(label='Update TLE', command=self.update_tle_cb)
        interval_menu_disp = tk.Menu(menubar, tearoff=0, activebackground='#F00000', postcommand=lambda: self.interval_cb('DISPLAY', interval_menu_disp))
        interval_menu_cat = tk.Menu(menubar, tearoff=0, activebackground='#F00000', postcommand=lambda: self.interval_cb('CAT', interval_menu_cat))
        self.settings_menu.add_cascade(label='Display Interval', menu=interval_menu_disp)
        self.settings_menu.add_cascade(label='CAT Interval', menu=interval_menu_cat)
        menubar.add_cascade(label='Settings', menu=self.settings_menu)
        
        power_menu = tk.Menu(menubar, tearoff=0, activebackground='#F00000')
        power_menu.add_command(label='Exit', command=lambda: self.power_cb('EXIT'))
        power_menu.add_command(label='Reboot', command=lambda: self.power_cb('REBOOT'))
        power_menu.add_command(label='Shutdown', command=lambda: self.power_cb('SHUTDOWN'))
        menubar.add_cascade(label='Power', menu=power_menu)
        
        self.menubar = menubar
        
        self.config(menu=menubar)
        self.grid()
        
        self.bind('<Escape>', lambda e: self.event_generate('<F10>'))
        
        self.set_active_layer('polar')
        
    
    def display_timer(self):
        if self.ptt_enabled: # Fix severe interference of TFT display (at least for transmitting)
            self.after(self.display_timer_interval, self.display_timer)
            return
        
        #Display UTC on screen
        t = time.strftime('%H:%M:%S')
        self.frames['polar'].time.set(t)
        
        #Display satellite name
        if self.active_sat.nick != '':
            name = self.active_sat.nick
        else:
            name = self.active_sat.name
        
        self.frames['polar'].sat_name.set(name)
        
        #display transponder name
        if self.active_trsp:
            name = self.active_trsp.name
        else:
            name = 'No Transponder'
        
        self.frames['polar'].trsp_name.set(name)
        
        body = self.calculate_sat_position()
        
        az = math.degrees(body.az)
        el = math.degrees(body.alt)
        self.frames['polar'].update_satpos(az, el)
        
        if self.compass:
            try:
                deg = self.compass.angles()
                self.frames['polar'].update_antpos(deg[0], deg[2])
            except:
                self.compass = None
        else:
            self.frames['polar'].update_antpos(0, 90)
        
        self.calculate_doppler_shift()
        
        self.frames['polar'].print_trsp(self.up_freq, self.down_freq, self.up_doppler_freq, self.down_doppler_freq)
            
        #periodically check for running rigctld and if 
        tty = os.path.exists('/dev/ttyUSB0')
        if (self.rigctld.running() and tty is False) or not self.rigctld.running():
            self.rigctld.stop()
            self.rig = None
                
        #restart timer for next event
        self.after(self.display_timer_interval, self.display_timer)
    
    
    def cat_timer(self):
        
        if self.ptt_enabled == False and self.rig:
            self.rig.set_freq(self.down_doppler_freq)
        
        self.after(self.cat_timer_interval, self.cat_timer)
    
    
    def cat_cb(self):
        if self.rig is None:
            if os.path.exists('/dev/ttyUSB0'):
                self.rigctld.start()
                time.sleep(0.05)
                self.rig = rigctl.Rig()
                
        else:
            self.rigctld.stop()
            self.rig = None

    
    def set_active_layer(self, name):
        self.frames[name].lift(self.active_frame)
        for f in self.frames.values():
            f.grid_remove()
            
        self.active_frame = self.frames[name]
        self.active_frame.grid()
    
    
    def calculate_sat_position(self):
        #Calcualte position of current satellite
        lon = self.__loc_2_dms(self.active_location.long)
        lat = self.__loc_2_dms(self.active_location.lat)
        obs = ephem.Observer()
        obs.lon = '{}:{}:{}'.format(lon[0], lon[1], lon[2])
        obs.lat = '{}:{}:{}'.format(lat[0], lat[1], lat[2])
        obs.elevation = self.active_location.elev
        obs.pressure = 0
        
        body = ephem.readtle(self.active_sat.line1, self.active_sat.line2, self.active_sat.line3)
        body.compute(obs)
        
        return body
    
    def calculate_doppler_shift(self):
        body = self.calculate_sat_position()
        vel = -body.range_velocity * 1.055 # bug in xephem, ugly "fix"
        
        c = 299792458
        shift = numpy.sqrt((c + vel) / (c - vel))
        if self.up_freq:
            self.up_doppler_freq = round(self.up_freq / shift)
        else:
            self.up_doppler_freq = None
        
        if self.down_freq:
            self.down_doppler_freq = round(self.down_freq * shift)
        else:
            self.down_doppler_freq = None
        
    
    def interval_cb(self, timer, menu):
        
        def cb(timer, i):
            if timer == 'DISPLAY':
                self.display_timer_interval = i
            elif timer == 'CAT':
                self.cat_timer_interval = i
        
        def make_lambda(timer, interval):
            return lambda: cb(timer, interval)
        
        menu.delete(0, tk.END)
        if timer == 'DISPLAY':
            for i in [250, 500, 750, 1000, 2500, 5000]:
                menu.add_command(label='{}ms'.format(i), command=make_lambda(timer, i))
        elif timer == 'CAT':
            for i in [500, 1000, 1500, 2000, 2500, 3000, 5000]:
                menu.add_command(label='{}ms'.format(i), command=make_lambda(timer, i))
    
    
    def select_transponder(self, trsp):
        self.active_trsp = trsp;
        if trsp is None:
            self.frames['polar'].up_sat.set('')
            self.frames['polar'].down_sat.set('')
            
        if isinstance(trsp.up, collections.Sequence):
            if trsp.invert:
                self.up_freq = trsp.up[1]
            else:
                self.up_freq = trsp.up[0]
                
        else:
            self.up_freq = trsp.up
        
        
        if isinstance(trsp.down, collections.Sequence):
            self.down_freq = trsp.down[0]
        else:
            self.down_freq = trsp.down
        
        self.calculate_doppler_shift()
        self.frames['polar'].print_trsp(self.up_freq, self.down_freq, self.up_doppler_freq, self.down_doppler_freq)
        
        if self.rig and trsp:
            self.adjust_frequency(up=True)
            self.adjust_frequency(up=False)
    
    
    
    def adjust_frequency(self, up=False):
        mode = None
        if self.active_trsp.mode == fileaccess.Transponder.Mode.LINEAR:
            mode = rigctl.Rig.Mode.LSB if up else rigctl.Rig.Mode.USB
        elif self.active_trsp.mode == fileaccess.Transponder.Mode.FM:
            mode = rigctl.Rig.Mode.FM
        elif self.active_trsp.mode == fileaccess.Transponder.Mode.CW:
            mode = rigctl.Rig.Mode.CW
        elif self.active_trsp.mode == fileaccess.Transponder.Mode.DIGI:
            mode = rigctl.Rig.Mode.USB
        
        assert mode is not None
        
        if up:
            self.rig.set_freq(self.up_doppler_freq)
            self.rig.set_mode(mode)
        else:
            self.rig.set_freq(self.down_doppler_freq)
            self.rig.set_mode(mode)
        
        
    
    def update_tle_cb(self):
        try:
            self.db.update()
        except:
            text = sys.exc_info()[0].__name__
            self.error_message(text)
    
    
    def error_message(self, text):
        top = tk.Toplevel(self, bd=2, relief=tk.RAISED)
        top.title('Error')
        
        top.resizable(False, False)
        top.geometry('200x100+60+40')
        
        msg = tk.Message(top, text=text, width=200)
        msg.pack(expand=True)
        
        button = tk.Button(top, text='OK', command=top.destroy, activebackground='#F00000')
        button.pack()
        
        def destroy(e):
            self.focus()
            top.destroy()
        
        top.bind('<Return>', destroy)
        top.focus()
    
    
    def frequency_changed_cb(self, dir):
        inc = 100
        if dir == 'UP':
            self.down_freq += inc
            if self.up_freq:
                if self.active_trsp.invert:
                    self.up_freq -= inc
                else:
                    self.up_freq += inc
        elif dir == 'DOWN':
            self.down_freq -= inc
            if self.up_freq:
                if self.active_trsp.invert:
                    self.up_freq += inc
                else:
                    self.up_freq -= inc
        
        self.calculate_doppler_shift()
        self.frames['polar'].print_trsp(self.up_freq, self.down_freq, self.up_doppler_freq, self.down_doppler_freq)
    
    
    def ptt_cb(self, enable):
        self.ptt_enabled = enable and (self.up_freq is not None) and (self.rig is not None)
        if self.rig:
            if enable and self.up_doppler_freq:
                self.adjust_frequency(up=True)
                self.rig.set_ptt(True)
            else:
                self.rig.set_ptt(False)
                self.after(200, lambda: self.adjust_frequency(up=False))
                
    
    
    def devices_dir_cb(self):
        #CAT
        label = 'Enable CAT' if self.rig == None else 'Disable CAT'
        self.device_menu.entryconfig(0, label=label)
        
        #sensors
        label = 'Enable Compass' if self.compass == None else 'Disable Compass'
        self.device_menu.entryconfig(1, label=label)
    
    
    def compass_cb(self):
        try:
            if self.compass == None:
                coord = (self.active_location.long, self.active_location.lat, self.active_location.elev)
                self.compass = sensors.Compass(coord, sensors.HMC5883L(), sensors.MMA7455())
                self.compass.calibrate()
            else:
                self.compass = None
        except:
            text = sys.exc_info()[0].__name__
            self.error_message(text)
    
    
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
        if len(sat.transponders) > 0:
            self.select_transponder(sat.transponders[0])
        else:
            self.select_transponder(None)



    
    def transponder_dir_cb(self):
        self.trsp_menu.delete(0, tk.END)
        
        if not self.active_sat:
            return
        
        for trsp in self.active_sat.transponders:
            def make_lambda(trsp):
                return lambda: self.select_transponder(trsp)
            
            self.trsp_menu.add_command(label=trsp.name, command=make_lambda(trsp))
            
    
    def location_dir_cb(self):
        self.loc_menu.delete(0, tk.END)
        
        for loc in self.cfg.locations:
            def make_lambda(loc):
                return lambda: self.location_select_cb(loc)
            
            self.loc_menu.add_command(label=loc.name, command=make_lambda(loc))
            
    def location_select_cb(self, loc):
        self.active_location = loc
    
    
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
        
    def __loc_2_dms(self, location):
        d = int(location)
        location = (location % 1) * 60
        min = int(location)
        location = (location % 1) * 60 
        sec = location
        return (d, min, sec)
        
        
class PolarMap(tk.Frame):    
    def __init__(self, parent, filter_coeff=[0.4, 0.3, 0.2, 0.1]):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        
        self.map = tk.Canvas(self, width=210, height=210, bg='white')
        self.draw_outline()
        self.map.grid(column=0, row=0)
        
        self.info = tk.Frame(self, height=210, width=110)
        
        
        self.sat_name = tk.StringVar(value='')
        self.trsp_name = tk.StringVar(value='')
        self.up_sat = tk.StringVar(value='')
        self.down_sat = tk.StringVar(value='')
        self.up_doppler = tk.StringVar(value='')
        self.down_doppler = tk.StringVar(value='')
        self.time = tk.StringVar(value='')
        
        font = lambda s: ('Monospace', s)
        color = 'black'
        
        self.label = tk.Label(self.info, textvar = self.sat_name, fg=color, font=font(8))
        self.label.grid(column=0, row=0, sticky=tk.W, columnspan=2)
        
        self.label = tk.Label(self.info, textvar = self.trsp_name, fg=color, font=font(8))
        self.label.grid(column=0, row=1, sticky=tk.W, columnspan=2)
        
        self.label = tk.Label(self.info, text='⇧', fg=color, font=font(16))
        self.label.grid(column=0, row=2, sticky=tk.W)
        
        self.label = tk.Label(self.info, text='⇩', fg=color, font=font(16))
        self.label.grid(column=0, row=3, sticky=tk.W) 
        
        self.label = tk.Label(self.info, textvar=self.up_sat, fg=color, font=font(8))
        self.label.grid(column=1, row=2, sticky=tk.W)
        
        self.label = tk.Label(self.info, textvar=self.down_sat, fg=color, font=font(8))
        self.label.grid(column=1, row=3, sticky=tk.W)
        
        self.label = tk.Label(self.info, text='Doppler:', fg=color, font=font(8))
        self.label.grid(column=0, row=4, sticky=tk.W, columnspan=2)
        
        self.label = tk.Label(self.info, text='⇧', fg=color, font=font(16))
        self.label.grid(column=0, row=5, sticky=tk.W)
        
        self.label = tk.Label(self.info, text='⇩', fg=color, font=font(16))
        self.label.grid(column=0, row=6, sticky=tk.W) 
        
        self.label = tk.Label(self.info, textvar=self.up_doppler, fg=color, font=font(8))
        self.label.grid(column=1, row=5, sticky=tk.W)
        
        self.label = tk.Label(self.info, textvar=self.down_doppler, fg=color, font=font(8))
        self.label.grid(column=1, row=6, sticky=tk.W)
        
        self.label = tk.Label(self.info, textvar=self.time, fg=color, font=font(8))
        self.label.grid(column=0, row=7, sticky=tk.W, columnspan=2)
        
        self.info.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.info.grid_propagate(False)
        self.grid()
        
        #add dot for satellite tracking
        r = 3
        self.dot_radius = r

        self.sat_dot = self.map.create_oval(105-r, 105-r, 105+r, 105+r, fill='black')
        self.ant_dot = self.map.create_oval(105-r, 105-r, 105+r, 105+r, fill='red')
        
        self.__antpos_filter = numpy.zeros((3, len(filter_coeff)))
        self.__antpos_filter_coeff = numpy.matrix(filter_coeff).getT()
    
    
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
        
    
    def update_satpos(self, az, el):
        self.__update_dotpos(az, el, self.sat_dot, 'black')
    
    
    def update_antpos(self, az, el):
        if el < 0: el = 0
        
        x_vect = numpy.cos(numpy.radians(az))
        y_vect = numpy.sin(numpy.radians(az))
        
        new = numpy.concatenate((numpy.matrix([[x_vect], [y_vect], [el]]), self.__antpos_filter[:, 0:-1]), 1) * self.__antpos_filter_coeff
        self.__antpos_filter = numpy.concatenate((new, self.__antpos_filter[:, 0:-1]), 1)
        az = numpy.degrees(numpy.arctan2(new[1, 0], new[0, 0]))

        self.__update_dotpos(az, new[2, 0], self.ant_dot, 'red')
        
        
    def __update_dotpos(self, az, el, dot, color):
        
        az = -az + 180
        
        #not mathematically correct, but the same as in gpredict
        r_unity = (90 - abs(el)) / 90
        z = math.sin(math.radians(el))
        
        y = round(105 - self.dot_radius + 105 * math.cos(math.radians(az)) * r_unity)
        x = round(105 - self.dot_radius + 105 * math.sin(math.radians(az)) * r_unity)
        
        pos = self.map.coords(dot)

        dx = x - pos[0]
        dy = y - pos[1]
        
        self.map.move(dot, dx, dy)
        if z < 0:
            self.map.itemconfig(dot, fill='', outline='')
        else:
            self.map.itemconfig(dot, fill=color, outline='black')

    def print_trsp(self, up, down, up_doppler, down_doppler):
        up = up / 1000 if up else None
        down = down / 1000 if down else None
        up_doppler = up_doppler / 1000 if up_doppler else None
        down_doppler = down_doppler / 1000 if down_doppler else None
        
        self.up_sat.set('{}'.format(up))
        self.down_sat.set('{}'.format(down))
        self.up_doppler.set('{}'.format(up_doppler))
        self.down_doppler.set('{}'.format(down_doppler))
        

class NextPasses(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tree = ttk.Treeview(self)
        
        self.tree['columns'] = ('time', 'az_in', 'az_out', 'el_max')
        
        self.tree.column('#0', width=100)
        self.tree.heading('#0', text='Satellite')
        
        self.tree.column('time', width=70)
        self.tree.heading('time', text='Time')

        self.tree.column('az_in', width=50, stretch=False)
        self.tree.heading('az_in', text='Az in')
        
        self.tree.column('az_out', width=50, stretch=False)
        self.tree.heading('az_out', text='Az out')
        
        self.tree.column('el_max', width=50, stretch=False)
        self.tree.heading('el_max', text='El')        
        
        self.tree.pack(expand=True)
        
    
    def show(self, satellites):
        pass
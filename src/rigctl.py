
import socket
import enum
import subprocess
import time

class Rig(object):
    
    class Mode(enum.Enum):
        USB = 0
        LSB = 1
        CW = 2
        CQR = 3
        RTTY = 4
        RTTYR = 5
        AM = 6
        FM = 7
        WFM = 8
        AMS = 9
        PKTLSB = 10
        PKTUSB = 11
        PKTFM = 12
        ECSSUSB = 13
        ECSSLSB = 14
        FAX = 15
        SAM = 16
        SAL = 17
        SAH = 18
        DSB = 19
        
    
    def __init__(self, port=4532):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1', port))
        
        
    def command(self, cmd_str):
        self.s.sendall(cmd_str.encode('ascii'))
    
    def set_freq(self, frequency):
        self.command('\\set_freq {}\n'.format(frequency))
    
    def set_mode(self, mode, passband=0):
        self.command('\\set_mode {} {}\n'.format(mode.name, passband))
        
    def set_ptt(self, en):
        self.command('\\set_ptt {}\n'.format(int(en)))
    
    def __del__(self):
        self.s.close()

class Daemon(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.p = None
    
    def running(self):
        if self.p is None:
            return False
        self.p.poll()
        if self.p.returncode is not None:
            self.p.wait()
            return False
        else:
            return True
    
    def restart(self):
        self.stop()
        self.start()
    
    def stop(self):
        if self.running():
            self.p.terminate() # might not be the best idea...
        
        if self.p is not None:
            self.p.wait()
            self.p = None
    
    def start(self):
        if self.running():
            return
        self.p = subprocess.Popen(self.cmd.split())
    
    def __del__(self):
        self.stop()
        
        

if __name__ == '__main__':
    rigctld = Daemon('rigctld -m120 -r/dev/ttyUSB0 -s38400')
    time.sleep(1)
    print(rigctld.running())
    rigctld.stop()
    time.sleep(1)
    print(rigctld.running())
    rigctld.restart()
    time.sleep(1)
    print(rigctld.running())
    rigctld.restart()
    time.sleep(1)
    print(rigctld.running())
    for i in range(100):
        time.sleep(1)
        print(rigctld.running())

    
    
    
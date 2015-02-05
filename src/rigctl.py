
import socket
import enum
import subprocess
import time

class Rigctl(object):
    
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
        

if __name__ == '__main__':
    r = Rigctl()
    r.set_freq(28120000)
    
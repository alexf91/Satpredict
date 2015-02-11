import os
from satpredict_app import *
import tkinter as tk
import subprocess
import fileaccess
from datetime import *

def setup_directories():
    os.makedirs(os.path.expanduser('~/.satpredict'), exist_ok=True)
    os.makedirs(os.path.expanduser('~/.satpredict/sats'), exist_ok=True)
    os.makedirs(os.path.expanduser('~/.satpredict/trsp'), exist_ok=True)


def main():
    
    if 'RASPBERRY_PI' in os.environ:
        date = datetime.now()
        filename = 'satpredict_' + date.strftime('%Y-%m-%d-%H-%M') + '.log'
        
        stderr_fd = sys.stderr.fileno()
        f = os.open(filename, os.O_WRONLY | os.O_CREAT)
        os.dup2(f, stderr_fd)
    
    setup_directories()
    
    app = SatPredictApp()
    app.title('SatPredict by OE5TKM')
    app.resizable(False, False)
    app.geometry('320x210')
    
    if 'RASPBERRY_PI' in os.environ:
        app.update()
        subprocess.call(['xwit', '-warp', '0', '0'])
        subprocess.call(['xset', 'r', 'off'])
        
    app.mainloop()


if __name__ == '__main__':
    main()
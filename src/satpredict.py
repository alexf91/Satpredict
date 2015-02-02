import os
import configuration


def setupDirectories():
    os.makedirs(os.path.expanduser('~/.sattrack'), exist_ok=True)
    os.makedirs(os.path.expanduser('~/.sattrack/sats'), exist_ok=True)
    os.makedirs(os.path.expanduser('~/.sattrack/trsp'), exist_ok=True)


def main():
    setupDirectories()
    







if __name__ == '__main__':
    main()
import json
import os


class Configuration(object):
    '''
    Global configuration of the program
    '''


    def __init__(self, path):
        '''
        Creates a configuration object from the config file
        at path or creates a new one with default values.
        '''
        
        #File exists, read configuration
        if os.path.isfile(path):
            fp = open(path)
            conf = json.load(fp)
            self.name = conf['name']
            self.satellites = list(conf['satellites'])
            
        else:
            self.name = 'default'
            self.satellites = [39444, 27607, 36122]
            json.dump(self.__dict__(), open(path, 'w'), sort_keys=True, indent=4, separators=(',', ': '))
            
    
    def __dict__(self):
        return {'name':self.name, 'satellites':self.satellites}
    
        
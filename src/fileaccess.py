import os
import json
import urllib3
from enum import Enum

class ExtendedEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, SatelliteEntry):
            return o.__dict__()
        elif isinstance(o, Transponder):
            return o.__dict__()
        elif isinstance(o, Transponder.Mode):
            return o.name
        elif isinstance(o, Location):
            return o.__dict__()
        return json.JSONEncoder.default(self, o)

class Database(object):
    '''
    Database containing satellite orbit- and transponder information
    '''

    def __init__(self, satDirectory=os.path.expanduser('~/.satpredict/sats'), trspDirectory=os.path.expanduser('~/.satpredict/trsp')):
        '''
        Constructor
        '''
        self.satDirectory = satDirectory
        os.makedirs(os.path.expanduser(satDirectory), exist_ok=True)
        self.trspDirectory = trspDirectory
    
    
    def update(self):
        # Get satellite orbit data from celestrak
        tleData = CelestrakLoader('amateur.txt').get()
        trspData = TransponderLoader(self.trspDirectory).get()
        
        for scn in tleData.keys():
            trsp = trspData.get(scn)
            cel = tleData.get(scn)
            sat = SatelliteEntry.fromData(cel.name, cel.nick, cel.tle1, cel.tle2, trsp)

            json.dump(sat, open(os.path.join(self.satDirectory, '{}.sat'.format(scn)), 'w'),
                      sort_keys=True, indent=4, separators=(',', ': '), cls=ExtendedEncoder)
            
    def query(self, filter):
        if isinstance(filter, int):
            filter = [filter]
        
        sats = list()
        for scn in filter:
            path = os.path.join(self.satDirectory, '{}.sat'.format(scn))
            if os.path.isfile(path):
                fd = open(path, 'r')
                sat = SatelliteEntry.fromJson(json.load(fd))
                sats.append(sat)

        return sats



class CelestrakLoader(object):
    
    def __init__(self, filename):
        self.filename = filename
    
    def get(self):
        '''
        Returns dictionary with entries of received data {scn : CelestrakEntry}
        '''
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', 'http://www.celestrak.com/NORAD/elements/{}'.format(self.filename), redirect=0)
            
            data = response.data.decode('utf-8').splitlines()
            entries = dict()
            for i in range(0, len(data), 3):
                entry = CelestrakEntry(data[i:i+3])
                entries[entry.scn] = entry
                
            return entries
        
        except:
            raise ConnectionError


class CelestrakEntry(object):
    
    def __init__(self, data):
        '''
        Takes list with 3 elements representing the 3 lines of the TLE entry
        '''
        nsplit = data[0].strip(' )').rsplit(' (', 1)
        self.scn  = int(data[2].split()[1])
        self.name = nsplit[0]
        try:
            self.nick = nsplit[1]
        except IndexError:
            self.nick = None
            
        self.tle1 = data[1].strip()
        self.tle2 = data[2].strip()



class SatelliteEntry(object):
    '''
    classdocs
    '''

    def __init__(self, scn, name, nick, tle1, tle2, transponders=None):
        self.scn = int(scn)
        self.name = name
        self.nick = nick
        self.tle1 = tle1
        self.tle2 = tle2
        self.transponders = transponders
    
    @property
    def line1(self):
        return '{} ({})'.format(self.name, self.nick)
    
    @property
    def line2(self):
        return self.tle1
    
    @property
    def line3(self):
        return self.tle2
    
    @classmethod
    def fromJson(cls, obj):
        '''
        Create satellite entry from json object
        '''
        trsps = []
        for t in obj['trsps']:
            trsps.append(Transponder.fromJson(t))
            
        return cls(obj['scn'],
                   obj['name'],
                   obj['nick'],
                   obj['tle1'],
                   obj['tle2'], 
                   trsps)
    
    
    @classmethod
    def fromData(cls, name, nick, tle1, tle2, transponders=None):
        '''
        Create satellite object from TLE data
        '''
        scn = int(tle2.split()[1])
        return cls(scn, name, nick, tle1, tle2, transponders)


    def __str__(self):
        return '{}\n{}'.format(self.scn, self.name)
    
    
    def __dict__(self):
        return {'scn'   : self.scn,
                'name'  : self.name,
                'nick'  : self.nick,
                'tle1'  : self.tle1,
                'tle2'  : self.tle2,
                'trsps' : self.transponders}



class TransponderLoader(object):
    
    def __init__(self, path):
        self.path = path;

    def get(self):
        '''
        Returns a dictionary with scn -> Transponder mapping
        '''
        sats = dict()
        for file in os.listdir(self.path):
            if file.endswith('.trsp'):
                obj = json.load(open(os.path.join(self.path, file)))
                scn = int(os.path.splitext(file)[0])
                trsps = list()
                for t in obj:
                    trsps.append(Transponder.fromJson(t))
                sats[scn] = trsps

        return sats
        

class Transponder(object):
    class Mode(Enum):
        LINEAR = 0
        FM = 1
        CW = 2
        DIGI = 3
    
    def __init__(self, name, mode, down, up=None, invert=False, pl=None):
        self.name = name
        self.mode = mode
        self.down = down
        self.up = up
        self.invert = invert
        self.pl = pl
    
    
    @classmethod
    def fromData(cls, name, mode, down, up=None, invert=False, pl=None):
        m = mode
        if isinstance(mode, str):
            m = Transponder.Mode[mode]
        elif isinstance(mode, int):
            m = Transponder.Mode(mode)
        
        return cls(name, m, down, up, invert, pl)
    
    
    @classmethod
    def fromJson(cls, obj):
        return cls(obj['name'],
                   Transponder.Mode[obj['mode']],
                   obj['down'],
                   obj['up'],
                   obj['invert'],
                   obj['pl'])
    
    
    def __dict__(self):
        return {'name'  : self.name,
                'mode'  : self.mode,
                'down'  : self.down,
                'up'    : self.up,
                'invert': self.invert,
                'pl'    : self.pl}




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
            self.locations = list()
            for loc in conf['locations']:
                name = loc['name']
                long = loc['longitude']
                lat =  loc['latitude']
                elev = loc['elevation']
                
                self.locations.append(Location(name, long, lat, elev))
            
        else:
            self.name = 'default'
            self.satellites = [24278, 7530, 25544, 39444, 27607, 36122]
            self.locations = [Location('JN68WN', 13.902486, 48.542816, 550)]
            
            json.dump(self.__dict__(), open(path, 'w'), sort_keys=True, indent=4, separators=(',', ': '), cls=ExtendedEncoder)
            
    
    def __dict__(self):
        return {'name':self.name, 'satellites':self.satellites, 'locations':self.locations}
    

class Location(object):
    def __init__(self,name, long, lat, elev):
        self.name = name
        self.long = long
        self.lat = lat
        self.elev = elev
    
    def __dict__(self):
        return {'name':self.name, 'longitude':self.long, 'latitude':self.lat, 'elevation':self.elev}
        
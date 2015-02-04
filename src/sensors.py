import smbus
import geomag
import numpy
import sys
import time

class HMC5883L(object):
    '''
    Class for the HMC5883L Magnetic sensor using smbus
    '''

    def __init__(self, bus=1, address=0x1E, gain=7):
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.x_off = 0
        self.y_off = 0
        self.z_off = 0
        
        self.x_scale = 1
        self.y_scale = 1
        self.z_scale = 1

        self.bus.write_byte_data(self.address, 0x00, 0x70)
        self.bus.write_byte_data(self.address, 0x01, gain << 5)
        self.bus.write_byte_data(self.address, 0x02, 0x00)
        
        

    def __read_block(self):
        return self.bus.read_i2c_block_data(self.address, 0x00)

    def __twos_complement(self, val, len):
        # Convert twos compliment to integer
        if (val & (1 << len - 1)):
            val = val - (1<<len)
        return val

    def __convert(self, data, offset):
        val = self.__twos_complement(data[offset] << 8 | data[offset+1], 16)
        if val == -4096: return None
        return val

    def calibrate(self):
        #Positive bias configuration
        self.bus.write_byte_data(self.address, 0x00, 0x71)
        time.sleep(0.2)
        (x_pos, y_pos, z_pos) = self.axes_raw()
        
        #Negative bias configuration
        self.bus.write_byte_data(self.address, 0x00, 0x72)
        time.sleep(0.2)
        (x_neg, y_neg, z_neg) = self.axes_raw()
        
        self.x_off = x_pos + x_neg
        self.y_off = y_pos + y_neg
        self.z_off = z_pos + z_neg
        
        self.bus.write_byte_data(self.address, 0x00, 0x70)

    def axes_raw(self):
        data = self.bus.read_i2c_block_data(self.address, 0x00)
        #print map(hex, data)
        x = self.__convert(data, 3)
        y = self.__convert(data, 7)
        z = self.__convert(data, 5)
        return (x,y,z)

    def axes(self):
        (x, y, z) = self.axes_raw()
        
        return (x-self.x_off, y-self.y_off, z-self.z_off)


class MMA7455(object):
    def __init__(self, bus=1, address=0x1D, glvl=8):
        assert glvl in [2, 4, 8]
        
        self.bus = smbus.SMBus(bus)
        self.address = address
        
        if glvl == 8: glvl = 0
        elif glvl == 2: glvl= 1
        elif glvl == 4: glvl = 2
        print(glvl)
        mcr = (1<<6) | (glvl << 2) | 0x01
        self.bus.write_byte_data(self.address, 0x16, mcr)
    
    def __read_block(self):
        return self.bus.read_i2c_block_data(self.address, 0x00)

    def __twos_complement(self, val, len):
        # Convert twos compliment to integer
        val = val & (2**len - 1)
        if (val & (1 << len - 1)):
            val = val - (1<<len)
        return val

    def __convert(self, data, offset):
        val = self.__twos_complement(data[offset+1] << 8 | data[offset], 10)
        return val
    
    def calibrate(self):
        '''
        requires sensor to be completely flat (x=0g, y=0g, z=1g)
        '''
        x_off = 0
        y_off = 0
        z_off = 0
        for i in range(0, 16):
            (x, y, z) = self.axes()
            
            x_off += round(-2.1*x)
            y_off += round(-2.1*y)
            z_off += round(2.1 * (-64 - z))
            
            self.bus.write_byte_data(self.address, 0x10, x_off & 0xFF)
            self.bus.write_byte_data(self.address, 0x11, x_off >> 8)
            self.bus.write_byte_data(self.address, 0x12, y_off & 0xFF)
            self.bus.write_byte_data(self.address, 0x13, y_off >> 8)
            self.bus.write_byte_data(self.address, 0x14, z_off & 0xFF)
            self.bus.write_byte_data(self.address, 0x15, z_off >> 8)        
        
            time.sleep(0.05)
    
    def axes(self):
        data = self.__read_block()
        x = self.__convert(data, 0)
        y = self.__convert(data, 2)
        z = self.__convert(data, 4)
        
        return (x, y, z)
        
        

class Compass(object):
    def __init__(self, location, sensor=HMC5883L()):
        '''
        sensor is a gyro or magnetic sensor device like HMC5883L
        location is triple (long(°), lat(°), altitude(m))
        '''
        lon = location[0]
        lat = location[1]
        alt = location[2]
        
        self.sensor = sensor
        self.declination = geomag.declination(dlat=lat, dlon=lon, h=3.2808399*alt)
    
    def __normalize(self, vector):
        s = numpy.sqrt(sum([i*i for i in vector]))
        return tuple([i / s for i in vector])

    def calibrate(self):
        self.sensor.calibrate()

    def az_el(self):
        v = self.sensor.axes()
        return v
    

if __name__ == "__main__":
    # http://magnetic-declination.com/Great%20Britain%20(UK)/Harrogate#
    compass = Compass((48.542840, 13.902494, 550))
    compass.calibrate()
    mma = MMA7455()
    mma.calibrate()
    while True:
        sys.stdout.write('\r' + str(mma.axes()) + '                 ')
        sys.stdout.flush()
        time.sleep(0.5)
  

# test_mcp4725.py 
# (C) 2017 Patrick Menschel
import smbus
import struct

class mcp4725():

    def __init__(self,bus=1,addr=0x62):
        self.bus = smbus.SMBus(bus)
        self.addr = addr
        self.status = {}

    def fast_write_dac(self,dac):
        #with fast mode, data payload reduces to the dac_val in 16bit big endian
        data = struct.pack(">H",dac)
        return self.bus.write_byte_data(self.addr,*data)#mapping the two bytes of data to 2nd and 3rd argument of function
    
    def write_status_and_dac_registers(self,dac,pd=0,we=False):
        cmd = 0x40
        if we:
            cmd = 0x60
        cmd |= (pd << 1)
        revdac = struct.unpack("H",struct.pack(">H",dac<<4))[0]#flip the bytes
        #the chip wants big endian format but the RPI I2C sends in little endian format
        return self.bus.write_word_data(self.addr,cmd,revdac)#three bytes of data, separated in 8bit cmd and 16bit data payload


    def read_status(self):
        data = bytearray(self.bus.read_i2c_block_data(self.addr,0))#the command "0" is not necessary und luckily ignored by the chip
        #returns 5bytes including (status bits, dac and eeprom val) and repeats these bytes several times after that. We ignore it though.
        rdy = (data[0] & (1 << 7)) >> 7
        por = (data[0] & (1 << 6)) >> 6
        pod = (data[0] & (3 << 1)) >> 1
        dac = struct.unpack(">H",data[1:3])[0]>>4
        eep = struct.unpack(">H",data[3:5])[0]
        eeppod = (eep & (3 << 5)) >> 5
        eepdac = eep & 0xFFF
        statusdict = {"ready":rdy,
                      "poweronreset":por,
                      "powerdown":pod,
                      "dac":dac,
                      "eeprompowerdown":eeppod,
                      "eepromdac":eepdac}
        self.status.update(statusdict)#save it locally
        return statusdict


if __name__ == "__main__":
    #test skript for mcp4724 with external indicator (LM3514 chip with 10LED bar)
    import time
    from pprint import pprint as pp
    mcp4725_obj = mcp4725()
    print("test1 - fast write")
    for i in range(1024):
        mcp4725_obj.fast_write_dac(i)
        time.sleep(0.01)
    print("and reset")
    mcp4725_obj.fast_write_dac(0)#zero output

    print("test2 - normal write")
    for i in range(1024):
        mcp4725_obj.write_status_and_dac_registers(i)
        time.sleep(0.01)
    print("and reset")
    mcp4725_obj.fast_write_dac(0)#zero output

    dac = 512
    print("test3 - write with eeprom {0}".format(dac))
    mcp4725_obj.write_status_and_dac_registers(dac,we=True)
    time.sleep(0.1)
    dac = 256
    print("test4 - fast write {0}".format(dac))
    mcp4725_obj.fast_write_dac(dac)
    time.sleep(0.1)
    print("test5 - read status from mcp4725")
    stat = mcp4725_obj.read_status()
    if stat:
        print("status dict follows:")
        pp(stat)
    
    print("now toggle power supply and see if it was saved")

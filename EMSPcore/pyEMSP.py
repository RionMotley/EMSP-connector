import serial
import time, os
import struct
import ConfigParser

class EMSP:

    # Class initialization
    def __init__(self, serPort, baudRate):

        #read config
        self.config = ConfigParser.ConfigParser()
        self.config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)),'config.ini'))
        #init serial port
        self.ser = serial.Serial()
        self.ser.port = serPort
        self.ser.baudrate = baudRate
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 2
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False
        self.ser.writeTimeout = 2

        try:
            self.Log("SYS","Trying to connect board on ..." )
            self.ser.open()
        except Exception, error:
            self.Log("ERR","Error opening " + self.ser.port + " port. " + str(error))



    # Function for logging output
    def Log(self, flag, msg):
        print "{0} {1} - {2}".format(time.ctime(),flag,msg) 



    # Function for sending a command to the board
    def sendCMD(self, dataLength, code, data):

        checkSum = 0
        total_data = ['$', 'M', '<', dataLength, code] + data
        for i in struct.pack('<2B%dh' % len(data), *total_data[3:len(total_data)]):
            checkSum = checkSum ^ ord(i)
        total_data.append(checkSum)

        try:
            self.ser.write(struct.pack('<3c2B%dhB' % len(data), *total_data))
        except Exception, error:
            self.Log("ERR","Error in sendCMD. " + str(error))
            pass

    # Function to receive a data packet from the board
    def getData(self, cmd, rcdata = [], dataLength = 0):
        try:

            ### get data
            start = time.time()
            self.sendCMD(dataLength,int(self.config.get('Code',cmd)),rcdata)

            while True:
                header = self.ser.read()
                if header == '$':
                    header = header + self.ser.read(2)
                    break

            datalength = struct.unpack('<b', self.ser.read())[0]
            code = struct.unpack('<b', self.ser.read())
            data = self.ser.read(datalength)

            self.ser.flushInput()
            self.ser.flushOutput()
            elapsed = time.time() - start
            ###

            if cmd == 'ATTITUDE':
                temp = struct.unpack('<'+'h'*(datalength/2),data)
                return self.getATTITUDE(temp, elapsed)
            elif cmd == 'RC':
                temp = struct.unpack('<'+'h'*(datalength/2),data)
                return self.getRC(temp, elapsed)
            elif cmd == 'RAW_IMU':
                temp = struct.unpack('<'+'h'*(datalength/2),data)
                return self.getRAW_IMU(temp, elapsed)
            elif cmd == 'MOTOR':
                temp = struct.unpack('<'+'h'*(datalength/2),data)
                return self.getMOTOR(temp, elapsed)
            elif cmd == 'SERVO':
                temp = struct.unpack('<'+'h'*(datalength/2),data)
                return self.getSERVO(temp, elapsed)
            elif cmd == 'API_VERSION':
                temp = struct.unpack('<'+'b'*(datalength),data)
                return self.getAPI_VERSION(temp, elapsed)
            elif cmd == 'FC_VARIANT':
                temp = struct.unpack('<'+'c'*(datalength),data)
                return self.getFC_VARIANT(temp, elapsed)
            elif cmd == 'FC_VERSION':
                temp = struct.unpack('<'+'b'*(datalength),data)
                return self.getFC_VERSION(temp, elapsed)
            elif cmd == 'BOARD_INFO':
                temp = struct.unpack('<'+'c'*(datalength-2)+'h',data)
                return self.getBOARD_INFO(temp, elapsed)
            elif cmd == 'BUILD_INFO':
                temp = struct.unpack('<'+'c'*(datalength),data)
                return self.getBUILD_INFO(temp, elapsed)
            else:
                return "No return error!"

        except Exception, error:
            self.Log("ERR","Error in getData. " + str(error))
            pass

    def getATTITUDE(self, temp, elapsed):
        data = {}
        data['angx'] = float(temp[0]/10.0)
        data['angy'] = float(temp[1]/10.0)
        data['heading'] = float(temp[2])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getRC(self, temp, elapsed):
        data = {}
        data['roll'] = float(temp[0])
        data['pitch'] = float(temp[1])
        data['yaw'] = float(temp[2])
        data['throttle'] = float(temp[3])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getRAW_IMU(self, temp, elapsed):
        data = {}
        data['ax'] = float(temp[0])
        data['ay'] = float(temp[1])
        data['az'] = float(temp[2])
        data['gx'] = float(temp[3])
        data['gy'] = float(temp[4])
        data['gz'] = float(temp[5])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getAPI_VERSION(self, temp, elapsed):
        data = {}
        data['protver'] = int(temp[0])
        data['majorver'] = int(temp[1])
        data['minorver'] = int(temp[2])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getFC_VARIANT(self, temp, elapsed):
        data = {}
        str = ''
        for c in temp:
            str += c
        data['fcId'] = str
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getFC_VERSION(self, temp, elapsed):
        data = {}
        data['fcver'] = int(temp[0])
        data['majorfcver'] = int(temp[1])
        data['minorfcver'] = int(temp[2])
        data['elapsed'] = round(elapsed*1000,3)
        return data       

    def getBOARD_INFO(self, temp, elapsed):
        data = {}
        str = ''
        for i in range(len(temp)-1):
            str += temp[i]
        if temp[-1] == 1:
            str += ' NAZE32'
        elif temp[-1] == 2:
            str += ' NAZE32_REV5'
        elif temp[-1] ==3:
            str += ' NAZE32_SP'
        data['boardId'] = str
        data['elapsed'] = round(elapsed*1000,3)
        return data   

    def getBUILD_INFO(self, temp, elapsed):
        data = {}
        str = ''
        for c in temp[0:11]:
            str += c
        data['date'] = str
        str = ''
        for c in temp[11:19]:
            str += c
        data['time'] = str
        str = ''        
        for c in temp[19:26]:
            str += c
        data['git'] = str
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getSET_RAW_RC(self, temp, elapsed):
        pass

    def getMOTOR(self, temp, elapsed):
        data = {}
        data['m1'] = float(temp[0])
        data['m2'] = float(temp[1])
        data['m3'] = float(temp[2])
        data['m4'] = float(temp[3])
        data['m5'] = float(temp[4])
        data['m6'] = float(temp[5])
        data['m7'] = float(temp[6])
        data['m8'] = float(temp[7])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def getSERVO(self, temp, elapsed):
        data = {}
        data['s1'] = float(temp[0])
        data['s2'] = float(temp[1])
        data['s3'] = float(temp[2])
        data['s4'] = float(temp[3])
        data['s5'] = float(temp[4])
        data['s6'] = float(temp[5])
        data['s7'] = float(temp[6])
        data['s8'] = float(temp[7])
        data['elapsed'] = round(elapsed*1000,3)
        return data

    def arm(self):
        timer = 0
        start = time.time()
        while timer < 0.5:
            data = [1500,1500,2000,1000]
            self.sendCMD(8,int(self.config.get('Code','SET_RAW_RC')),data)
            time.sleep(0.05)
            timer = time.time() - start

    def disarm(self):
        timer = 0
        start = time.time()
        while timer < 0.5:
            data = [1500,1500,1000,1000]
            self.sendCMD(8,int(self.config.get('Code','SET_RAW_RC')),data)
            time.sleep(0.05)
            timer = time.time() - start


import struct
import threading

import serial
import crcmod


class SerialParser:
    def __init__(self, serialPortName: str, callback):
        self.serialPortName = serialPortName
        self.preamble = bytearray(b'\xFF\xFF')
        self.buffer = bytearray()
        self.packetBuffer = {}
        self.callback = callback
        self.ser = serial.Serial(self.serialPortName, 9600)
        self.crc16Gen = crcmod.mkCrcFun(poly=0x11021, initCrc=0xFFFF, rev=False, xorOut=0x0000)
        if not self.ser.is_open:
            raise RuntimeError('Serial port is not open')

        self.thread = threading.Thread(target=mainZaLoop, args=(self, ), daemon=True)
        self.thread.start()

    def crc16(self, data):
        return self.crc16Gen(data)

    def parsePacket(self, packet: bytearray):
        id = int.from_bytes(packet[2:2 + 2], byteorder='little', signed=False)
        accX = struct.unpack('<f', packet[4:4 + 4])[0]
        accY = struct.unpack('<f', packet[4 + 4:4 + 8])[0]
        accZ = struct.unpack('<f', packet[4 + 8:4 + 12])[0]
        gyroX = struct.unpack('<f', packet[4 + 12:4 + 16])[0]
        gyroY = struct.unpack('<f', packet[4 + 16:4 + 20])[0]
        gyroZ = struct.unpack('<f', packet[4 + 20:4 + 24])[0]
        temp = struct.unpack('<f', packet[4 + 24:4 + 28])[0]
        press = struct.unpack('<f', packet[4 + 28:4 + 32])[0]
        hum = struct.unpack('<f', packet[4 + 32:4 + 36])[0]
        co2 = struct.unpack('<f', packet[4 + 36:4 + 40])[0]
        lat = struct.unpack('<f', packet[4 + 40:4 + 44])[0]
        long = struct.unpack('<f', packet[4 + 44:4 + 48])[0]
        secs = int.from_bytes(packet[4 + 48:4 + 52], byteorder='little', signed=False)
        err = packet[4 + 52]
        crc = packet[4 + 53:4 + 55]
        if int.from_bytes(crc, byteorder='little', signed=False) != self.crc16(packet[:len(packet) - 2]):
            print("crc mismatch")
            return None
        dict = {"id": id, "accX": accX, "accY": accY, "accZ": accZ, "gyroX": gyroX, "gyroY": gyroY, "gyroZ": gyroZ,
                "temp": temp, "press": press, "hum": hum, "co2": co2, "secs": secs, "err": err,
                "acc": ((accX ** 2 + accY ** 2 + accZ ** 2) ** 0.5),
                "gyro": ((gyroX ** 2 + gyroY ** 2 + gyroZ ** 2) ** 0.5),
                "lat": lat, "long": long}
        self.packetBuffer.update(dict)
        self.callback(dict)
        print(packet)
        print(dict)
        print('')
        return id, accX, accY, accZ, gyroX, gyroY, gyroZ, temp, press, hum, co2, lat, long, secs, err

    def readSerial(self):
        if self.ser.is_open:
            self.buffer += self.ser.read(size=50)
            idx = self.buffer.find(self.preamble)
            if idx != -1:
                if idx + 59 <= len(self.buffer) - 1:
                    self.parsePacket(self.buffer[idx:idx + 59])
                    self.buffer = bytearray(self.buffer[idx + 59:])

    def disconnect(self):
        self.ser.close()


def mainZaLoop(sp: SerialParser):
    while True:
        sp.readSerial()

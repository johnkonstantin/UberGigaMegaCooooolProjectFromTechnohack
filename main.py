import threading
from ui import MainWindow
from serialParser import SerialParser


def bim(se: SerialParser):
    while 1:
        se.readSerial()


if __name__ == '__main__':
    mainWindow = MainWindow()

    #ser = SerialParser('COM10', callback=graphsFrame.addPacket)

    #thread = threading.Thread(target=bim, args=(ser,), daemon=True)
    #thread.start()

    mainWindow.mainloop()

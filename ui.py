import datetime
import tkinter as tk
from random import randrange
from time import sleep
from tkinter import ttk

import serial.tools.list_ports
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkintermapview import TkinterMapView

from serialParser import SerialParser


class ComFrame(tk.Frame):
    def __init__(self, master, callbackPacketPlot):
        tk.Frame.__init__(self, master)
        self.master = master
        self.callbackPacketPlot = callbackPacketPlot
        self.sp = None

        self.comLabel = tk.Label(self, text="COM Порт:")
        self.currentComPort = tk.StringVar()
        self.comCombo = ttk.Combobox(self, textvariable=self.currentComPort, values=("COM10",))
        self.updateComButton = tk.Button(self, text="Обновить")
        self.connectComButton = tk.Button(self, text="Отключиться")
        self.comLabel.grid(row=0, column=0, sticky=tk.NSEW, columnspan=1, rowspan=1)
        self.comCombo.grid(row=0, column=1, sticky=tk.NSEW, columnspan=2, rowspan=1)
        self.updateComButton.grid(row=0, column=3, sticky=tk.NSEW, columnspan=1, rowspan=1)
        self.connectComButton.grid(row=1, column=1, sticky=tk.NSEW, columnspan=4, rowspan=1)

        def comComboBoxUpdate():
            comPorts = serial.tools.list_ports.comports()
            print("Com ports found:")
            portsList = []
            for port, desc, hwid in sorted(comPorts):
                print("{}: {} [{}]".format(port, desc, hwid))
                portsList.append(port)
            self.comCombo["values"] = portsList

        def comComboBoxConnect():
            if self.currentComPort.get() == "":
                return
            if self.sp is not None:
                self.sp.disconnect()
                self.sp = None
                self.connectComButton["text"] = "Подключиться"
                return
            print("Try to connect to: ", self.currentComPort.get())
            self.sp = SerialParser(self.currentComPort.get(), self.callbackPacketPlot)
            self.connectComButton["text"] = "Отключиться"

        self.updateComButton["command"] = comComboBoxUpdate
        self.connectComButton["command"] = comComboBoxConnect


class MapFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        self.currentTileServer = tk.StringVar()
        self.tileServers = {
            "OSM": "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "Google Normal": "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga",
            "Google Satellite": "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga"
        }
        self.tileServersCombobox = ttk.Combobox(self, textvariable=self.currentTileServer,
                                                values=list(self.tileServers.keys()),
                                                state='readonly')
        self.tileServersCombobox.current(0)
        self.mapView = TkinterMapView(self, width=640, height=470, corner_radius=25)
        self.tileServersCombobox.bind("<<ComboboxSelected>>", lambda event: (
            self.mapView.set_tile_server(self.tileServers[self.currentTileServer.get()])
        ))
        self.mapView.set_position(deg_x=54.842994, deg_y=83.093222, marker=True, text="25.08.2024 15:49:07")

        self.mapView.pack(fill=tk.BOTH, side=tk.TOP)
        self.tileServersCombobox.pack(side=tk.BOTTOM)

    def setPosition(self, deg_x: float, deg_y: float, time: str):
        self.mapView.set_position(deg_x=deg_x, deg_y=deg_y, marker=True).set_text(time)


class GraphFrame(tk.Frame):
    def __init__(self, master, name):
        tk.Frame.__init__(self, master)
        self.master = master
        self.name = name
        self.xList = []
        self.yList = []
        self.xStart = 0
        self.plotL = 20

        self.figure = pyplot.figure(figsize=(7.5, 4.5), dpi=50)
        self.figure.gca().set_title(self.name)
        self.line, = pyplot.plot_date(self.xList, self.yList, '-')
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
        self.figure_canvas.get_tk_widget().pack()

        def onscroll(event):
            if len(self.xList) <= self.plotL:
                return
            if event.button == "up":
                if self.xStart + self.plotL < len(self.xList) - 1:
                    self.xStart = self.xStart + 1
                else:
                    return
                if self.xStart >= len(self.xList):
                    self.xStart = len(self.xList) - 1
            else:
                self.xStart = self.xStart - 1
                if self.xStart < 0:
                    self.xStart = 0

        self.figure_canvas.mpl_connect('scroll_event', onscroll)

        def updatePlot(frame):
            start = 0
            stop = 0
            if self.xStart >= len(self.xList):
                if (len(self.xList) - 1) >= 0:
                    self.xStart = (len(self.xList) - 1)
                else:
                    self.xStart = 0
            else:
                start = self.xStart
                if self.xStart + self.plotL < len(self.xList):
                    stop = self.xStart + self.plotL
                else:
                    stop = len(self.xList)
            self.line.set_data(self.xList[start:stop], self.yList[start:stop])
            self.figure.gca().relim()
            self.figure.gca().autoscale_view()
            if len(self.yList) > 1:
                self.figure.gca().set_ylim(bottom=min(self.yList) * 0.8, top=max(self.yList) * 1.2)
            return self.line,

        self.animation = FuncAnimation(self.figure, updatePlot, frames=60, interval=60)

    def addPoint(self, x, y):
        self.xList.append(x)
        self.yList.append(y)
        if len(self.xList) >= self.plotL:
            if self.xStart + self.plotL == len(self.xList) - 2:
                self.xStart = self.xStart + 1


class ErrFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        self.bmpInitLabel = tk.Label(self, text="BMP Init", bg="green")
        self.bmpReadLabel = tk.Label(self, text="BMP Read", bg="green")
        self.mpuInitLabel = tk.Label(self, text="MPU Init", bg="green")
        self.mpuReadLabel = tk.Label(self, text="MPU Read", bg="green")
        self.gpsReadLabel = tk.Label(self, text="GPS Read", bg="green")
        self.co2ReadLabel = tk.Label(self, text="CO2 Read", bg="green")
        self.infoLabel = tk.Label(self, text="Статус устройства:")

        self.infoLabel.grid(row=0, column=0)
        self.bmpInitLabel.grid(row=0, column=1)
        self.bmpReadLabel.grid(row=0, column=2)
        self.mpuInitLabel.grid(row=0, column=3)
        self.mpuReadLabel.grid(row=0, column=4)
        self.gpsReadLabel.grid(row=0, column=5)
        self.co2ReadLabel.grid(row=0, column=6)

    def setErr(self, err: int):
        if err & (1 << 2):
            self.bmpInitLabel['bg'] = 'red'
        if err & (1 << 3):
            self.bmpReadLabel['bg'] = 'red'
        if err & (1 << 4):
            self.mpuInitLabel['bg'] = 'red'
        if err & (1 << 5):
            self.gpsReadLabel['bg'] = 'red'
        if err & (1 << 6):
            self.co2ReadLabel['bg'] = 'red'
        if err & (1 << 7):
            self.mpuReadLabel['bg'] = 'red'


class GraphsFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        self.tempGraph = GraphFrame(self, "Температура, градусы Цельсия")
        self.pressGraph = GraphFrame(self, "Давление, Па")
        self.humGraph = GraphFrame(self, "Относительная влажность, проценты")
        self.angVelGraph = GraphFrame(self, "Угловая скорость, градус/с")
        self.accelGraph = GraphFrame(self, "Линейное ускорение, доли g")
        self.carbGraph = GraphFrame(self, "Содержание CO2, ppm")

        self.tempGraph.grid(row=0, column=0, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.pressGraph.grid(row=1, column=0, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.humGraph.grid(row=2, column=0, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.angVelGraph.grid(row=0, column=1, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.accelGraph.grid(row=1, column=1, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.carbGraph.grid(row=2, column=1, sticky=tk.NSEW, rowspan=1, columnspan=1)
        self.grid_columnconfigure(index=0, weight=0)
        self.grid_columnconfigure(index=1, weight=0)
        self.grid_rowconfigure(index=0, weight=0)
        self.grid_rowconfigure(index=1, weight=0)
        self.grid_rowconfigure(index=2, weight=0)

        self.i = 0

    def addPacket(self, packet: dict):
        self.tempGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["temp"])
        self.pressGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["press"])
        self.humGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["hum"])
        self.angVelGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["gyro"])
        self.accelGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["acc"])
        self.carbGraph.addPoint(
            datetime.datetime(year=2024, month=8, day=25) + datetime.timedelta(hours=15, minutes=47,
                                                                               seconds=(34 + self.i)),
            packet["co2"])
        self.i = self.i + 1


class MainWindow(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry('1280x720')
        self.resizable(False, False)
        self.title("Ground Station Client")

        bimbimData = []
        for i in range(100):
            bimbimData.append({"temp": 25.5 + randrange(-10, 10) / 15.0, "press": 98657.0 + randrange(-30, 50) / 0.7,
                               "hum": 47 + randrange(-10, 10) / 10.0, "gyro": 0 + randrange(-10, 10) / 10.0,
                               "acc": 1 + randrange(-10, 10) / 100.0, "co2": 504 + randrange(-10, 10) / 10.0})

        mapFrame = MapFrame(self)
        graphsFrame = GraphsFrame(self)
        comFrame = ComFrame(self, graphsFrame.addPacket)

        comFrame.place(anchor='nw')
        mapFrame.place(anchor='nw', rely=0.12, relwidth=0.4, relheight=0.68)
        graphsFrame.place(anchor='nw', relx=0.405)

        for i in bimbimData:
            graphsFrame.addPacket(i)
            print("add ", i)

        errFrame = ErrFrame(self)
        errFrame.place(rely=0.9)

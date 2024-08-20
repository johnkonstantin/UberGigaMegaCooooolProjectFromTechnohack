import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
from tkintermapview import TkinterMapView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np

connectedFlag = False


def comComboBoxUpdate(combobox: ttk.Combobox):
    comPorts = list(serial.tools.list_ports.comports())
    print("Com ports found: ", comPorts)
    combobox["values"] = comPorts


def comComboBoxConnect():
    if currentComPort.get() == "":
        return
    print("Try to connect to: ", currentComPort.get())


if __name__ == '__main__':
    mainWindow = tk.Tk()
    mainWindow.geometry('1280x720')

    currentComPort = tk.StringVar()
    comComboBox = ttk.Combobox(mainWindow, textvariable=currentComPort, state="readonly")
    updateComButton = tk.Button(mainWindow, text="Обновить", command=lambda: (
        comComboBoxUpdate(comComboBox)
    ))
    connectComButton = tk.Button(mainWindow, text="Подключиться", command=comComboBoxConnect)
    tileServers = {
        "OSM": "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "Google Normal": "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga",
        "Google Satellite": "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga"
    }
    currentTileServer = tk.StringVar()
    tileServersCombobox = ttk.Combobox(mainWindow, textvariable=currentTileServer, values=list(tileServers.keys()),
                                       state='readonly')
    tileServersCombobox.current(0)
    mapView = TkinterMapView(mainWindow, width=640, height=480, corner_radius=25)
    tileServersCombobox.bind("<<ComboboxSelected>>", lambda event: (
        mapView.set_tile_server(tileServers[currentTileServer.get()])
    ))
    mapView.set_position(deg_x=54.842994, deg_y=83.093222)
    fig, ax = plt.subplots()
    ax.set_title("Температура")
    canvas = FigureCanvasTkAgg(fig, master=mainWindow)
    canvas.get_tk_widget().grid(column=2, row=0)
    t = np.arange(0, 2 * np.pi, .01)
    ax.plot(t, np.sin(t))
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, mainWindow, pack_toolbar=False)
    toolbar.update()
    toolbar.grid(column=2, row=1)

    comComboBox.grid(column=0, row=0)
    updateComButton.grid(column=1, row=0)
    connectComButton.grid(column=0, row=1)
    mapView.grid(column=0, row=2)
    tileServersCombobox.grid(column=0, row=3)

    mainWindow.mainloop()

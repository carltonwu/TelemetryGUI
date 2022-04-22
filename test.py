from PyQt6 import QtWidgets, QtCore, QtSerialPort, QtGui, uic
from pyqtgraph import PlotWidget, plot
from PyQt6.QtSerialPort import QSerialPortInfo
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow
import pyqtgraph as pg
import sys
import struct
from random import randint

STRUCT_SIZE = 56

data = {
    'time': [],
    'accx': [],
    'accy': [],
    'accz': [],
    'avelx': [],
    'avely': [],
    'avelz': [],
    'altitude': [],
    'pressure': [],
    'temp': [],
    'w': [],
    'x': [],
    'y': [],
    'z': [],
}

dataStruct = struct.Struct('< f f f f f f f f f f f f f f')

class AddComport(QMainWindow):
    portUpdate = pyqtSignal(str)
    
    def __init__(self, parent, menu):
        super().__init__(parent)
        
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        serial_ports = [port.portName() for port in serial_list]
        serial_ports = [k for k in serial_ports if 'cu.' in k]
        menu.clear()
        if(len(serial_ports) > 0):
            numPorts = len(serial_ports)
            index = 0
            while index < numPorts:
                button_action = QAction(serial_ports[index], self)
                txt = serial_ports[index]
                button_action = QAction( txt , self)
                button_action.setCheckable(True)
                button_action.triggered.connect(lambda checked, txt = txt: self.comPortClick(txt))
                menu.addAction(button_action)
                index += 1
        else:
            print("No com ports found")
            
    def comPortClick(self, port):
        self.portUpdate.emit(port)
        
    def closeEvent(self, event):
        self.close()



class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        form_class = uic.loadUi('mainwindow.ui', self)
        
        comfinder = AddComport(self, self.menuPort)
        self.menuFile.hovered.connect(lambda: self.updatePorts(self, self.menuPort))
        comfinder.portUpdate.connect(self.portInit)
        
        # Baudrate Stuff
        actiongroup = QtGui.QActionGroup(self)
        actiongroup.setExclusive(True)
        actiongroup.addAction(self.br9600)
        actiongroup.addAction(self.br115200)
        
        self.connectButton.clicked.connect(lambda: self.on_toggled())

        self.serial = QtSerialPort.QSerialPort(
            "Port",
            baudRate=QtSerialPort.QSerialPort.BaudRate.Baud9600,
            readyRead=self.receive)
        
        self.br9600.triggered.connect(lambda: self.serial.setBaudRate(9600))
        self.br115200.triggered.connect(lambda: self.serial.setBaudRate(115200))
        
        # Graph Stuff
        self.graph1.setBackground('#1f1f1f')
        self.graph2.setBackground('#1f1f1f')
        self.graph7.setBackground('#1f1f1f')
        self.graph1.setYRange(-20, 20, padding=0)
        self.graph2.setYRange(-20, 20, padding=0)
        pen1 = pg.mkPen(color=(247, 15, 65), width=3)
        pen2 = pg.mkPen(color=(66, 135, 245), width=3)
        pen3 = pg.mkPen(color=(77, 224, 40), width=3)
        self.accx = []
        self.accy = []
        self.accz = []
        self.avelx = []
        self.avely = []
        self.avelz = []
        self.altitude = []
        self.data_line1 = self.graph1.plot(self.accx, pen=pen1)
        self.data_line2 = self.graph1.plot(self.accy, pen=pen2)
        self.data_line3 = self.graph1.plot(self.accz, pen=pen3)
        self.data_line4 = self.graph2.plot(self.avelx, pen=pen1)
        self.data_line5 = self.graph2.plot(self.avely, pen=pen2)
        self.data_line6 = self.graph2.plot(self.avelz, pen=pen3)
        self.data_line7 = self.graph7.plot(self.altitude, pen=pen1)
        
    def updatePorts(self, parent, menu):
        print("port updated")
        comfinder = AddComport(parent, menu)
        comfinder.portUpdate.connect(self.portInit)
        
    @QtCore.pyqtSlot()    
    def receive(self):
        while self.serial.bytesAvailable() >= 120:
            if (self.serial.read(1) == bytes.fromhex('0d')):
                if (self.serial.read(1) == bytes.fromhex('f0')):
                    if (self.serial.read(1) == bytes.fromhex('ef')):
                        if (self.serial.read(1) == bytes.fromhex('be')):
                            packet_s = dataStruct.unpack(self.serial.read(56))
                            self.accx.append(packet_s[1])
                            self.accy.append(packet_s[2])
                            self.accz.append(packet_s[3])
                            self.avelx.append(packet_s[4])
                            self.avely.append(packet_s[5])
                            self.avelz.append(packet_s[6])
                            self.altitude.append(packet_s[7])
                            self.data_line1.setData(self.accx)
                            self.data_line2.setData(self.accy)
                            self.data_line3.setData(self.accz)
                            self.data_line4.setData(self.avelx)
                            self.data_line5.setData(self.avely)
                            self.data_line6.setData(self.avelz)
                            self.data_line7.setData(self.altitude)
                            self.tempLabel.setText(str(round(packet_s[9], 2)) + "(C)")
                            self.altitudeLabel.setText(str(round(packet_s[7], 2)) + "(m)")
        
        
    @QtCore.pyqtSlot()
    def send(self):
        self.serial.write(self.message_le.text().encode())

    @QtCore.pyqtSlot(bool)
    def on_toggled(self):
        checked = self.connectButton.isChecked()
        self.connectButton.setText("Disconnect" if checked else "Connect")
        if checked:
            if not self.serial.isOpen():
                self.serial.open(QtCore.QIODevice.OpenModeFlag.ReadWrite)
                if not self.serial.isOpen():
                    self.connectButton.setChecked(False)
            else:
                self.connectButton.setChecked(False)
        else:
            self.serial.close()
  
    def portInit(self, portName):
        portOpen = False
        if self.serial.isOpen():
            portOpen = True
            self.serial.close()   
        self.serial.setPortName(portName)
        if portOpen:
            self.serial.open(QtCore.QIODevice.OpenModeFlag.ReadWrite)
            if not self.serial.isOpen():
                self.button.setChecked(False)
    
    def closeEvent(self, event):
        self.serial.close()
        print("Com port closed")
    
    #def update_plot_data(self):
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()
from PyQt6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, QLabel, QColorDialog, QHBoxLayout
from PyQt6.QtCore import QTimer
import sys
import glob
from time import sleep
import serial
import threading

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()

def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

ser = serial.Serial(serial_ports()[0], 115200)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.currentData = []
        ser.write(bytearray([0xFF]))
        self.get_data()

        self.temp = QLabel("Температура воздуха: " + str(self.currentData[3]) + "°C")
        self.humidity = QLabel("Влажность воздуха: " + str(self.currentData[-3]) + "%")

        self.airLayout = QHBoxLayout()
        self.airLayout.addWidget(self.temp)
        self.airLayout.addWidget(self.humidity)

        self.pressure = QLabel("Давление воздуха: " + str(self.currentData[5]) + "hPa")
        self.soiltemp = QLabel("Температура почвы: " + str(self.currentData[9]) + "°C")

        self.soilLayout = QHBoxLayout()
        self.soilLayout.addWidget(self.pressure)
        self.soilLayout.addWidget(self.soiltemp)

        self.soilhumidity = QLabel("Влажость почвы: " + str(self.currentData[10]) + "%")
        self.light = QLabel("Интенсивность света: " + str(self.currentData[6]) + "Люкс")

        self.otherLayout = QHBoxLayout()
        self.otherLayout.addWidget(self.soilhumidity)
        self.otherLayout.addWidget(self.light)
        
        self.color = QColorDialog()

        self.submitColor = QPushButton("Задать цвет")
        self.submitColor.clicked.connect(self.onSubmitColor)

        self.signalButton = QPushButton("Включить сирену" if self.currentData[-6] == 0 else "Выключить сирену")
        self.signalButton.clicked.connect(self.onsignalButtonClick)

        self.windButton = QPushButton("Включить вентилятор" if self.currentData[-2] == 0 else "Выключить вентилятор")
        self.windButton.clicked.connect(self.onWindButtonClick)

        self.doorButton = QPushButton("Закрыть дверь" if self.currentData[-1] == 32 else "Открыть дверь")
        self.doorButton.clicked.connect(self.ondoorButtonClick)

        self.melodyButton = QPushButton("Включить мелодию")
        self.melodyButton.clicked.connect(self.onMelodyButtonClick)
        
        layout = QVBoxLayout()
        layout.addWidget(self.humidity)
        layout.addWidget(self.color)
        layout.addWidget(self.submitColor)
        layout.addWidget(self.signalButton)
        layout.addWidget(self.windButton)
        layout.addWidget(self.doorButton)
        layout.addWidget(self.melodyButton)

        container = QWidget()
        container.setLayout(layout)

        self.setWindowTitle("Умный дом")

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.updateData)
        self.timer.start()

        self.setCentralWidget(container)

    def updateData(self):
        ser.write(bytearray([0xFF]))
        self.get_data()
        self.reloadSensors()

    def reloadSensors(self):
        self.humidity.setText("Влажность воздуха: " + str(self.currentData[-3]) + "%")

    def onSubmitColor(self):
        _currentColor = self.color.currentColor()
        _writeRGB = bytearray([0xA3])
        self.reloadSensors()

        _writeRGB.append(_currentColor.red())
        _writeRGB.append(_currentColor.green())
        _writeRGB.append(_currentColor.blue())

        ser.write(_writeRGB)
        self.get_data()
        self.color.show()
        
    def onsignalButtonClick(self):
        ser.write(bytearray([0xA0, 0x1]))
        self.get_data()
        self.reloadSensors()
        self.signalButton.setText("Включить сирену" if self.currentData[-6] == 0 else "Выключить сирену")

    def onWindButtonClick(self):
        ser.write(bytearray([0xA1, 0x1]))
        self.get_data()
        self.reloadSensors()
        self.windButton.setText("Включить вентилятор" if self.currentData[-2] == 0 else "Выключить вентилятор")

    def ondoorButtonClick(self):
        if (self.currentData[-1] == 32):
            ser.write(bytearray([0xA2, 0x96]))
            self.doorButton.setText("Открыть дверь")
        else:
            ser.write(bytearray([0xA2, 0x20]))
            self.doorButton.setText("Закрыть дверь")

        self.get_data()

    def onMelodyButtonClick(self):
        ser.write(bytearray([0xA6, 0x1]))

    def get_data (self):
        sleep(0.1)
        _currentData = str(ser.read_all())
        _currentData = _currentData[2:_currentData.find('\\r\\n')]
        if (_currentData!=''):
            currentDataList = list(map(float, _currentData.split('|')))
            self.currentData = currentDataList
            print(currentDataList)


app = QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec())

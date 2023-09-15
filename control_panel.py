import sys
import os
import time
import platform
import struct
import socket
import pyvisa
import nidaqmx
import scanner_ui
import pandas as pd
import numpy as np
import pyqtgraph as pg
from threading import Thread
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QMouseEvent, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect, QFileDialog, QDesktopWidget, QVBoxLayout

class MyWindow(scanner_ui.Ui_Form, QWidget):
    scanner_info_msg = pyqtSignal(str)
    def __init__(self):

        super().__init__()

        # init UI
        self.setupUi(self)
        self.ui_width = int(QDesktopWidget().availableGeometry().size().width()*0.5)
        self.ui_height = int(QDesktopWidget().availableGeometry().size().height()*0.55)
        self.resize(self.ui_width, self.ui_height)
        center_pointer = QDesktopWidget().availableGeometry().center()
        x = center_pointer.x()
        y = center_pointer.y()
        old_x, old_y, width, height = self.frameGeometry().getRect()
        self.move(int(x - width / 2), int(y - height / 2))

        # set flag off and widget translucent
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # set window blur
        self.render_shadow()
        
        # init window button signal
        self.window_btn_signal()

        # init scanner contol nidaq
        self.init_nidaq()

        # init signal
        self.scanner_signal()
        # Init scanner setup info ui
        self.scanner_info_ui()
        self.scanner_info_msg.connect(self.scanner_slot)
    def scanner_info_ui(self):

        self.scanner_msg.setWordWrap(True)  # 自动换行
        self.scanner_msg.setAlignment(Qt.AlignTop)  # 靠上

        # 用于存放消息
        self.scanner_msg_history = []
    def scanner_slot(self, msg):

        self.scanner_msg_history.append(msg)
        self.scanner_msg.setText("<br>".join(self.scanner_msg_history))
        self.scanner_msg.resize(700, self.scanner_msg.frameSize().height() + 20)
        self.scanner_msg.repaint()  # 更新内容，如果不更新可能没有显示新内容  
    def init_nidaq(self):
        self.x_task = nidaqmx.Task()
        self.x_task.ao_channels.add_ao_voltage_chan("cDAQ1Mod1/ao0", min_val=-1.0, max_val=6.0)
        self.y_task = nidaqmx.Task()
        self.y_task.ao_channels.add_ao_voltage_chan("cDAQ1Mod1/ao1", min_val=-1.0, max_val=6.0)

        self.scanner_scroll.verticalScrollBar().rangeChanged.connect(
            lambda: self.scanner_scroll.verticalScrollBar().setValue(
                self.scanner_scroll.verticalScrollBar().maximum()
            )
        )
    def scanner_signal(self):
        self.x_move_tbtn.clicked.connect(self.x_moveto)
        self.x_voltage.editingFinished.connect(self.x_moveto)
        self.y_move_tbtn.clicked.connect(self.y_moveto)
        self.y_voltage.editingFinished.connect(self.y_moveto)
        self.y_plus_btn.clicked.connect(self.y_plus)
        self.y_minus_btn.clicked.connect(self.y_minus)
        self.x_plus_btn.clicked.connect(self.x_plus)
        self.x_minus_btn.clicked.connect(self.x_minus)
    def y_plus(self):
        y_position = float(self.y_voltage.value())/20
        step = float(self.step_voltage_spbx.value())/20
        target_position = y_position + step
        self.scanner_info_msg.emit('current position '+str(target_position*20))
        self.y_task.write(target_position)
        self.y_voltage.setValue(target_position*20)
    def y_minus(self):
        y_position = float(self.y_voltage.value())/20
        step = float(self.step_voltage_spbx.value())/20
        target_position = y_position - step
        self.scanner_info_msg.emit('current position '+str(target_position*20))
        self.y_task.write(target_position)
        self.y_voltage.setValue(target_position*20)
    def x_plus(self):
        x_position = float(self.x_voltage.value())/20
        step = float(self.step_voltage_spbx.value())/20
        target_position = x_position + step
        self.scanner_info_msg.emit('current position '+str(target_position*20))
        self.x_task.write(target_position)
        self.x_voltage.setValue(target_position*20)
    def x_minus(self):
        x_position = float(self.x_voltage.value())/20
        step = float(self.step_voltage_spbx.value())/20
        target_position = x_position - step
        self.scanner_info_msg.emit('current position '+str(target_position*20))
        self.x_task.write(target_position)
        self.x_voltage.setValue(target_position*20)
    def x_moveto(self):
        x_pos = float(self.x_voltage.value())/20
        self.x_task.write(x_pos)
    def y_moveto(self):
        y_pos = float(self.y_voltage.value())/20
        self.y_task.write(y_pos)
    '''Set window ui'''
    def window_btn_signal(self):
        # window button sigmal
        self.close_btn.clicked.connect(self.close)
        self.max_btn.clicked.connect(self.maxornorm)
        self.min_btn.clicked.connect(self.showMinimized)
        
    #create window blur
    def render_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)  # 偏移
        self.shadow.setBlurRadius(30)  # 阴影半径
        self.shadow.setColor(QColor(128, 128, 255))  # 阴影颜色
        self.mainwidget.setGraphicsEffect(self.shadow)  # 将设置套用到widget窗口中

    def maxornorm(self):
        if self.isMaximized():
            self.showNormal()
            self.norm_icon = QIcon()
            self.norm_icon.addPixmap(QPixmap(":/my_icons/images/icons/max.svg"), QIcon.Normal, QIcon.Off)
            self.max_btn.setIcon(self.norm_icon)
        else:
            self.showMaximized()
            self.max_icon = QIcon()
            self.max_icon.addPixmap(QPixmap(":/my_icons/images/icons/norm.svg"), QIcon.Normal, QIcon.Off)
            self.max_btn.setIcon(self.max_icon)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = QPoint
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 更改鼠标图标
        
    def mouseMoveEvent(self, QMouseEvent):
        m_position = QPoint
        m_position = QMouseEvent.globalPos() - self.pos()
        width = QDesktopWidget().availableGeometry().size().width()
        height = QDesktopWidget().availableGeometry().size().height()
        if m_position.x() < width*0.7 and m_position.y() < height*0.06:
            self.m_flag = True
            if Qt.LeftButton and self.m_flag:                
                pos_x = int(self.m_Position.x())
                pos_y = int(self.m_Position.y())
                if pos_x < width*0.7 and pos_y < height*0.06:           
                    self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
                    QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    def closeEvent(self, event):
        self.x_task.write(0.0)
        self.y_task.write(0.0)
        self.x_task.close()
        self.y_task.close()
    
if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    app.exec()

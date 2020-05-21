import numpy as np
import socket
import cv2
import pickle
from PyQt5.QtCore import QThread, pyqtSignal
from time import sleep
import yolov3_keras
import ssdmobilenetv2lite
import time
import io
import asyncio
import select
import re
from configparser import ConfigParser 
import time
from websocket import create_connection

udpServerAddr = ('255.255.255.255', 6868) # replace with your network address, it usually 192.168.1.255 (255 in this case means broadcast)

RECV_BUFF_SIZE = 8192*8
HEADER_SIZE = 4
DEBUG = False

# Subclassing QThread
# http://qt-project.org/doc/latest/qthread.html
class ImageThread(QThread):

  new_image = pyqtSignal()
  stop_signal = pyqtSignal()
  pause_signal = pyqtSignal()
  resume_signal = pyqtSignal()

  def __init__(self):
    QThread.__init__(self)
    self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.udp_socket.settimeout(1)
    self.udp_socket.bind(("0.0.0.0",12345))
    self.bufferSize = RECV_BUFF_SIZE
    self.isStop = False
    self.isPause = False
    self.stop_signal.connect(self.requestStop)
    self.pause_signal.connect(self.requestPause)
    self.resume_signal.connect(self.requestResume)
    # self.delta = 0
    self.initRequestCnt = 5
    self.frame = None

    configure = ConfigParser() 
    print (configure.read('setting.ini'))
    print ("Sections : ", configure.sections()) 
    if(int(configure.get('system','GPU')) == 1):
      self.model = yolov3_keras.yolo3_keras_model('./yolov3.h5')
    else:
      self.model = ssdmobilenetv2lite.ssdMobilenetV2('./ssdlite_mobilenet_v2_quantized.tflite')

  def requestStop(self):
    while self.initRequestCnt > 0:
      self.udp_socket.sendto(b'stop', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.isStop = True

  def requestPause(self):
    while self.initRequestCnt > 0:
      self.udp_socket.sendto(b'stop', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.isPause = True

  def requestResume(self):
    while self.initRequestCnt > 0:
      self.udp_socket.sendto(b'stream', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.isPause = False

  def requestLeft(self, val):
    print('[DEBUG]ImageThread request left {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.udp_socket.sendto(b'leon', udpServerAddr)
      else:
        self.udp_socket.sendto(b'leoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def requestRight(self, val):
    print('[DEBUG]ImageThread request right {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.udp_socket.sendto(b'rion', udpServerAddr)
      else:
        self.udp_socket.sendto(b'rioff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def requestFw(self, val):
    print('[DEBUG]ImageThread request backward {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.udp_socket.sendto(b'bwon', udpServerAddr)
      else:
        self.udp_socket.sendto(b'bwoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    
  def requestBw(self, val):
    print('[DEBUG]ImageThread request forward {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.udp_socket.sendto(b'fwon', udpServerAddr)
      else:
        self.udp_socket.sendto(b'fwoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def run(self):
    ws = None
    while self.initRequestCnt > 0:
      try:
          self.udp_socket.sendto(b'whoami', udpServerAddr)
          data, server = self.udp_socket.recvfrom(1024)
          ws = create_connection("ws://{}:86/websocket".format(server[0]))
          break
      except socket.timeout:
          self.initRequestCnt -= 1
          print('REQUEST TIMED OUT')
    self.initRequestCnt = 5
    cnt = 0

    frame_data = b''

    start_time = time.time()

    while not self.isStop:
      if self.isPause:
            time.sleep(0.1)
            continue
      frame_data =  ws.recv()
      frame_stream = io.BytesIO(frame_data)
      frame_stream.seek(0)
      file_bytes = np.asarray(bytearray(frame_stream.read()), dtype=np.uint8)
      frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
      if frame is not None:
        self.frame = frame[:,:,::-1].copy()
        self.frame, boxes = self.model.do_inference(self.frame)
        self.fps = 1/(time.time() - start_time)
        self.fps = round(self.fps,2)
        print ("---receive and processing frame {} time: {} seconds ---".format(cnt, (time.time() - start_time)))
        start_time = time.time()

        self.new_image.emit()

        if DEBUG:
          cv2.imwrite('test_{}.jpg'.format(0), self.frame[:,:,::-1])

    if ws is not None:
      ws.close()
    self.udp_socket.close()
    print('remote exit')
  
  def getImage(self):
    return self.frame, self.fps

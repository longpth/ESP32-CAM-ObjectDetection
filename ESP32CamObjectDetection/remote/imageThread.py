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

# udpServerAddr   = ("127.0.0.1", 6868)
udpServerAddr = ('192.168.1.255', 6868) # replace with your network address, it usually 192.168.1.255 (255 in this case means broadcast)
myTCPServerAddr = ('', 6868)

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
    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.client_socket.settimeout(1)
    self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_sock.bind(myTCPServerAddr)
    self.server_sock.listen(5)
    self.server_sock.settimeout(2)
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
      self.client_socket.sendto(b'stop', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.server_sock.shutdown(socket.SHUT_WR)
    self.isStop = True

  def requestPause(self):
    while self.initRequestCnt > 0:
      self.client_socket.sendto(b'stop', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.isPause = True

  def requestResume(self):
    while self.initRequestCnt > 0:
      self.client_socket.sendto(b'stream', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    self.isPause = False

  def requestLeft(self, val):
    print('[DEBUG]ImageThread request left {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.client_socket.sendto(b'leon', udpServerAddr)
      else:
        self.client_socket.sendto(b'leoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def requestRight(self, val):
    print('[DEBUG]ImageThread request right {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.client_socket.sendto(b'rion', udpServerAddr)
      else:
        self.client_socket.sendto(b'rioff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def requestFw(self, val):
    print('[DEBUG]ImageThread request backward {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.client_socket.sendto(b'bwon', udpServerAddr)
      else:
        self.client_socket.sendto(b'bwoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    
  def requestBw(self, val):
    print('[DEBUG]ImageThread request forward {}'.format(val))
    while self.initRequestCnt > 0:
      if val:
        self.client_socket.sendto(b'fwon', udpServerAddr)
      else:
        self.client_socket.sendto(b'fwoff', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5

  def run(self):

    while self.initRequestCnt > 0:
      self.client_socket.sendto(b'stream', udpServerAddr)
      self.initRequestCnt -= 1
    self.initRequestCnt = 5
    cnt = 0

    read_list = [self.server_sock]

    frame_data = b''

    start_time = time.time()

    while not self.isStop:
      if self.isPause:
            time.sleep(0.1)
            continue
      readable, writable, errored = select.select(read_list, [], [])
      for s in readable:
        if s is self.server_sock:
            # print(s)
            client_socket, address = self.server_sock.accept()
            read_list.append(client_socket)
            print ("Connection from {}".format(address))
        else:
            data = s.recv(2048)
            try:
              if data:
                if b'len:' in data:
                  idx_len = re.search(b'len:',data).span()[1]
                  # print(idx_len)
                  # print(data[idx_len:re.search(b'len:',data).span()[0]+10])
                  img_size = int(data[idx_len:idx_len+6].decode("utf-8"))
                  # print("image size: {}".format(img_size))

                  if idx_len != 4:
                    frame_data += data[0:idx_len-4]

                  frame_stream = io.BytesIO(frame_data)
                  frame_stream.seek(0)
                  file_bytes = np.asarray(bytearray(frame_stream.read()), dtype=np.uint8)
                  frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                  if frame is not None:
                    self.frame = frame[:,:,::-1].copy()
                    self.frame, boxes = self.model.do_inference(self.frame)
                    self.fps = 1/(time.time() - start_time)
                    self.fps = round(self.fps,2)
                    # cv2.putText( self.frame, 'fps: '+str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), lineType=cv2.LINE_AA)
                    # draw a box over the image
                    # frame_h, frame_w,_ = self.frame.shape
                    # lineThickness = 2
                    # color = (0,0,255)
                    # cv2.line(self.frame, (10, 10), (50, 10), color, lineThickness)
                    # cv2.line(self.frame, (10, 10), (10, 50), color, lineThickness)

                    # cv2.line(self.frame, (10, frame_h-10), (10, frame_h-50), color, lineThickness)
                    # cv2.line(self.frame, (10, frame_h-10), (50, frame_h-10), color, lineThickness)
                    
                    # cv2.line(self.frame, (frame_w-10, 10), (frame_w-50, 10), color, lineThickness)
                    # cv2.line(self.frame, (frame_w-10, 10), (frame_w-10, 50), color, lineThickness)
                    
                    # cv2.line(self.frame, (frame_w-10, frame_h-10), (frame_w-10, frame_h-50), color, lineThickness)
                    # cv2.line(self.frame, (frame_w-10, frame_h-10), (frame_w-50, frame_h-10), color, lineThickness)

                    print("---receive and processing frame {} time: {} seconds ---".format(cnt, (time.time() - start_time)))
                    start_time = time.time()

                    self.new_image.emit()

                    if DEBUG:
                      cv2.imwrite('test_{}.jpg'.format(0), self.frame[:,:,::-1])

                  frame_data = data[idx_len+6:]
                else:
                  frame_data += data

            except Exception as e: 
              print('exception {}'.format(e))

    self.client_socket.close()
    self.server_sock.close()
    print('remote exit')
  
  def getImage(self):
    return self.frame, self.fps

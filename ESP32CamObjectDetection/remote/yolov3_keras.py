import numpy as np
import cv2
import keras
import utils
import glob
import os
from keras.models import load_model
import time
import tensorflow as tf

from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.7
set_session(tf.Session(config=config))

labelsCoco = [
            "person",
            "bicycle",
            "car",
            "motorbike",
            "aeroplane",
            "bus",
            "train",
            "truck",
            "boat",
            "traffic_light",
            "fire_hydrant",
            "stop_sign",
            "parking_meter",
            "bench",
            "bird",
            "cat",
            "dog",
            "horse",
            "sheep",
            "cow",
            "elephant",
            "bear",
            "zebra",
            "giraffe",
            "backpack",
            "umbrella",
            "handbag",
            "tie",
            "suitcase",
            "frisbee",
            "skis",
            "snowboard",
            "sports_ball",
            "kite",
            "baseball_bat",
            "baseball_glove",
            "skateboard",
            "surfboard",
            "tennis_racket",
            "bottle",
            "wine_glass",
            "cup",
            "fork",
            "knife",
            "spoon",
            "bowl",
            "banana",
            "apple",
            "sandwich",
            "orange",
            "broccoli",
            "carrot",
            "hot_dog",
            "pizza",
            "donut",
            "cake",
            "chair",
            "sofa",
            "pottedplant",
            "bed",
            "diningtable",
            "toilet",
            "tvmonitor",
            "laptop",
            "mouse",
            "remote",
            "keyboard",
            "cell_phone",
            "microwave",
            "oven",
            "toaster",
            "sink",
            "refrigerator",
            "book",
            "clock",
            "vase",
            "scissors",
            "teddy_bear",
            "hair_drier",
            "toothbrush"
            ]

# anchors = [[81,82,  135,169,  344,319], [23,27,  37,58,  81,82]] #tiny
anchors = [[116,90, 156,198, 373,326], [30,61, 62,45, 59,119], [10,13, 16,30, 33,23]]

obj_threshold = 0.5
nms_threshold = 0.3
# network size
net_w, net_h = 416,416

class yolo3_keras_model():

  def __init__(self, model_path):
    self.model = load_model(model_path)
    self.model._make_predict_function()
    self.model.summary()

  def draw_boxes(self, boxes, img):
    # draw boxes onto image
    for box in boxes:
      if box.get_score() > 0:
        cv2.rectangle( img, (box.xmin, box.ymin), (box.xmax, box.ymax),  (0,255,0),3)
        cv2.rectangle( img, (box.xmin, box.ymin), (box.xmin+130, box.ymin+40), (0,255,0),-1)
        cv2.putText( img, labelsCoco[box.get_label()], (box.get_box()[0]+10, box.get_box()[1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), lineType=cv2.LINE_AA)
    return img

  def do_inference(self, img):

    # image size
    ih, iw, _ = img.shape

    # preprocess input image
    img_rgb = img[:,:,::-1]
    image_data = utils.preprocess_input(img_rgb, net_w, net_h)

    start_time = time.time()
    # prediction
    out = self.model.predict(image_data)
    print("---cnn inference time: {} seconds ---".format((time.time() - start_time)))
    out[0] = np.squeeze(out[0])
    out[1] = np.squeeze(out[1])
    out[2] = np.squeeze(out[2])

    boxes = list()
    # for i in range(2): #tiny
    for i in range(3):
      # decode the output of the network
      boxes += utils.decode_netout(out[i], anchors[i], obj_threshold, 416, 416)

    boxes = utils.correct_yolo_boxes(boxes, ih, iw, net_w, net_h)

    boxes = utils.do_nms(boxes, nms_threshold)

    # draw boxes onto image
    self.draw_boxes(boxes, img)

    return img, boxes

# def main():
#   model = yolo3_keras_model('./yolov3.h5')

#   img_paths = glob.glob(os.path.join('/media/p4f/My Passport/02.dataset/coco/val2017','*.jpg'))

#   for img_path in img_paths:
#     print('inference on image: {}'.format(img_path))
#     img = cv2.imread(img_path)
#     image, boxes = model.do_inference(img)
#     cv2.imshow('result', image)
#     key = cv2.waitKey(0)
#     if key == 27:
#       break

def main():
  model = yolo3_keras_model('./yolov3.h5')

  cap = cv2.VideoCapture(0)
  ret, img = cap.read()
  while ret:
    start_time = time.time()
    image, boxes = model.do_inference(img)
    print("--- %s seconds ---" % (time.time() - start_time))
    cv2.imshow('result', image)
    key = cv2.waitKey(1)
    if key == 27:
      break
    ret, img = cap.read()

if __name__ == '__main__':
  main()


import cv2
import os
import numpy as np
import tensorflow as tf
from tensorflow.lite.python import interpreter as interpreter_wrapper
import time

tf.config.threading.set_inter_op_parallelism_threads(
    4
)

IMAGE_MEAN = 128.0
IMAGE_STD = 128.0

labelsSSD = [
          "person",
          "bicycle",
          "car",
          "motorcycle",
          "airplane",
          "bus",
          "train",
          "truck",
          "boat",
          "traffic light",
          "fire hydrant",
          "street sign",
          "stop sign",
          "parking meter",
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
          "hat",
          "backpack",
          "umbrella",
          "shoe",
          "eye glasses",
          "handbag",
          "tie",
          "suitcase",
          "frisbee",
          "skis",
          "snowboard",
          "sports ball",
          "kite",
          "baseball bat",
          "baseball glove",
          "skateboard",
          "surfboard",
          "tennis racket",
          "bottle",
          "plate",
          "wine glass",
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
          "hot dog",
          "pizza",
          "donut",
          "cake",
          "chair",
          "couch",
          "potted plant",
          "bed",
          "mirror",
          "dining table",
          "window",
          "desk",
          "toilet",
          "door",
          "tv",
          "laptop",
          "mouse",
          "remote",
          "keyboard",
          "cell phone",
          "microwave",
          "oven",
          "toaster",
          "sink",
          "refrigerator",
          "blender",
          "book",
          "clock",
          "vase",
          "scissors",
          "teddy bear",
          "hair drier",
          "toothbrush",
          "hair brush"
]

class ssdMobilenetV2():
  def __init__(self, model_path):
    self.interpreter = interpreter_wrapper.Interpreter(model_path=model_path)
    self.interpreter.allocate_tensors()

    self.input_details  = self.interpreter.get_input_details()
    self.output_details = self.interpreter.get_output_details()

    print(self.input_details)
    print(self.output_details)

  def do_inference(self, img):
    orig = img.copy()
    resized_image = cv2.resize(orig, (300, 300), cv2.INTER_AREA)

    if self.input_details[0]['dtype'] == np.float32:
      resized_image = resized_image.astype('float32')
      mean_image = np.full((300,300,3), IMAGE_MEAN, dtype='float32')
      resized_image = (resized_image - mean_image)/IMAGE_STD

    resized_image = resized_image[np.newaxis,...]

    start_time = time.time()
    self.interpreter.set_tensor(self.input_details[0]['index'], resized_image)
    self.interpreter.invoke()
    print("---cnn inference time: {} seconds ---".format((time.time() - start_time)))

    output_data0 = self.interpreter.get_tensor(self.output_details[0]['index'])
    output_data1 = self.interpreter.get_tensor(self.output_details[1]['index'])
    output_data2 = self.interpreter.get_tensor(self.output_details[2]['index'])

    output_data0 = np.squeeze(output_data0)
    output_data1 = np.squeeze(output_data1)
    output_data2 = np.squeeze(output_data2)
    detection_boxes = output_data0

    indices = np.where(output_data2>=0.3)

    detection_boxes = detection_boxes[indices]
    detection_boxes [:, 0] = detection_boxes [:, 0]*orig.shape[0]
    detection_boxes [:, 1] = detection_boxes [:, 1]*orig.shape[1]
    detection_boxes [:, 2] = detection_boxes [:, 2]*orig.shape[0]
    detection_boxes [:, 3] = detection_boxes [:, 3]*orig.shape[1]

    cnt = 0
    for detection_box in detection_boxes:
      print('{} {} {} {} {}'.format(labelsSSD[int(output_data1[cnt])], detection_box[1], detection_box[0], detection_box[3], detection_box[2]))
      cv2.rectangle( orig, (detection_box[1],detection_box[0]), (detection_box[3],detection_box[2]), (0,255,0),3)
      cv2.rectangle( orig, (int(detection_box[1]), int(detection_box[0])), (int(detection_box[1]+130), int(detection_box[0]+40)), (0,255,0),-1)
      cv2.putText( orig, labelsSSD[int(output_data1[cnt])], (int(detection_box[1]+10), int(detection_box[0]+30)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), lineType=cv2.LINE_AA)
      cnt += 1

    return orig, detection_boxes

def main():

  # model_path = './ssdlite_mobilenet_v2.tflite'
  model_path = './ssdlite_mobilenet_v2_quantized.tflite'

  interpreter = interpreter_wrapper.Interpreter(model_path=model_path)
  interpreter.allocate_tensors()

  input_details = interpreter.get_input_details()
  output_details = interpreter.get_output_details()

  print(input_details)
  print(output_details)

  cap = cv2.VideoCapture(0)

  ret, orig = cap.read(0)

  while ret:

    resized_image = cv2.resize(orig, (300, 300), cv2.INTER_AREA)

    # print(resized_image)
    # resized_image = resized_image.astype('float32')
    # mean_image = np.full((300,300,3), IMAGE_MEAN, dtype='float32')
    # resized_image = (resized_image - mean_image)/IMAGE_STD

    resized_image = resized_image[np.newaxis,...]

    start = time.time()
    interpreter.set_tensor(input_details[0]['index'], resized_image)
    interpreter.invoke()
    end = time.time()

    output_data0 = interpreter.get_tensor(output_details[0]['index'])
    output_data1 = interpreter.get_tensor(output_details[1]['index'])
    output_data2 = interpreter.get_tensor(output_details[2]['index'])

    print(output_data0.shape)
    print(output_data1.shape)
    print(output_data2.shape)

    output_data0 = np.squeeze(output_data0)
    output_data1 = np.squeeze(output_data1)
    output_data2 = np.squeeze(output_data2)
    detection_boxes = output_data0

    indices = np.where(output_data2>=0.3)

    detection_boxes = detection_boxes[indices]
    detection_boxes [:, 0] = detection_boxes [:, 0]*orig.shape[0]
    detection_boxes [:, 1] = detection_boxes [:, 1]*orig.shape[1]
    detection_boxes [:, 2] = detection_boxes [:, 2]*orig.shape[0]
    detection_boxes [:, 3] = detection_boxes [:, 3]*orig.shape[1]

    cnt = 0
    for detection_box in detection_boxes:
      print('{} {} {} {} {}'.format(labelsSSD[int(output_data1[cnt])], detection_box[1], detection_box[0], detection_box[3], detection_box[2]))
      cv2.rectangle( orig, (detection_box[1],detection_box[0]), (detection_box[3],detection_box[2]), (255,0,0),2)
      # print(labelsSSD[int(output_data1[cnt])])
      cv2.putText( orig, labelsSSD[int(output_data1[cnt])], (int(detection_box[1]+10), int(detection_box[0]+10)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), lineType=cv2.LINE_AA)
      cnt += 1

    print("time execution {}".format(end-start))

    cv2.imshow('result', orig)
    key = cv2.waitKey(1)
    
    if key == 27:
      break

    ret, orig = cap.read(0)


if __name__ == '__main__':
    main()


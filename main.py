#!/usr/bin/env python3

"""People Counter."""
"""
 Copyright (c) 2018 Intel Corporation.
 Permission is hereby granted, free of charge, to any person obtaining
 a copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit person to whom the Software is furnished to do so, subject to
 the following conditions:
 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import sys
import time
import socket
import json
import numpy as np
import cv2

from loguru import logger
import paho.mqtt.client as mqtt
from tqdm import tqdm

from argparse import ArgumentParser
from inference import Network

# MQTT server environment variables
HOSTNAME = socket.gethostname()
IPADDRESS = socket.gethostbyname(HOSTNAME)
MQTT_HOST = IPADDRESS
MQTT_PORT = 3001
MQTT_KEEPALIVE_INTERVAL = 60


def build_argparser():
    """Parse command line arguments.

    :return: command line arguments
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        type=str,
        help="Path to an xml file with a trained model.",
    )
    parser.add_argument(
        "-i", "--input", required=True, type=str, help="Path to image or video file"
    )
    parser.add_argument(
        "-l",
        "--cpu_extension",
        required=False,
        type=str,
        default=None,
        help="MKLDNN (CPU)-targeted custom layers."
        "Absolute path to a shared library with the"
        "kernels impl.",
    )
    parser.add_argument(
        "-d",
        "--device",
        type=str,
        default="CPU",
        help="Specify the target device to infer on: "
        "CPU, GPU, FPGA or MYRIAD is acceptable. Sample "
        "will look for a suitable plugin for device "
        "specified (CPU by default)",
    )
    parser.add_argument(
        "-pt",
        "--prob_threshold",
        type=float,
        default=0.5,
        help="Probability threshold for detections filtering" "(0.5 by default)",
    )
    parser.add_argument(
        "--out", action="store_true", help="Write video to file.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show output on screen [debugging].",
    )

    return parser


def connect_mqtt():
    client = mqtt.Client()
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        return client
    except Exception as err:
        logger.error(f"MQTT client -> {str(err)}")


def categories_list():
    # https://github.com/opencv/opencv/blob/master/samples/data/dnn/object_detection_classes_coco.txt
    return [
        "null",
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
    ]


def draw_boxes(frame, result, prob_threshold, width, height):
    """Draw bounding boxes onto the frame."""
    loc = 10
    count = 0
    # As per: https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco.md#converted-model-1
    for box in result[0][0]:  # Output shape is 1x1x100x7
        label = categories_list()[int(box[1])]
        conf = box[2]
        if conf >= prob_threshold:
            xmin = int(box[3] * width)
            ymin = int(box[4] * height)
            xmax = int(box[5] * width)
            ymax = int(box[6] * height)
            _y = ymax - loc if ymax - loc > loc else ymax + loc

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 1)

            cv2.putText(
                frame,
                f"{label.title()}: {conf *100:.2f}%",
                (xmin, _y),
                cv2.FONT_HERSHEY_COMPLEX,
                fontScale=0.5,
                color=(127, 255, 127),
                thickness=1,
            )
            count += 1
    return frame, count


def process_frame(frame, height, width, data_layout=(2, 0, 1)):
    """Helper function for processing frame"""
    p_frame = cv2.resize(frame, (width, height))
    gray = cv2.cvtColor(p_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Change data layout from HWC to CHW
    p_frame = p_frame.transpose(data_layout)
    p_frame = p_frame.reshape(1, *p_frame.shape)
    return p_frame, gray


def testIntersectionIn(x, y):
    res = -450 * x + 400 * y + 157500
    # print(res, (res >= -550) and (res < 550))
    if (res >= -550) and (res < 550):
        return True


def testIntersectionOut(x, y):
    res = -450 * x + 400 * y + 180000
    if (res >= -550) and (res <= 550):
        return True


def infer_on_stream(args, client):
    """
    Initialize the inference network, stream video to network,
    and output stats and video.

    :param args: Command line arguments parsed by `build_argparser()`
    :param client: MQTT client
    :return: None
    """
    # Initialise the class
    infer_network = Network()
    # Set Probability threshold for detections
    prob_threshold = args.prob_threshold

    ### TODO: Load the model through `infer_network` ###
    infer_network.load_model(
        model_xml=args.model,
        device=args.device,
        cpu_extension=args.cpu_extension if args.cpu_extension else None,
    )
    ### TODO: Handle the input stream ###
    logger.info("Processing video...")
    writer = None
    stream = cv2.VideoCapture(args.input)
    stream.open(args.input)
    # Grab the shape of the input
    orig_width = int(stream.get(3))
    orig_height = int(stream.get(4))

    if args.out:
        # Create a video writer for the output video
        # The second argument should be `cv2.VideoWriter_fourcc('M','J','P','G')`
        # on Mac, and `0x00000021` on Linux
        logger.debug("Enabled writing output video to file.")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter("out.mp4", fourcc, 30, (orig_width, orig_height))
        length = stream.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = stream.get(cv2.CAP_PROP_FPS)
        pbar = tqdm(total=int(length - fps + 1))

    # Example: for 'ssd_mobilenet_v2_coco.xml'
    # Image, shape - 1,300,300,3, format is B,H,W,C where:
    # B - batch size
    # H - height
    # W - width
    # C - channel
    batch_size, channel, input_height, input_width = infer_network.get_input_shape()
    ### TODO: Loop until stream is over ###
    if not stream.isOpened():
        msg = "Cannot open video source!!!"
        logger.error(msg)
        raise RuntimeError(msg)

    # person detected counter.
    last_counted = 0
    total_count = 0
    firstFrame = None
    textIn = 0
    textOut = 0

    # Regions of Interest
    x0_blue, y0_blue = int(orig_width // 2.3), 0
    x1_blue, y1_blue = int(orig_width // 2.3), orig_height
    x0_red, y0_red = int(orig_width // 2.3) + 250, 0
    x1_red, y1_red = int(orig_width // 2.3) + 250, orig_height

    while stream.isOpened():
        ### TODO: Read from the video capture ###
        # Grab the next stream.
        (grabbed, frame) = stream.read()
        # If the frame was not grabbed, then we might have reached end of steam,
        # then break
        if not grabbed:
            break

        p_frame, gray = process_frame(frame, input_width, input_height)

        # if the first frame is None, initialize it
        if firstFrame is None:
            firstFrame = gray
            continue

        # compute the absolute difference between the current frame and
        # first frame
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 50, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        # Taking a matrix of size 10 as the kernel
        kernel = np.ones((10, 10), np.uint8)

        thresh = cv2.dilate(thresh, kernel, iterations=2)
        contours = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )[0]
        start_infer = time.time()
        infer_network.exec_net(p_frame)
        if infer_network.wait() == 0:
            result = infer_network.get_output()
            end_infer = time.time() - start_infer
            cv2.line(
                frame, (x0_blue, y0_blue), (x1_blue, y1_blue), (250, 0, 1), 2,
            )  # blue line
            cv2.line(
                frame, (x0_red, y0_red), (x1_red, y1_red), (0, 0, 255), 2,
            )  # red line
            if contours:
                for cnt in contours:
                    # if the contour is too small, ignore it
                    if cv2.contourArea(cnt) < 6000:
                        continue
                    # compute the bounding box for the contour, draw it on the frame,
                    # and update the text
                    (x, y, w, h) = cv2.boundingRect(cnt)
                    # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # import IPython; globals().update(locals()); IPython.embed(header='Python Debugger')
                    rectagleCenterPont = (
                        (orig_width + x) // 2,
                        (y - h + orig_height) // 2,
                    )
                    # print(rectagleCenterPont)
                    cv2.circle(frame, rectagleCenterPont, 5, (0, 0, 255), 5)

                    if testIntersectionIn(*rectagleCenterPont):
                        # if testIntersectionIn((x + w), (y + y + h)):
                        textIn += 1

                    # if testIntersectionOut((x + x + w), (y + y + h)):
                    if testIntersectionOut(*rectagleCenterPont):
                        textOut += 1
                    # print(textIn)
                    # print(textOut)
            cv2.putText(
                frame,
                "In: {}".format(str(textIn)),
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                "Out: {}".format(str(textOut)),
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2,
            )

            # Draw the boxes onto the input
            out_frame, current_count = draw_boxes(
                frame, result, prob_threshold, orig_width, orig_height
            )
            message = f"Inference time: {end_infer*1000:.2f}ms"
            cv2.putText(
                frame, message, (20, 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1
            )
            if args.out:
                pbar.update(1)
                out.write(frame)
            # Check when a person enters the video the first time.
            if current_count > last_counted:
                detected_start = time.time()
                total_count = total_count + current_count - last_counted
                # print(total_count)

            # Check how long the person is in the video
            if current_count < last_counted:
                detected_end = time.time() - detected_start
                # print(detected_end)
            last_counted = current_count
        ### TODO: Extract any desired stats from the results ###

        ### TODO: Calculate and send relevant information on ###
        ### current_count, total_count and duration to the MQTT server ###
        ### Topic "person": keys of "count" and "total" ###
        ### Topic "person/duration": key of "duration" ###

        ### TODO: Send the frame to the FFMPEG server ###

        if args.debug:
            cv2.imshow("Gray Frame", gray)
            cv2.imshow("Contour Frame", thresh)
            cv2.imshow("Frame", frame)

        key = cv2.waitKey(1) & 0xFF

        # # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    # Release the out writer, capture, and destroy any OpenCV windows
    if args.out:
        pbar.close()
        out.release()
    stream.release()
    cv2.destroyAllWindows()
    if client:
        client.disconnect()


def main():
    """
    Load the network and parse the output.

    :return: None
    """
    # Grab command line args
    args = build_argparser().parse_args()
    # Connect to the MQTT server
    client = connect_mqtt()
    # Perform inference on the input stream
    infer_on_stream(args, client)


if __name__ == "__main__":

    main()

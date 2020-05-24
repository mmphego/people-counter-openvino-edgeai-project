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
import json
import os
import socket
import sys
import time

from argparse import ArgumentParser

import cv2
import matplotlib.pyplot as plt
import numpy as np
import paho.mqtt.client as mqtt

from inference import Network
from loguru import logger
from tqdm import tqdm

# MQTT server environment variables
HOSTNAME = socket.gethostname()
IPADDRESS = socket.gethostbyname(HOSTNAME)
MQTT_HOST = IPADDRESS
MQTT_PORT = 3001
MQTT_KEEPALIVE_INTERVAL = 60
TIMEOUT = 60

# person detected counter.
last_count = 0
total_count = 0
firstFrame = None
textIn = 0
textOut = 0

average_infer_time = []


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
        "--ffmpeg", action="store_true", help="Flush video to FFMPEG.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show output on screen [debugging].",
    )

    return parser


def connect_mqtt():
    client = mqtt.Client()
    try:
        client.connect(MQTT_HOST, MQTT_PORT, TIMEOUT)
    except Exception as err:
        MQTT_HOST = "mosca-server"
        try:
            logger.warn(
                f"Failed to connect to {MQTT_HOST}:{MQTT_PORT}, trying docker container"
                f" MQTT server on {MQTT_HOST}:{MQTT_PORT}")
            client.connect(MQTT_HOST, MQTT_PORT, TIMEOUT)
        except Exception as err:
            logger.error(f"Failed to connect to {MQTT_HOST}:{MQTT_PORT}")
            return

    logger.info(f"Connected to MQTT server on {MQTT_HOST}:{MQTT_PORT}")
    return client

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


def plot_frame(frame):
    """Helper function for finding image coordinates/px"""
    img = frame[:, :, 0]
    plt.plot(img)
    plt.imshow(img)
    plt.show()


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
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Change data layout from HWC to CHW
    p_frame = p_frame.transpose(data_layout)
    p_frame = p_frame.reshape(1, *p_frame.shape)
    return p_frame, gray


def testIntersectionIn(x, y):
    pass


def testIntersectionOut(x, y):
    pass


def find_intersections(
    contours, frame, x0, y0, x1, y1,
):
    global textIn, textOut

    if contours:
        for cnt in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(cnt) < 12000:
                continue
            cv2.line(
                frame, x0, y0, (250, 0, 1), 2,
            )  # blue line
            cv2.line(
                frame, x1, y1, (0, 0, 255), 2,
            )  # red line

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (xmin, ymin, xmax, ymax) = cv2.boundingRect(cnt)

            cv2.rectangle(
                frame, (xmin, ymin), (xmin + xmax, ymin + ymax), (0, 255, 0), 2
            )

            rectagleCenterPont = ((2 * xmin + xmax) // 2, (2 * ymin + ymax) // 2)

            cv2.circle(frame, rectagleCenterPont, 1, (0, 0, 255), 1)

            if testIntersectionIn(xmin, ymax):
                textIn += 1

            if testIntersectionOut(xmin, ymax):
                textOut += 1

    return textIn, textOut


def infer_on_stream(args, client):
    """
    Initialize the inference network, stream video to network,
    and output stats and video.

    :param args: Command line arguments parsed by `build_argparser()`
    :param client: MQTT client
    :return: None
    """
    global firstFrame, last_count, total_count, average_infer_time
    # Initialise the class
    infer_network = Network()
    # Set Probability threshold for detections
    prob_threshold = args.prob_threshold

    ### TODO: Load the model through `infer_network` ###
    try:
        infer_network.load_model(
        model_xml=args.model,
        device=args.device,
        cpu_extension=args.cpu_extension if args.cpu_extension else None,
        )
    except Exception:
        logger.exception("Failed to load the model")
        raise
    video_file = args.input
    writer = None
    logger.info(f"Processing video: {video_file}...")
    stream = cv2.VideoCapture(video_file)
    stream.open(video_file)

    # Grab the shape of the input
    orig_width = int(stream.get(3))
    orig_height = int(stream.get(4))

    # Regions of Interest
    blue_line_start = orig_width + 150, orig_height - 50
    blue_line_end = 0, 100
    red_line_start = orig_width, orig_height - 100
    red_line_end = 200, 0

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

    if not stream.isOpened():
        msg = "Cannot open video source!!!"
        logger.error(msg)
        raise RuntimeError(msg)

    while stream.isOpened():
        ### TODO: Read from the video capture ###
        # Grab the next stream.
        (grabbed, frame) = stream.read()
        # If the frame was not grabbed, then we might have reached end of steam,
        # then break
        if not grabbed:
            break

        p_frame, gray = process_frame(frame, input_height, input_width)

        # if the first frame is None, initialize it
        if firstFrame is None:
            firstFrame = gray
            continue

        # compute the absolute difference between the current frame and
        # first frame
        frameDelta = cv2.absdiff(firstFrame, gray)
        _, thresh = cv2.threshold(frameDelta, 50, 255, cv2.THRESH_BINARY)
        # dilate the threshold image to fill in holes, then find contours
        # on threshold image
        # Taking a matrix of size 10 as the kernel
        kernel = np.ones((5, 5), np.uint8)

        thresh = cv2.dilate(thresh, kernel, iterations=3)
        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        start_infer = time.time()
        infer_network.exec_net(p_frame)
        if infer_network.wait() == 0:
            result = infer_network.get_output()
            end_infer = time.time() - start_infer
            average_infer_time.append(end_infer)
            message = f"Inference time: {end_infer*1000:.2f}ms"
            cv2.putText(
                frame, message, (20, 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1
            )
            # Display contour: Useful for debugging.
            # cv2.drawContours(frame, contours, -1, (0, 0, 0), 2)

            # TODO: Fix the logic of counting people going in/out of ROI
            # Possible solution:
            # Assuming that people enter from left and exit on right.
            # Create the equation for line y=mx+c where m is slope.
            # We assume y direction is going up (you'll need to inverse the sign).
            # Substitute x_person into equation to calculate y_line.
            # If y_person > y_line, then it is above the line.
            # I think a better way is to use a box around the polling station and
            # check if the person is within the box.

            # textIn, textOut = find_intersections(
            #     contours,
            #     frame,
            #     blue_line_start,
            #     blue_line_end,
            #     red_line_start,
            #     red_line_end,
            # )

            # Draw the boxes onto the input
            out_frame, current_count = draw_boxes(
                frame, result, prob_threshold, orig_width, orig_height
            )

            # Check when a person enters the video the first time.
            if current_count > last_count:
                start_time = time.time()
                total_count += current_count - last_count
                if hasattr(client, "publish"):
                    client.publish("person", json.dumps({"total": total_count}))

            if current_count < last_count:
                duration = int(time.time() - start_time)
                # Publish messages to the MQTT server
                if hasattr(client, "publish"):
                    client.publish("person/duration", json.dumps({"duration": duration}))

            if hasattr(client, "publish"):
                client.publish("person", json.dumps({"count": current_count}))
            last_count = current_count

            if args.out:
                pbar.update(1)
                out.write(frame)

        if args.debug:
            # cv2.imshow("Gray Frame", gray)
            # cv2.imshow("Contour Frame", thresh)
            cv2.imshow("Frame", frame)

        # Send frame to the ffmpeg server
        if args.ffmpeg:
            # ffserver color correction.
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            sys.stdout.buffer.write(frame)
            sys.stdout.flush()

        key = cv2.waitKey(1) & 0xFF

        # # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

    # Release the out writer, capture, and destroy any OpenCV windows
    if client:
        client.disconnect()
    if args.out:
        pbar.close()
        out.release()
    stream.release()
    cv2.destroyAllWindows()
    logger.info(
        f"Detected {total_count} people with an average inference time: "
        f"{np.mean(average_infer_time)*1000:.3f}ms using the model: "
        f"{args.model} {infer_network._model_size:.2f}MB @ "
        f"Probability {prob_threshold*100}% threshold."
    )


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
    start_time = time.time()
    infer_on_stream(args, client)
    end_time = time.time() - start_time
    logger.info(f"It took {end_time:.2f}s to complete the inference and stream.")

if __name__ == "__main__":

    main()

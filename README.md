# Deploy a People Counter App at the Edge

| Details            |              |
|-----------------------|---------------|
| Programming Language: |  [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) |
| Intel OpenVINO ToolKit: |[![OpenVINO 2020.2.120](https://img.shields.io/badge/openvino-2020.2-blue.svg)](https://software.intel.com/content/www/us/en/develop/tools/openvino-toolkit/choose-download.html)|
| Docker (Ubuntu OpenVINO pre-installed): | [mmphego/intel-openvino](https://hub.docker.com/r/mmphego/intel-openvino)|
| Hardware Used: | Intel(R) Core(TM) i7-8750H CPU @ 2.20GHz |
| Device: | CPU |
| Blog Post | [![blogpost](https://img.shields.io/badge/BlogPost-Link-brightgreen)](https://blog.mphomphego.co.za/blog/2020/06/28/How-I-deployed-a-People-Counter-App-at-the-Edge-using-Intel-OpenVINO.html) |
| Visitors | ![](https://visitor-badge.laobi.icu/badge?page_id=mmphego.people-counter-openvino-edgeai-project)|

--- 

![people-counter-python](https://user-images.githubusercontent.com/7910856/87838133-3b136d80-c896-11ea-80f4-7a88aafac6c4.gif)

## What it Does

The people counter application will demonstrate how to create a smart video IoT solution using Intel® hardware and software tools. The app will detect people in a designated area, providing the number of people in the frame, average duration of people in frame, and total count.

## How it Works

The counter will use the Inference Engine included in the Intel® Distribution of OpenVINO™ Toolkit. The model used should be able to identify people in a video frame. The app should count the number of people in the current frame, the duration that a person is in the frame (time elapsed between entering and exiting a frame) and the total count of people. It then sends the data to a local web server using the Paho MQTT Python package.

You will choose a model to use and convert it with the Model Optimizer.

![architectural diagram](./images/arch_diagram.png)

## Requirements

### Hardware

* 6th to 10th generation Intel® Core™ processor with Iris® Pro graphics or Intel® HD Graphics.
* OR use of Intel® Neural Compute Stick 2 (NCS2)
* OR Udacity classroom workspace for the related course

### Software

*   Intel® Distribution of OpenVINO™ toolkit 2019 R3 release
*   Node v6.17.1
*   Npm v3.10.10
*   CMake
*   MQTT Mosca server


## Setup

### Install Intel® Distribution of OpenVINO™ toolkit

Utilize the classroom workspace, or refer to the relevant instructions for your operating system for this step.

- [Linux/Ubuntu](./linux-setup.md)
- [Mac](./mac-setup.md)
- [Windows](./windows-setup.md)

### Install Nodejs and its dependencies

Utilize the classroom workspace, or refer to the relevant instructions for your operating system for this step.

- [Linux/Ubuntu](./linux-setup.md)
- [Mac](./mac-setup.md)
- [Windows](./windows-setup.md)

### Install npm

There are three components that need to be running in separate terminals for this application to work:

-   MQTT Mosca server
-   Node.js* Web server
-   FFmpeg server

From the main directory:

* For MQTT/Mosca server:
   ```
   cd webservice/server
   npm install
   ```

* For Web server:
  ```
  cd ../ui
  npm install
  ```
  **Note:** If any configuration errors occur in mosca server or Web server while using **npm install**, use the below commands:
   ```
   sudo npm install npm -g
   rm -rf node_modules
   npm cache clean
   npm config set registry "http://registry.npmjs.org"
   npm install
   ```

## What model to use

It is up to you to decide on what model to use for the application. You need to find a model not already converted to Intermediate Representation format (i.e. not one of the Intel® Pre-Trained Models), convert it, and utilize the converted model in your application.

Note that you may need to do additional processing of the output to handle incorrect detections, such as adjusting confidence threshold or accounting for 1-2 frames where the model fails to see a person already counted and would otherwise double count.

**If you are otherwise unable to find a suitable model after attempting and successfully converting at least three other models**, you can document in your write-up what the models were, how you converted them, and why they failed, and then utilize any of the Intel® Pre-Trained Models that may perform better.

## Run the application

Note: In order to run the app locally export the 2 envvars (See: #a-note-on-running-locally)
```bash
export CAMERA_FEED_SERVER="http://localhost:3004"
export MQTT_SERVER="ws://localhost:3002"
```

### Option 1

In order to run the application execute the following script:
```bash
bash runme.sh
```

This script with start the `mosca server`, `ffserver`, `webui` and `app` in the background - assuming that the install NPM step was followed.

### Option 2

From the main directory:

### Step 1 - Start the Mosca server

#### Docker Container

- Create a network bridge to communicate between the containers.
```bash
docker network create -d bridge openvino
```

- Build the docker container for the mosca-server.
```bash
docker build -t mmphego/mosca-server -f Dockerfile-mosca-server .
```

- Run the container while exposing port 3001 and 3002.
```bash
docker run \
-p 3002:3002 \
-p 3001:3001 \
--network="openvino" \
--name "mosca-server" \
-ti mmphego/mosca-server
```

You should see the following message, if successful:
```
Mosca server started.
```

#### Local Development
```
cd webservice/server/node-server
node ./server.js
```

You should see the following message, if successful:
```
Mosca server started.
```

### Step 2 - Start the GUI

#### Docker Container

- Build the docker container for the Web UI

```bash
docker build -t mmphego/webui -f Dockerfile-ui .
```

- Run the container while exposing port 3000.
```bash
docker run \
-p 3000:3000 \
--network="openvino" \
--name "webui" \
-ti mmphego/webui
```

You should see the following log output:
```bash
> intel-people-counter-app@0.1.0 dev /app/webservice/ui
> cross-env NODE_ENV=development webpack-dev-server --history-api-fallback --watch --hot --inline

Project is running at http://0.0.0.0:3000/

webpack: Compiled successfully.
```

#### Local Development
Open new terminal and run below commands.
```
cd webservice/ui
npm run dev
```

You should see the following message in the terminal.
```
webpack: Compiled successfully
```

### Step 3 - FFmpeg Server

#### Docker Container


```bash
docker run \
-p 3004:3004 \
--network="openvino" \
--name "ffmpeg-server" \
-ti mmphego/ffmpeg-server
```

You should see the following output:
```bash
Sat May 23 05:51:10 2020 FFserver started.
```

#### Local Development
Open new terminal and run the below commands.
```
wget https://github.com/vot/ffbinaries-prebuilt/releases/download/v3.4/ffserver-3.4-linux-64.zip
sudo unzip ffserver-3.4-linux-64.zip /usr/local/bin
sudo ffserver -f ./ffmpeg/server.conf
```

### Step 4 - Run the code

Open a new terminal to run the code.

#### Setup the environment

You must configure the environment to use the Intel® Distribution of OpenVINO™ toolkit one time per session by running the following command:
```
source /opt/intel/openvino/bin/setupvars.sh -pyver 3.5
```

You should also be able to run the application with Python 3.6, although newer versions of Python will not work with the app.

#### Running on the CPU

When running Intel® Distribution of OpenVINO™ toolkit Python applications on the CPU, the CPU extension library is required. This can be found at:

```
/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/
```

*Depending on whether you are using Linux or Mac, the filename will be either `libcpu_extension_sse4.so` or `libcpu_extension.dylib`, respectively.* (The Linux filename may be different if you are using a AVX architecture)

Though by default application runs on CPU, this can also be explicitly specified by ```-d CPU``` command-line argument:

```
python main.py -i resources/Pedestrian_Detect_2_1_1.mp4 -m your-model.xml -l /opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so -d CPU -pt 0.6 | ffmpeg -v warning -f rawvideo -pixel_format bgr24 -video_size 768x432 -framerate 24 -i - http://0.0.0.0:3004/fac.ffm
```
If you are in the classroom workspace, use the “Open App” button to view the output. If working locally, to see the output on a web based interface, open the link [http://0.0.0.0:3004](http://0.0.0.0:3004/) in a browser.

##### Debugging with Docker
In order to see what is going inside the docker we need to sync the displays with `--env DISPLAY=$DISPLAY` `--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"`.

```bash
docker build -t "$USER/$(basename $PWD)" .
xhost +
docker run --rm -ti \
--volume "$PWD":/app \
--env DISPLAY=$DISPLAY \
--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
 "$USER/$(basename $PWD)" \
 bash -c "source /opt/intel/openvino/bin/setupvars.sh &&python main.py -i resources/Pedestrian_Detect_2_1_1.mp4 -m models/ssd_mobilenet_v2_coco.xml"
xhost -
```

#### Running on the Intel® Neural Compute Stick

To run on the Intel® Neural Compute Stick, use the ```-d MYRIAD``` command-line argument:

```
python3.5 main.py -d MYRIAD -i resources/Pedestrian_Detect_2_1_1.mp4 -m your-model.xml -pt 0.6 | ffmpeg -v warning -f rawvideo -pixel_format bgr24 -video_size 768x432 -framerate 24 -i - http://0.0.0.0:3004/fac.ffm
```

To see the output on a web based interface, open the link [http://0.0.0.0:3004](http://0.0.0.0:3004/) in a browser.

**Note:** The Intel® Neural Compute Stick can only run FP16 models at this time. The model that is passed to the application, through the `-m <path_to_model>` command-line argument, must be of data type FP16.

#### Using a camera stream instead of a video file

To get the input video from the camera, use the `-i CAM` command-line argument. Specify the resolution of the camera using the `-video_size` command line argument.

For example:
```
python main.py -i CAM -m your-model.xml -l /opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so -d CPU -pt 0.6 | ffmpeg -v warning -f rawvideo -pixel_format bgr24 -video_size 768x432 -framerate 24 -i - http://0.0.0.0:3004/fac.ffm
```

To see the output on a web based interface, open the link [http://0.0.0.0:3004](http://0.0.0.0:3004/) in a browser.

**Note:**
User has to give `-video_size` command line argument according to the input as it is used to specify the resolution of the video or image file.

## A Note on Running Locally

The servers herein are configured to utilize the Udacity classroom workspace. As such,
to run on your local machine, you will need to change the below file:

```
webservice/ui/src/constants/constants.js
```

The `CAMERA_FEED_SERVER` and `MQTT_SERVER` both use the workspace configuration.
You can change each of these as follows:

```bash
export CAMERA_FEED_SERVER="http://localhost:3004"
export MQTT_SERVER="ws://localhost:3002"
```

## TODO

- Dockerize the application (hint: docker-compose)
- Benchmark application on various devices.
- Run VTune profiling software to find any bottlenecks.

#!/bin/bash

bash -c "ffserver -f ffmpeg/server.conf &>/dev/null &disown;"
bash -c "node webservice/server/node-server/server.js &>/dev/null &disown;"
cd webservice/ui/
bash -c "npm run dev &>/dev/null &disown;"
cd -
source /opt/intel/openvino/bin/setupvars.sh -pyver 3.5
python main_udacity.py \
-i resources/Pedestrian_Detect_2_1_1.mp4 \
-m models/person-detection-retail-0013.xml \
-l cpu_ext/libcpu_extension_sse4.so \
--ffmpeg \
| ffmpeg \
-v warning \
-f rawvideo \
-pixel_format bgr24 \
-video_size 768x432 \
-framerate 24 \
-i - http://0.0.0.0:3004/fac.ffm

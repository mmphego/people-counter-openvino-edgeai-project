# Usage:
# docker build -t "$USER/$(basename $PWD)" .
# docker run --rm -ti -v "$PWD":/app "$USER/$(basename $PWD)" \
#    bash -c "source /opt/intel/openvino/bin/setupvars.sh && python3 main.py -h"

FROM mmphego/intel-openvino

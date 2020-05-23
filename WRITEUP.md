
# Project Write-Up

This project was made as one of the requirements in order to obtain [Intel(R) Edge AI for IoT Developers Nanodegree program at Udacity](https://www.udacity.com/course/intel-edge-ai-for-iot-developers-nanodegree--nd131). In this Write Up, I will explain some concepts related with OpenVINO usage and some considerations from the user side.

## Explaining Custom Layers

When loading a model inside an OpenVINO application, chances are that the model requires some operations not supported by default OpenVINO library (operations like especial activation functions, loss functions, etc). This could create situations where is not possible for the Model Optimizer to create an appropriate direct Intermediate Representation.

In that case, OpenVINO offers different options depending on model original framework (TensorFlow, Caffe, MXNet, etc), available devices and user preferences to handle those not recognized operations as Custom Layers.

At the moment the Model Optimizer tries to convert a model, it will give more relevance to preserve any defined Custom Layer, which means that if a layer is defined as custom (with some internal logic), it will be used even if such layer is already supported. The simplified work-flow is as follows:

- When a model operation is loaded, will check first if it is defined as a Custom Layer, depending of the framework, this could be either the operation is already described in a Custom Layers file, or as an extension for the Model Optimizer. If not, then it will check if the operation could be described using default configurations already available with OpenVINO.

- There are cases when operation's complexity (or user preferences) makes it not possible to create a representation that is suitable for the Inference Engine. In those scenarios, we can redirect the computation effort to the model original framework. This has some disadvantages, like that the device where the model will run must have the framework installed and, for sure, it will not be as efficient as if the model was completely represented as a full OpenVINO Intermediate Representation.

The result of the Model Optimizer conversion of a model with (or without) Custom Layers should be Intermediate Representation files (.xml and .bin). But for the application, in order to be able to run, the Inference Engine needs also to be fed with relevant extensions regarding model required operations, including custom ones. These extensions are device-related, and it is also possible to have an application running on multiple different devices, each one handling different extensions.

## Comparing Model Performance

Some of the models evaluated before opting for the one used for this project:

| Model Name | Model Size [*Post Conversion*] (MB) | Average Precision (AP) (%)| Inference Ave. Time (ms) | N. People Detected | Completion Time (s)| Running Project |
|--|--|--|--|--|--|--|
| [person-detection-retail-0002](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0002/description/person-detection-retail-0002.md)| 6.19| 80.14|47.684| 0| 73.40 |![image](https://user-images.githubusercontent.com/7910856/82674240-4609a300-9c43-11ea-84dd-d1cdae37a4f9.png) |
| [person-detection-retail-0013](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0013/description/person-detection-retail-0013.md)| 1.38 | 88.62|14.358  |11 | 28.63 | ![image](https://user-images.githubusercontent.com/7910856/82669230-5f0e5600-9c3b-11ea-85a6-fadc49e280d4.png)|
| [ssd_mobilenet_v2_coco](https://github.com/opencv/open_model_zoo/blob/master/models/public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco.md)| 64.16| |21.949| 30| 38.17 |![image](https://user-images.githubusercontent.com/7910856/82669420-b1e80d80-9c3b-11ea-8608-4a40729b14ea.png)|
| [ssdlite_mobilenet_v2_coco](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/public/ssdlite_mobilenet_v2/ssdlite_mobilenet_v2.md)| 17.07 | |11.791 | 40 | 25.97| ![image](https://user-images.githubusercontent.com/7910856/82672628-e0b4b280-9c40-11ea-9782-c6413e265bc0.png)|
| [pedestrian-detection-adas-0002](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/pedestrian-detection-adas-0002/description/pedestrian-detection-adas-0002.md) | 2.22| 88|14.435 |71 |27.36|![image](https://user-images.githubusercontent.com/7910856/82670470-7c442400-9c3d-11ea-9c7f-32ca935bdee5.png)|

After careful consideration, the selected model for the project was *person-detection-retail-0013* considering the size of the model, number of detected people and average inference time.

### Downloading The Model

An example as to how to download a model from the Open Model Zoo and convert to Intermediate Representations.

Typical Usage:

- Download the correct model for object detection using the docker container.
```bash
docker run --rm -ti -v "$PWD":/app mmphego/intel-openvino\
/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py \
--name ssd_mobilenet_v2_coco \
--precision FP16
```

- Convert TensorFlow model to Intermediate Representation.
```bash
cd public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco_2018_03_29
docker run --rm -ti -v "$PWD":/app mmphego/intel-openvino \
/opt/intel/openvino/deployment_tools/model_optimizer/mo.py \
--input_model frozen_inference_graph.pb \
--tensorflow_object_detection_api_pipeline_config pipeline.config \
--reverse_input_channels \
--transformations_config /opt/intel/openvino/deployment_tools/model_optimizer/extensions/front/tf/ssd_v2_support.json
mv frozen_inference_graph.xml ssd_mobilenet_v2_coco.xml
mv frozen_inference_graph.bin ssd_mobilenet_v2_coco.bin
rsync -truv --remove-source-files ssd_mobilenet_v2_coco.{bin,xml} ../../../models/
```

## Assess Model Use Cases

People counter app has many potential uses, some of them are:

- For security reasons, it could be used for industrial or residential purposes in order to detect any unauthorised persons.
- With the current COVID-19 pandemic, this app would help guarantee a place is not overcrowded, or there are some limitations related with the quantity of people allowed to be there.
- Retail stores could create people traffic heat-maps to check where people prefer to be in the store, providing useful information for targeted marketing, products positioning and even how many people visited the store.
- In emergency scenarios, it would be useful to know how many people are inside a place (building, factory, etc) as an indicator for possible rescue operations.

Note: The applications is not perfect and it might result in false-positives or true-negatives. For example, a person could enter with a blanket covering themselves and the app (as it is presented here) will not make a detection. It is possible to include other elements to avoid this situations, but as for today, there are not perfect people detection models.


## Assess Effects on End User Needs

People counter app can be used in different scenario. If high accuracy is required, then all factors including lighting, camera focal length, image size/resolution, position of camera and model accuracy contribute to output result.

Lighting should be reasonable to detected objects, It should not to dark so that model fail to detect objects. Camera position also matters for accuracy purposes. If object structure is clear from current camera position, model will easily able to detect. Image Size should not too small or too big, it should be according to model used. More pre-processing is required if it is far from required size. Most critical is model accuracy we are currently using. Model with high accuracy will provide more accurate inference.

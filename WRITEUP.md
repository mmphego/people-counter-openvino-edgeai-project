
# Project Write-Up

You can use this document as a template for providing your project write-up. However, if you have a different format you prefer, feel free to use it as long as you answer all required questions.

## Explaining Custom Layers

The process behind converting custom layers involves...

Some of the potential reasons for handling custom layers are...

## Comparing Model Performance

Some of the models evaluated before opting for the one used for this project:

| Model Name | Model Size [*Post Conversion*] (MB) | Average Precision (AP) (%)| Inference Ave. Time (ms) | N. People Detected | Completion Time (s)| Running Project |
|--|--|--|--|--|--|--|
| [person-detection-retail-0002](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0002/description/person-detection-retail-0002.md)| 6.19| 80.14|47.684| 0| 73.40 |![image](https://user-images.githubusercontent.com/7910856/82674240-4609a300-9c43-11ea-84dd-d1cdae37a4f9.png) |
| [person-detection-retail-0013](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0013/description/person-detection-retail-0013.md)| 1.38 | 88.62|14.358  |11 | 28.63 | ![image](https://user-images.githubusercontent.com/7910856/82669230-5f0e5600-9c3b-11ea-85a6-fadc49e280d4.png)|
| [ssd_mobilenet_v2_coco](https://github.com/opencv/open_model_zoo/blob/master/models/public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco.md)| 64.16| |21.949|30| 38.17 |![image](https://user-images.githubusercontent.com/7910856/82669420-b1e80d80-9c3b-11ea-8608-4a40729b14ea.png)|
| [ssdlite_mobilenet_v2_coco](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/public/ssdlite_mobilenet_v2/ssdlite_mobilenet_v2.md)| 17.07 | |11.791 | 40 | 25.97| ![image](https://user-images.githubusercontent.com/7910856/82672628-e0b4b280-9c40-11ea-9782-c6413e265bc0.png)|
| [pedestrian-detection-adas-0002](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/pedestrian-detection-adas-0002/description/pedestrian-detection-adas-0002.md) | 2.22| 88|14.435 |71 |27.36|![image](https://user-images.githubusercontent.com/7910856/82670470-7c442400-9c3d-11ea-9c7f-32ca935bdee5.png)|

## Assess Model Use Cases

Some of the potential use cases of the people counter app are...

Each of these use cases would be useful because...

## Downloading the model

An example as to how to download a model from the Open Model Zoo and convert to IR.

Typical Usage:

- Download the correct model for object detection.
```bash
DOCKERCONT="mmphego/intel-openvino"
docker run --rm -ti -v "$PWD":/app "$DOCKERCONT" \
/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py \
--name ssd_mobilenet_v2_coco \
--precision FP16
```

- Convert TensorFlow model to Intermediate Representation
```bash
DOCKERCONT="mmphego/intel-openvino"
cd public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco_2018_03_29
docker run --rm -ti -v "$PWD":/app "$DOCKERCONT" \
/opt/intel/openvino/deployment_tools/model_optimizer/mo.py \
--input_model frozen_inference_graph.pb \
--tensorflow_object_detection_api_pipeline_config pipeline.config \
--reverse_input_channels \
--transformations_config /opt/intel/openvino/deployment_tools/model_optimizer/extensions/front/tf/ssd_v2_support.json
rsync -truv --remove-source-files frozen_inference_graph.{bin,xml} ../../../models/
```

## Assess Effects on End User Needs

Lighting, model accuracy, and camera focal length/image size have different effects on a deployed edge model. The potential effects of each of these are as follows...

## Model Research

[This heading is only required if a suitable model was not found after trying out at least three different models. However, you may also use this heading to detail how you converted a successful model.]

In investigating potential people counter models, I tried each of the following three models:

- Model 1: [Name]
  - [Model Source]
  - I converted the model to an Intermediate Representation with the following arguments...
  - The model was insufficient for the app because...
  - I tried to improve the model for the app by...

- Model 2: [Name]
  - [Model Source]
  - I converted the model to an Intermediate Representation with the following arguments...
  - The model was insufficient for the app because...
  - I tried to improve the model for the app by...

- Model 3: [Name]
  - [Model Source]
  - I converted the model to an Intermediate Representation with the following arguments...
  - The model was insufficient for the app because...
  - I tried to improve the model for the app by...

//////////////////////////////////////////////////////////////////


# Project Write-Up

You can use this document as a template for providing your project write-up. However, if you have a different format you prefer, feel free to use it as long as you answer all required questions.

## Explaining Custom Layers

The process behind converting custom layers involves...

Some of the potential reasons for handling custom layers are...

## Comparing Model Performance

My method(s) to compare models before and after conversion to Intermediate Representations
were...

The difference between model accuracy pre- and post-conversion was...

The size of the model pre- and post-conversion was...

The inference time of the model pre- and post-conversion was...

## Assess Model Use Cases

Some of the potential use cases of the people counter app are...

Each of these use cases would be useful because...

### Models Analysis
Possible models to consider for the project.
- [ssd_mobilenet_v2_coco ](https://github.com/opencv/open_model_zoo/blob/master/models/public/ssd_mobilenet_v2_coco/ssd_mobilenet_v2_coco.md)
- [person-detection-retail-0013 AP: 88.62%](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0013/description/person-detection-retail-0013.md)
- [pedestrian-detection-adas-0002 AP: 88%](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/pedestrian-detection-adas-0002/description/pedestrian-detection-adas-0002.md)
- [person-detection-retail-0002 AP: 80%](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-retail-0002/description/person-detection-retail-0002.md)
- [person-detection-asl-0001 AP: 77.68%](https://github.com/opencv/open_model_zoo/blob/7d235755e2d17f6186b11243a169966e4f05385a/models/intel/person-detection-asl-0001/description/person-detection-asl-0001.md)

### Downloading the model

An example as to how to download a model from the Open Model Zoo and convert to IR.

Typical Usage:

- Download the correct model for object detection.
```bash
DOCKERCONT="mmphego/intel-openvino"
docker run --rm -ti -v "$PWD":/app "$DOCKERCONT" \
/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py \
--name ssd_mobilenet_v2_coco
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

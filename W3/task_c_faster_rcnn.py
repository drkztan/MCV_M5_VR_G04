"""

Task 2: Use object detection models in inference: Faster R-CNN

"""

import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import numpy as np
import os, json, cv2, random
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog

import matplotlib.pyplot as plt

from detectron2.engine import DefaultTrainer
from detectron2.structures import BoxMode

from detectron2.utils.visualizer import ColorMode

from PIL import Image
import io_tools
import pycocotools
from tqdm import tqdm

from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader


"""
Obtención de las boxes de cada imagen
"""
def get_dicts(path):
    raw_dicts = []
    dataset_dicts = []
    Pedestrians = []
    Cars =[]
    for file in sorted(os.listdir(path + "/instances_txt")):
        annotations = io_tools.load_txt(path + "/instances_txt/" + file)
        raw_dicts.append(annotations)
    for idx, dicts in tqdm(enumerate(raw_dicts)):
        for key,value in dicts.items():
            record = {}
            img_id = str(key).zfill(6)
            img_path = os.path.join(IMG_PATH,str(idx).zfill(4),str(img_id)+".png")
            img = cv2.imread(img_path)
            height,width,channels = img.shape

            record["file_name"] = img_path
            record["image_id"] = img_id
            record["height"] = height
            record["width"] = width
            objs = []
            for instance in value:
                category_id = instance.class_id
                if category_id == 1 or category_id == 2:
                    bbox = pycocotools.mask.toBbox(instance.mask)
                    obj = {
                        "bbox": [float(bbox[0]),float(bbox[1]),float(bbox[2]),float(bbox[3])],
                        "bbox_mode": BoxMode.XYWH_ABS,
                        "category_id": category_id,
                    }
                    objs.append(obj)
            record["annotations"] = objs
            dataset_dicts.append(record)

    return dataset_dicts


LOCAL_RUN = False
IMG_PATH = "../datasets/KITTI-MOTS/training/image_02"
LABEL_PATH = "../datasets/KITTI-MOTS/instances_txt"
BASE_PATH = "../datasets/KITTI-MOTS/"

if LOCAL_RUN:
    IMG_PATH = "../resources/KITTI-MOTS/training/image_02"
    LABEL_PATH = "../resources/KITTI-MOTS/instances_txt"
    BASE_PATH = "../resources/KITTI-MOTS/"


cfg = get_cfg()
# add project-specific config (e.g., TensorMask) here if you're not running a model in detectron2's core library
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # set threshold for this model
# Find a model from detectron2's model zoo. You can use the https://dl.fbaipublicfiles... url as well
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")

predictor = DefaultPredictor(cfg)

DatasetCatalog.register("kitti-mots_train", lambda d="train": get_dicts(BASE_PATH))
kitti_mots_metadata = MetadataCatalog.get("kitti-mots_train")

dataset_dicts = get_dicts(BASE_PATH)

for rand in random.sample(dataset_dicts, 1):
    img = cv2.imread(rand["file_name"])
    visualizer = Visualizer(img[:, :, ::-1], metadata=kitti_mots_metadata, scale=0.5)
    out = visualizer.draw_dataset_dict(rand)
    plt.imshow(out.get_image()[:, :, ::-1])
    plt.show()
    cv2.imwrite("out_kittimotts_faster_rcnn.png", out.get_image()[:, :, ::-1])


evaluator = COCOEvaluator("kitti-mots_train", cfg, False, output_dir="./output/")
val_loader = build_detection_test_loader(cfg, "kitti-mots_train")
print(inference_on_dataset(predictor.model, val_loader, evaluator))


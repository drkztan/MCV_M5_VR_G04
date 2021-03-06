import json
import os
import random
import time

import cv2
import detectron2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
from detectron2.config import get_cfg
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.utils.visualizer import Visualizer
from torch.utils.data import DataLoader
from tqdm import tqdm

print(torch.__version__, torch.cuda.is_available())
from detectron2.utils.logger import setup_logger

setup_logger()

import pickle

import pycocotools
import pycocotools.mask as rletools
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import (DatasetCatalog, DatasetMapper, MetadataCatalog,
                             build_detection_test_loader)
from detectron2.engine import DefaultPredictor, DefaultTrainer
from detectron2.evaluation import (COCOEvaluator, LVISEvaluator,
                                   inference_on_dataset)
from detectron2.structures import BoxMode
from detectron2.utils.visualizer import Visualizer

import coco_io


########### CUSTOM data reader
def get_kitti_dataset_train(path_list):
    MAX_ITER = 10

    img_dir = "../resources/KITTI-MOTS/training/image_02"

    labels_dir = path_list[0][
        :-8
    ]  # same for all: /home/drkztan/Documents/repos/MCV_M5_VR_G04/resources/KITTI-MOTS/instances_txt/
    folders_list = []  # [0000, 0001, 0002, ...]
    all_files_list_dicts = []
    for path in path_list[:-4]:
        folder = path[-8:-4] + "/"
        folders_list.append(folder)
        dict_files_in_path = coco_io.load_txt(
            path
        )  # returns a dictionary with 0,1,2,3... as keys
        all_files_list_dicts.append(dict_files_in_path)

    dataset_dicts = []
    for idx, all_files in tqdm(enumerate(all_files_list_dicts)):
        for key, value in all_files.items():
            record = {}
            filename = str(key).zfill(6) + ".png"
            # print(filename)
            img_filename = os.path.join(
                img_dir, folders_list[idx], filename
            )  # TODO: get propper img_dir and folder
            height, width = cv2.imread(img_filename).shape[:2]

            record["file_name"] = img_filename
            record["image_id"] = str(key).zfill(4)
            record["height"] = height
            record["width"] = width

            objs = []

            for objects in value:
                class_id = objects.class_id
                instance_id = objects.track_id
                bbox = pycocotools.mask.toBbox(objects.mask)

                mask = rletools.decode(objects.mask)
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
                )
                seg = [[int(i) for i in c.flatten()] for c in contours]
                seg = [s for s in seg if len(s) >= 6]

                if not seg:
                    continue

                if class_id == 1 or class_id == 2:
                    obj = {
                        "type": "Car" if class_id == 1 else "Pedestrian",
                        "bbox": [
                            float(bbox[0]),
                            float(bbox[1]),
                            float(bbox[2]),
                            float(bbox[3]),
                        ],
                        "bbox_mode": BoxMode.XYWH_ABS,
                        "category_id": 2 if class_id == 1 else 0,
                        "segmentation": seg,
                    }

                    objs.append(obj)

            record["annotations"] = objs
            dataset_dicts.append(record)

    ############################ HERE WE DO MOTSChallenge #############################

    return dataset_dicts


########### CUSTOM data reader val
def get_kitti_dataset_val(path_list):
    MAX_ITER = 10

    img_dir = "../resources/KITTI-MOTS/training/image_02"

    labels_dir = path_list[0][
        :-8
    ]  # same for all: /home/drkztan/Documents/repos/MCV_M5_VR_G04/resources/KITTI-MOTS/instances_txt/
    folders_list = []  # [0000, 0001, 0002, ...]
    all_files_list_dicts = []
    for path in path_list:
        folder = path[-8:-4] + "/"
        folders_list.append(folder)
        dict_files_in_path = coco_io.load_txt(
            path
        )  # returns a dictionary with 0,1,2,3... as keys
        all_files_list_dicts.append(dict_files_in_path)

    dataset_dicts = []
    for idx, all_files in tqdm(enumerate(all_files_list_dicts)):
        # print(folders_list[idx])
        # exit()

        for key, value in all_files.items():
            record = {}
            filename = str(key).zfill(6) + ".png"
            # print(filename)
            img_filename = os.path.join(
                img_dir, folders_list[idx], filename
            )  # TODO: get propper img_dir and folder
            height, width = cv2.imread(img_filename).shape[:2]

            record["file_name"] = img_filename
            record["image_id"] = str(key).zfill(4)
            record["height"] = height
            record["width"] = width

            objs = []

            for objects in value:
                class_id = objects.class_id
                instance_id = objects.track_id
                bbox = pycocotools.mask.toBbox(objects.mask)

                mask = rletools.decode(objects.mask)
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
                )
                seg = [[int(i) for i in c.flatten()] for c in contours]
                seg = [s for s in seg if len(s) >= 6]
                if not seg:
                    continue

                if class_id == 1 or class_id == 2:
                    obj = {
                        # "type": "Car" if class_id == 1 else "Pedestrian",
                        "bbox": [
                            float(bbox[0]),
                            float(bbox[1]),
                            float(bbox[2]),
                            float(bbox[3]),
                        ],
                        "bbox_mode": BoxMode.XYWH_ABS,
                        "category_id": 2 if class_id == 1 else 0,
                        "segmentation": seg,
                    }

                    objs.append(obj)

            record["annotations"] = objs
            dataset_dicts.append(record)

            print(record)
            exit()

    return dataset_dicts


# Dataset registration
base_path = "../resources/KITTI-MOTS/instances_txt/"

test_paths = [base_path + str(i).zfill(4) + ".txt" for i in range(19, 21)]

train_arr = [0, 6, 7, 8, 10, 13, 14, 16, 18]
train_paths = [base_path + str(i).zfill(4) + ".txt" for i in train_arr]

val_arr = [2, 1, 3, 4, 5, 9, 11, 12, 15, 17, 19, 20]
val_paths = [base_path + str(i).zfill(4) + ".txt" for i in val_arr]


import os

outputs = "inference_test_antoni_2"

if not os.path.exists(outputs):
    os.makedirs(outputs)

# train dataset
# classes = ['Car','Person', 'NA']
# we have no idea why this particular order is the only one that returns reasonable AP values
classes = ["Pedestrian","NA", "Car"]

for d in [train_paths]:
    DatasetCatalog.register("train_kitti-mots", lambda d=d: get_kitti_dataset_train(d))
    MetadataCatalog.get("train_kitti-mots").set(thing_classes=classes)

# val dataset
for d in [val_paths]:
    DatasetCatalog.register("val_kitti-mots", lambda d=d: get_kitti_dataset_val(d))
    MetadataCatalog.get("val_kitti-mots").set(thing_classes=classes)

# Pre-trained
print("Loading pre-trained models...")
cfg = get_cfg()

# Select model

model_name = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml"
cfg.DATALOADER.NUM_WORKERS = 8
cfg.merge_from_file(model_zoo.get_config_file(model_name))

cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(model_name)
cfg.DATASETS.TEST = ("val_kitti-mots",)
# cfg.DATASETS.TRAIN = ("train_kitti-mots",)

cfg.OUTPUT_DIR = outputs
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
tic = time.perf_counter()
######################################################################
######################################################################
######################################################################
######################################################################

# 
# cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
#     model_name
# )  
# # Let training initialize from model zoo
# cfg.SOLVER.IMS_PER_BATCH = 4
# cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
# cfg.SOLVER.MAX_ITER = 600  # 300 iterations seems good enough for this toy dataset; you will need to train longer for a practical dataset
# cfg.SOLVER.STEPS = []  # do not decay learning rate
# cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = (
#     512  # faster, and good enough for this toy dataset (default: 512)
# )
# cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3  # only has one class (ballon). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
# # NOTE: this config means the number of classes, but a few popular unofficial tutorials incorrect uses num_classes+1 here.
# cfg.TEST.EVAL_PERIOD = 100

# trainer = DefaultTrainer(cfg)
# trainer.resume_or_load(resume=False)
# trainer.train()

# cfg.MODEL.WEIGHTS = os.path.join(
#     cfg.OUTPUT_DIR, "model_final.pth"
# )  
# # path to the model we just trained
# cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7   # set a custom testing threshold
# predictor = DefaultPredictor(cfg)

#####################################################################
#####################################################################
#####################################################################
#####################################################################


predictor = DefaultPredictor(cfg)

# Evaluate
print("Evaluating...")

tasks = (
    "bbox",
    "segm",
)
evaluator = COCOEvaluator(
    "val_kitti-mots",
    tasks,
    False,
    output_dir=outputs,
)
val_loader = build_detection_test_loader(cfg, "val_kitti-mots")
print(inference_on_dataset(predictor.model, val_loader, evaluator))
toc=time.perf_counter()
toctoc = toc - tic
print(f"time elapsed: {toctoc:4f}")

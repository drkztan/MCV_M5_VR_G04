import argparse
import logging
import os
import pickle
import random
import sys
import time

import colorama
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pycocotools.mask as rletools
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import (DatasetCatalog, DatasetMapper, MetadataCatalog,
                             build_detection_test_loader)
from detectron2.engine import DefaultPredictor, DefaultTrainer
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.modeling import build_model
from detectron2.utils.visualizer import ColorMode, Visualizer
from pycocotools import coco
from tqdm import tqdm

import getDicts
from src import config, imgUtils, cooc_tools

### 158.109.75.51 –p 55022


def parse_args():
    parser = argparse.ArgumentParser(description="visualize annotations")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-m",
        "--mots",
        dest="mots",
        action="store_true",
        default=False,
        required=False,
    )
    fname = os.path.splitext(parser.prog)
    return parser.parse_args(), fname


def use_model(model_name, model_url):
    current_output_dir = f"{config.output_path}/{model_name}"
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(model_url))
    os.makedirs(current_output_dir, exist_ok=True)
    cfg.OUTPUT_DIR = f"{current_output_dir}"
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(model_url)

    coco_2017_val_dataset = "coco_2017_val"
    cfg.DATASETS.TEST = (coco_2017_val_dataset,)
    cfg.DATALOADER.NUM_WORKERS = 4
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7  # set a custom testing threshold
    out_of_contex_dir = "../resources/out_of_context"

    predictor = DefaultPredictor(cfg)
    i = 0
    pred_dict = {}
    pred_dict["Class_names"] = MetadataCatalog.get(coco_2017_val_dataset).thing_classes

    for filename in tqdm(os.listdir(out_of_contex_dir), desc="Image_gen", colour="Magenta"):

        im = cv2.imread(os.path.join(out_of_contex_dir,filename))
        outputs = predictor(im)
        v = Visualizer(
            im[:, :, ::-1],
            metadata=MetadataCatalog.get(coco_2017_val_dataset),
            scale=1,
            instance_mode=ColorMode.IMAGE_BW,
        )

        v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        img = v.get_image()[:, :, ::-1]

        # show_img_with_escape(img)

        img_filepath = f"{config.gen_img_path}/imgs"
        img_filename = f"{img_filepath}/{filename}"
        config.create_txt_results_path(img_filepath)
        # print(filename)

        # cv2.imwrite(img_filename, img)

        ############################## Co-occurrence matrix  ###################################
        ############################# text class idx to labels #################################
        pred_classes = outputs["instances"].pred_classes
        class_names = MetadataCatalog.get(coco_2017_val_dataset).thing_classes
        pred_class_names = list(map(lambda x: class_names[x], pred_classes))
        # print(pred_classes)
        # print(f"pred class names {pred_class_names} \n")
        # print(class_names)

        tmparr = [0] * len(class_names)

        # print(pred_dict)
        # exit()

        for idx in pred_classes:
            tmparr[idx]+=1

        pred_dict[f'{filename[:-4]}'] = tmparr


    # print(cooc)
    plt_filepath = f"{config.gen_img_path}/plts"
    plt_filename = f"{plt_filepath}/cooc_heatmap.png"
    config.create_txt_results_path(f"{plt_filepath}")
    cooc_mat = cooc_tools.build_cooc_matrix(pred_dict, plt_filename)
    print(cooc_mat)



def show_img_with_escape(img):
    cv2.imshow("img", img)
    k = cv2.waitKey(0)
    if k==27:    # Esc key to stop
        exit()


if __name__ == "__main__":
    ##########################################################################################
    ###################################   WORKSPACE SETUP   ##################################
    ##########################################################################################
    colorama.init(autoreset=False)
    parser, fname = parse_args()
    mots = parser.mots

    v = parser.verbose
    if v:
        print(
            colorama.Fore.LIGHTRED_EX
            + "\n#################################\n"
            + str(parser)
        )

    config.init_workspace(v, fname[0])
    if config.verbose:
        logging.basicConfig(level=logging.INFO)

    ##########################################################################################
    ###################################   WORKSPACE SETUP   ##################################
    ##########################################################################################


    ##########################################################################################
    ##############################   PRETRAINED MODEL INFERENCE   ############################
    ##########################################################################################


    for model_name, model_url in config.mask_rcnn_models.items():
        if config.verbose:
            print(
                colorama.Fore.LIGHTGREEN_EX
                + f"\nUsing {model_name} from url {model_url}"
            )
        config.mask_rcnn_results[f"{model_name}"] = use_model(
            model_name=model_name,
            model_url=model_url
        )
        # break
    for model_name, result in config.mask_rcnn_results.items():
        if config.verbose:
            print(f"{model_name}: {result}\n\n\n\n")

    ##########################################################################################
    ##############################   PRETRAINED MODEL INFERENCE   ############################
    ##########################################################################################

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

import utils

LOCAL_RUN = True
DATA_TEST_PATH = "../datasets/KITTI-MOTS/testing/image_02"
if LOCAL_RUN:
    DATA_TEST_PATH = "../resources/KITTI-MOTS/testing/image_02"



OUTPUT_PATH = "outputs/b_retinaNet"

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

retinaNet = get_cfg()
# add project-specific config (e.g., TensorMask) here if you're not running a model in detectron2's core library
retinaNet.merge_from_file(model_zoo.get_config_file("COCO-Detection/retinanet_R_50_FPN_1x.yaml"))
retinaNet.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # set threshold for this model
# Find a model from detectron2's model zoo. You can use the https://dl.fbaipublicfiles... url as well
retinaNet.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/retinanet_R_50_FPN_1x.yaml")
retinaPredictor = DefaultPredictor(retinaNet)

i=0
for category_folder in os.listdir(DATA_TEST_PATH):
    utils.print_percent_done(i, len(next(os.walk(DATA_TEST_PATH))[1]))
    i += 1
    for filename in random.sample(os.listdir(DATA_TEST_PATH + "/" + category_folder),3):
        # print("validation image: "+DATA_TEST_PATH + "/" + category_folder + "/" + filename)

        imRetina = cv2.imread(DATA_TEST_PATH+"/"+category_folder+"/"+filename)
        outRetina = retinaPredictor(imRetina)

        # print(outputs["instances"].pred_classes)
        # print(outputs["instances"].pred_boxes)

        retinaVisualizer = Visualizer(imRetina[:, :, ::-1], MetadataCatalog.get(retinaNet.DATASETS.TRAIN[0]), scale=1.2)
        outRetina = retinaVisualizer.draw_instance_predictions(outRetina["instances"].to("cpu"))

        img = np.array(outRetina.get_image()[:, :, ::-1])

        txt_font = cv2.FONT_HERSHEY_PLAIN
        fontsize = 5
        fontcolor = (255,0,255)
        bg_color = (200,200,200)
        fontthickness = 3
        txtSize = cv2.getTextSize("retinaNet", txt_font, fontsize, fontthickness)[0]
        margin = 10
        textX = img.shape[1] - (txtSize[0])- margin
        textY = margin
        coords = (textX,textY)
        # print(coords)
        

        img = utils.draw_text(img, "retinaNet", txt_font, coords, fontsize, fontthickness, fontcolor, bg_color)

        cv2.imwrite(f"{OUTPUT_PATH}/{category_folder}_{filename}.png", img) 

        # plt.imshow(out.get_image()[:, :, ::-1])
        # plt.show()

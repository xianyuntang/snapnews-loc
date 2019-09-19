import torch
import torch.nn as nn
from torch.autograd import Variable
import cv2
from craft import craft_utils
from craft import imgproc

from craft.craft import CRAFT

from collections import OrderedDict
import numpy as np


class Localization:
    def __init__(self,
                 weights_path='./craft/weights/craft_mlt_25k.pth',
                 canvas_size=1280,
                 text_threshold=0.9,
                 link_threshold=0.1,
                 mag_ratio=1.5,
                 low_text=0.5,
                 gpu=True):
        self.canvas_size = canvas_size
        self.text_threshold = text_threshold
        self.link_threshold = link_threshold
        self.low_text = low_text
        self.mag_ratio = mag_ratio
        self.gpu = gpu
        self.model = CRAFT()
        self.model.load_state_dict(self.copy_state_dict(torch.load(weights_path,map_location='cpu')))
        if self.gpu:
            self.model.cuda()
            self.model = torch.nn.DataParallel(self.model)
        self.model.eval()

    @staticmethod
    def copy_state_dict(state_dict):
        if list(state_dict.keys())[0].startswith("module"):
            start_idx = 1
        else:
            start_idx = 0
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = ".".join(k.split(".")[start_idx:])
            new_state_dict[name] = v
        return new_state_dict

    def predict(self, image):
        img_resized, target_ratio, size_heatmap = imgproc.resize_aspect_ratio(image, self.canvas_size,
                                                                              interpolation=cv2.INTER_AREA,
                                                                              mag_ratio=self.mag_ratio)
        ratio_h = ratio_w = 1 / target_ratio
        x = imgproc.normalizeMeanVariance(img_resized)
        x = torch.from_numpy(x).permute(2, 0, 1)  # [h, w, c] to [c, h, w]
        x = Variable(x.unsqueeze(0))  # [c, h, w] to [b, c, h, w]
        if self.gpu:
            x = x.cuda()

        y, _ = self.model(x)


        
        score_text = y[0, :, :, 0].cpu().data.numpy()
        score_link = y[0, :, :, 1].cpu().data.numpy()

        boxes = craft_utils.getDetBoxes(score_text, score_link, self.text_threshold, self.link_threshold, self.low_text)
        boxes = craft_utils.adjustResultCoordinates(boxes, ratio_w, ratio_h)

        boxes = np.reshape(boxes, newshape=(-1, 8)).astype(np.int)
        print(boxes)
        return boxes

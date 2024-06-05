import os
import shutil

import torch

import numpy as np
from PIL import Image
from tqdm import tqdm
from moviepy.editor import VideoFileClip, ImageSequenceClip

from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline


class RealESRGAN:
    def __init__(self, param):
        self.param = param
        self.model = param["checkpoint"]
        self.device = param["device"]
        if not torch.cuda.is_available():
            self.device = "cpu"

    def infer(self, input_data, output_data):
        os.environ['MODELSCOPE_CACHE'] = os.path.join(os.path.dirname(__file__), "checkpoint")

        input_path = input_data["video_path"]

        temp_dir    = output_data["temp_dir"]
        output_path = output_data["video_path"]

        os.makedirs(temp_dir, exist_ok=True)

        video = VideoFileClip(input_path)
        fps = video.fps

        super_resolution = pipeline('image-super-resolution-x2', model=self.model)
        temp_save_path = os.path.join(temp_dir, f"temp.png")
        image_paths = list()
        for i, frame in enumerate(tqdm(video.iter_frames())):
            frame = np.array(frame)
            Image.fromarray(frame).save(temp_save_path)
            result = super_resolution(temp_save_path)
            temp_image_path = os.path.join(temp_dir, f"image_{i}.png")
            Image.fromarray(result[OutputKeys.OUTPUT_IMG][:, :, ::-1]).save(temp_image_path)
            image_paths.append(temp_image_path)

        output_video = ImageSequenceClip(image_paths, fps=fps)

        output_video = output_video.set_audio(video.audio)
        output_video.write_videofile(output_path)
        shutil.rmtree(temp_dir)

        return output_path
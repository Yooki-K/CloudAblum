# coding=utf-8
import json
import models
from PIL import Image
from tlt.utils import load_pretrained_weights
from timm.data import create_transform
from io import BytesIO

model = models.volo_d1(img_size=224)
load_pretrained_weights(model=model, checkpoint_path='pretrained/d1_224_84.2.pth.tar')
model.eval()
transform = create_transform(input_size=224, crop_pct=model.default_cfg['crop_pct'])
imagenet_classes = {}
index = 0
with open('API/images_class.txt', 'r', encoding='utf-8') as f:
    r = f.readlines()
for x in r:
    imagenet_classes[index] = x.replace('\n', '')
    index = index + 1


class ObjectAPI:
    options = 'ObjectDetectionAPI'

    @staticmethod
    def predict(imagebyte):
        i = Image.open(BytesIO(imagebyte))
        input_i = transform(i).unsqueeze(0)
        p = model(input_i)
        return imagenet_classes[int(p.argmax())]

    @staticmethod
    def object_detection(imgFile) -> str:
        return ObjectAPI.predict(imgFile)


# ['人物','动物', '风景', '建筑物', '交通工具']
def get_label(tag: list):
    """返回[分类大类,小类]"""
    with open('./static/json/labels.json', mode='r', encoding='utf-8')as f:
        r = json.load(f)
    for y in tag:
        for x in r:
            if y in r[x]:
                return [x, tag]
    return ['', tag]

from utils import *
import dlib
import cv2
import numpy as np


class face_recognition:
    def __init__(self):
        self.predictor_path = "./dat/shape_predictor_68_face_landmarks.dat"
        self.predictor_path1 = "./"
        self.face_rec_model_path = "dat/dlib_face_recognition_resnet_model_v1.dat"
        self.detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(self.predictor_path)
        self.face_rec_model = dlib.face_recognition_model_v1(self.face_rec_model_path)

    def face_detect_api(self, file):
        fileBin = file
        temp = np.frombuffer(fileBin, np.uint8)
        img = cv2.imdecode(temp, cv2.IMREAD_ANYCOLOR)
        # 检测人脸
        faces = self.detector(img, 1)
        return len(faces)

    def face_compare_api(self, files):
        """小于0.6可认为是同一人"""
        dist = []
        for file in files:
            temp = np.frombuffer(file, np.uint8)
            img = cv2.imdecode(temp, cv2.IMREAD_ANYCOLOR)
            # 转换rgb顺序的颜色。
            b, g, r = cv2.split(img)
            img2 = cv2.merge([r, g, b])
            # 检测人脸
            faces = self.detector(img, 1)
            if len(faces):
                for index, face in enumerate(faces):
                    # # 提取68个特征点
                    shape = self.shape_predictor(img2, face)
                    # 计算人脸的128维的向量
                    face_descriptor = self.face_rec_model.compute_face_descriptor(img2, shape)
                    dist.append(list(face_descriptor))
            else:
                return None
        goal = self.dis_o(dist[0], dist[1])
        return 1 - goal

    # 欧式距离
    @staticmethod
    def dis_o(dist_1, dist_2) -> float:
        dis = np.sqrt(sum((np.array(dist_1) - np.array(dist_2)) ** 2))
        return dis


class FaceAPI:
    options = 'FaceDetectionAPI'
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    def __init__(self):
        pass

    # 人脸检测
    def face_detection(self, img) -> [dict, None]:
        face = face_recognition()
        faceNum = face.face_detect_api(img)
        return faceNum

    # 添加人脸
    @staticmethod
    def add_face() -> [str, None]:
        all_char = 'qazwsxedcrfvtgbyhnujmikolp'
        index = len(all_char) - 1
        faceid = ''
        for _ in range(6):
            n = random.randint(0, index)
            faceid += all_char[n]
        return faceid

    # 匹配两张人脸图片
    def match_face(self, imageFile1, imageFile2) -> [float, None]:
        face = face_recognition()
        confidence = face.face_compare_api([imageFile1, imageFile2])
        return confidence


if __name__ == '__main__':
    pass

import base64
import configparser as conf
import copy
import hmac
import random
import time
import urllib
import urllib.parse
from hashlib import sha1
from hashlib import sha256
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
import multiprocessing as mp

CONF = conf.ConfigParser()
CONF.read('ini.cfg', encoding="utf-8")
detection_process_name = 'DetectionProcess'
detection_process_list = mp.Queue()


# 查看检测进程是否在进行
def getDetectionProcess():
    ps = mp.active_children()
    for p in ps:
        if p.name == detection_process_name:
            return p
    return None


# PIL打开图片转换为opencv2打开格式
def pil_to_cv2(img, code=cv2.COLOR_RGB2BGR):
    return cv2.cvtColor(np.array(img), code)


# opencv2打开图片转换为PIL打开格式
def cv2_to_pil(img, code=cv2.COLOR_BGR2RGB):
    return Image.fromarray(cv2.cvtColor(img, code))


# opencv2 打开图片
def cv_open(f_stream, code=cv2.IMREAD_UNCHANGED):
    return cv2.imdecode(np.array(bytearray(f_stream), dtype='uint8'), code)


def cv_to_bits(img, format):
    return np.array(cv2.imencode('.' + format, img)[1]).tobytes()


def pil_to_bits(img, format):
    bytesIO = BytesIO()
    if format == 'JPG':
        format = 'JPEG'
    img.save(bytesIO, format=format)
    return bytesIO.getvalue()


# PIL 打开图片
def pil_open(f_stream) -> Image:
    return Image.open(BytesIO(f_stream))


def encode(bits, isStr=True):
    """返回是否是字符串"""
    if isStr:
        return str(base64.b64encode(bits), 'utf-8')
    else:
        return base64.b64encode(bits)


def decode(str_or_byte, isByte=False):
    """输入是否是二进制"""
    if isByte:
        return base64.b64decode(str_or_byte)
    else:
        return base64.b64decode(bytes(str_or_byte, 'utf-8'))


def generate_random_str(randomlength=16):
    """
  生成一个指定长度的随机字符串
  """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


def get_time_format() -> str:
    """解析时间成字符串格式：%Y-%m-%dT%H:%M:%SZ"""
    return time.strftime("", time.localtime())


# 创建图像缩略图 返回二进制流
def createThumbnail(im_bytes):
    img = Image.open(BytesIO(im_bytes))
    w = img.width
    h = img.height
    img_ = img.resize((w, h), Image.NEAREST)
    return pil_to_bits(img_, img.format)


class ImgHandler:
    type_json = {
        'PNG': b'\x89\x50',
        'JPG': b'\xff\xd8',
        'ICO': b'\x00\x00\x01\x00\x01\x00\x20\x20',
        'GIF': b'\x47\x49\x46',
        'BMP': b'\x42\xd4D',
        'TIFF': [b'\x4D\x4D', b'\x49\x49'],
        'webp': b'RIFF'
    }

    @staticmethod
    def getType(f_stream) -> [str, None]:
        for x in ImgHandler.type_json.keys():
            value = ImgHandler.type_json[x]
            if type(value) is bytes:
                length = len(value)
                if f_stream[0:length] == value:
                    return x
            elif type(value) is list:
                for y in value:
                    length = len(y)
                    if f_stream[0:length] == y:
                        return x
        return None

    @staticmethod
    def getBase64(f_stream, t=None) -> [str, None]:
        if t is None:
            tt = ImgHandler.getType(f_stream)
        else:
            tt = t
        if tt is not None:
            return "data:image/{0};base64,{1}".format(tt, encode(f_stream))
        else:
            print(None)
            return None


def aes_encrypt(message, aes_key):
    """use AES to encrypt message,
    :param message: 需要加密的内容
    :param aes_key: 密钥
    :return: encrypted_message密文
    """
    mode = AES.MODE_ECB  # 加密模式
    if type(message) == str:
        message = bytes(message, 'utf-8')
    if type(aes_key) == str:
        aes_key = bytes(aes_key, 'utf-8')
    # aes_key, message必须为16的倍数
    while len(aes_key) % 16 != 0:
        aes_key += b' '
    while len(message) % 16 != 0:
        message += b' '
    # 加密对象aes
    aes = AES.new(key=aes_key, mode=mode)
    encrypt_message = aes.encrypt(plaintext=message)
    return b2a_hex(encrypt_message)


def aes_decrypt(encrypt_message, aes_key):
    """ AES解密
    :param encrypt_message: 密文
    :param aes_key: 秘钥
    :return: decrypt_text解密后内容
    """
    aes_mode = AES.MODE_ECB  # 加密模式
    aes = AES.new(key=bytes(aes_key, 'utf-8'), mode=aes_mode)
    decrypted_text = aes.decrypt(a2b_hex(encrypt_message))
    decrypted_text = decrypted_text.rstrip()  # 去空格
    return decrypted_text.decode()


class Signature:
    def __init__(self, accessKey, secretKey):
        self.access_key = accessKey
        self.secret_key = secretKey

        # 签名

    def sign(self, httpMethod, playlocd, servlet_path):
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())
        playlocd['Timestamp'] = time_str
        parameters = copy.deepcopy(playlocd)
        parameters.pop('Signature')
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        # 传入参数有list的情况
        for (k, v) in sortedParameters:
            if isinstance(v, list):
                for v_l in v:
                    canonicalizedQueryString += '&' + self.percent_encode(k) + '=' + self.percent_encode(v_l)
                    break
            else:
                canonicalizedQueryString += '&' + self.percent_encode(k) + '=' + self.percent_encode(v)
        stringToSign = httpMethod + '\n' + self.percent_encode(servlet_path) + '\n' + sha256 \
            (canonicalizedQueryString[1:].encode('utf-8')).hexdigest()

        key = ("BC_SIGNATURE&" + self.secret_key).encode('utf-8')

        stringToSign = stringToSign.encode('utf-8')
        signature = hmac.new(key, stringToSign, sha1).hexdigest()
        # print("signature", signature)
        return signature

    def percent_encode(self, encodeStr):
        encodeStr = str(encodeStr)
        res = urllib.parse.quote(encodeStr.encode('utf-8'), '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

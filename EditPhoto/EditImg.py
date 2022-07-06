from utils import *

# 磨皮 value越大，程度越深
def p_chart_cv(image, value=28):
    dst = cv2.bilateralFilter(image, value, value * 2, value / 2)
    return dst


# 锐化
def custom_blur_demo(image):
    # kernel = np.ones([5, 5], np.float32)/25
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
    dst = cv2.filter2D(image, -1, kernel=kernel)
    return dst


# 素描 depth越大，程度越深
def to_sketch_pil(img, depth=20):  # depth (0-100)，可以理解为图像的深淡程度
    img = np.array(img.convert('L')).astype('float')  # 转化为灰度图
    grad = np.gradient(img)  # 取图像灰度的梯度值
    grad_x, grad_y = grad  # 分别取横纵图像梯度值
    grad_x = grad_x * depth / 100.
    grad_y = grad_y * depth / 100.
    A = np.sqrt(grad_x ** 2 + grad_y ** 2 + 1.)  # 构造x和y轴梯度的三维归一化单位坐标系
    uni_x = grad_x / A
    uni_y = grad_y / A
    uni_z = 1. / A

    vec_el = np.pi / 2.2  # 光源的俯视角度，弧度值
    vec_az = np.pi / 4.  # 光源的方位角度，弧度值
    dx = np.cos(vec_el) * np.cos(vec_az)  # 光源对x 轴的影响
    dy = np.cos(vec_el) * np.sin(vec_az)  # 光源对y 轴的影响
    dz = np.sin(vec_el)  # 光源对z 轴的影响

    b = 255 * (dx * uni_x + dy * uni_y + dz * uni_z)  # 梯度与光源相互作用，将梯度转化为灰度
    b = b.clip(0, 255)  # 为避免数据越界，将生成的灰度值裁剪至0‐255区间

    return Image.fromarray(b.astype('uint8'))  # 重构图像


# 手绘
def to_freehand_cv(img):
    img_f = img
    img_blur = cv2.GaussianBlur(img_f, (21, 21), 0, 0)  # 高斯模糊
    img_blend = cv2.divide(img, img_blur, scale=256)
    return img_blend


# 填充
def fill_pil(img, size: tuple = (1920, 1080), color: tuple = (255, 255, 255, 200)):
    w = size[0]
    h = size[1]
    img_blender = Image.new('RGBA', size, color)  # 填充rgb颜色
    x = int((w - img.size[0]) / 2)
    y = int((h - img.size[1]) / 2)
    img_blender.paste(img, (x, y))
    return img_blender


# 去除某颜色部分 ，处理水印   失败
def remove_watermark(f_stream):
    img = cv_open(f_stream)
    hight, width, depth = img.shape[0:3]
    # 图片二值化处理，把[240, 240, 240]~[255, 255, 255]以外的颜色变成0
    thresh = cv2.inRange(img, np.array([240, 240, 240]), np.array([255, 255, 255]))
    # 创建形状和尺寸的结构元素
    kernel = np.ones((3, 3), np.uint8)
    # 扩张待修复区域
    hi_mask = cv2.dilate(thresh, kernel, iterations=10)
    specular = cv2.inpaint(img, hi_mask, 1, flags=cv2.INPAINT_TELEA)

    cv2.namedWindow("Image", 0)
    cv2.resizeWindow("Image", width, hight)
    cv2.imshow("Image", img)

    cv2.namedWindow("newImage", 0)
    cv2.resizeWindow("newImage", width, hight)
    cv2.imshow("newImage", specular)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test1(path):
    img_ = Image.open(path)
    # 手绘
    img = pil_to_cv2(img_, cv2.COLOR_BGR2GRAY)
    img = to_freehand_cv(img)
    cv2_to_pil(img).show()
    # 彩绘
    img = pil_to_cv2(img_, cv2.COLOR_BGR2GRAY)
    img = to_freehand_cv(img)
    cv2_to_pil(img).show()
    # 填充
    img = fill_pil(img_)
    img.show()


#
# def test2(path):
#     f = fapi.FaceAPI()
#     f.get_token()
#     with open(path, 'rb') as ff:
#         a = encode(ff.read(), True)
#     r = f.face_detection(a)
#     print(r)
#     img = cv_open(path)
#     if r['state'] == 'OK':
#         face_position_list = r['body']['faceDetectDetailList']
#         for x in face_position_list:
#             pos = [x['faceDectectRectangleArea']['upperLeftX'],
#                    x['faceDectectRectangleArea']['upperLeftY'],
#                    x['faceDectectRectangleArea']['lowerRightX'],
#                    x['faceDectectRectangleArea']['lowerRightY']
#                    ]
#             temp = img[int(pos[1]):int(pos[3]), int(pos[0]):int(pos[2])]
#             # P图
#             img[int(pos[1]):int(pos[3]), int(pos[0]):int(pos[2])] = p_chart(image=temp, value=28)
#             cv2_to_pil(img).show()


if __name__ == '__main__':
    path = 'D:\\ChromeCoreDownloads\\origin.jpg'
    img = Image.open(path)

# @description：把照片合成视频。

from PIL import ImageDraw, ImageFont
from flask import url_for
from moviepy.editor import *
from DataSQL.DBUtil import *


# 添加水印

def pil_add_text(img, text, position: tuple, textColor=(0, 255, 0), textSize=20):
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        url_for('static', filename='fonts/淘气黑体.ttf'), textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    return img


# 剪裁音频

def resize_bgm(bgm_path, begin, longtime) -> AudioFileClip:
    begin = float(begin)
    audioclip = AudioFileClip(bgm_path)
    if audioclip.duration < longtime:
        audioclip = afx.audio_loop(audioclip, duration=longtime)
    else:
        audioclip = audioclip.subclip(t_start=begin, t_end=begin + longtime)
    return audioclip


# 添加背景音乐

def add_music(temp_path, video_path):
    # 随机获得bgm文件
    p = url_for('static', filename='music\\music')
    l = os.listdir(p)
    index = random.randint(0, len(l) - 1)
    bgm_path = os.path.join(p, l[index])
    # 获取视频的长度
    videoclip = VideoFileClip(temp_path)
    audioclip = resize_bgm(bgm_path, 78, videoclip.duration)
    videoclip = videoclip.set_audio(audioclip)
    videoclip.write_videofile(os.path.splitext(video_path)[0] + '.mp4')
    # 删除temp文件
    os.remove(temp_path)


# 创建视频

def write_video(session, uid, file_list, style, is_add_text=True, isBgm=True, save_name=None):
    if len(file_list) == 0:
        return
    fps, size, file_list = 1.5, (800, 800), file_list
    # AVI格式编码输出 MJPG
    four_cc = cv2.VideoWriter_fourcc(*'MJPG')
    if save_name is None:
        save_name = '%d#%s#%s.avi' % (
            uid, time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time())).replace(':', '-'), style)
    save_path = url_for('static', filename='temp\\video') + '\\' + save_name
    temp_path = url_for('static', filename='temp\\temp') + '\\' + save_name
    if isBgm:
        video_writer = cv2.VideoWriter(temp_path, four_cc, float(fps), size)
    else:
        video_writer = cv2.VideoWriter(save_path, four_cc, float(fps), size)
    # 写入视频
    for item in file_list:
        name = item.name
        img = pil_open(item.content)
        img = img.resize(size, Image.ANTIALIAS)  # 重定尺寸,不变形
        if is_add_text:
            img = pil_add_text(img, str(item.datetime) + '——' + name, (size[0] - 500, size[1] - 50),
                               (79, 139, 238))  # 文字在图中的坐标(注意:这里的坐标原点是图片左上角)
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        # cv2.imshow("123",img)
        # cv2.waitKey()
        if len(img):
            video_writer.write(img)
    video_writer.release()
    cv2.destroyAllWindows()
    if isBgm:
        add_music(temp_path, save_path)


if __name__ == '__main__':
    pass

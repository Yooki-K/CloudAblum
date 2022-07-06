import threading

from sqlalchemy import func, desc

from utils import *
from PIL import Image
from io import BytesIO
from DataSQL.models import *
import API.FaceDetectionAPI as fapi
import API.ObjectDetectionAPI as oapi


def show_imq(a):
    img = Image.open(BytesIO(a))
    img.show()


def upload_img(session, user: str, file_list: list, tt, txt=None, isFromNet=False):
    """用户上传图片 直接上传至数据库"""
    imgs = []
    ttt = time.time()
    index = 0
    for x in file_list:
        if isFromNet:
            filename = x['filename'].split('.')[0]
            x = x['stream']
        else:
            filename = x.filename.split('.')[0]
            x = x.stream.read()
        classes = 'waiting'
        index = index + 1
        if tt == 3 and txt is not None:
            classes = txt
        if tt == 2 and txt is not None:
            imgs.append(
                {'user': user, 'name': filename, 'content': x, 'classes': 'human', 'facetag': txt})
        else:
            imgs.append(
                {'user': user, 'name': filename, 'content': x, 'classes': classes})
    session.execute(
        Img.__table__.insert(),
        imgs
    )
    session.commit()
    r = session.query(Img.id).filter(
        Img.user == user).order_by(desc('id')).first()
    print('上传{0}张图片，耗时：{1}秒'.format(index, time.time() - ttt))
    return r[0]


def delete_all(session, entity_list):
    for x in entity_list:
        session.delete(x)
    session.commit()


def delete(session, entity):
    if entity is None:
        return False
    session.delete(entity)
    session.commit()
    return True


def insert_all(session, entity_list):
    for x in entity_list:
        session.add(x)
    session.commit()


def group_by_date(session, u: User):
    result = {}
    r = session.query(func.date_format(Img.datetime, '%Y-%m-%d').label('date')).filter(
        Img.user == u.user, Img.deletetime == None).order_by(desc('date')).group_by('date').all()
    for x in r:
        date = x[0]
        result[date] = session.query(Img).filter(Img.user == u.user, Img.deletetime == None,
                                                 func.date_format(Img.datetime, '%Y-%m-%d') == date).all()
    print(result)
    return result


def group_by_tag(session, u: User):
    result = {}
    r = session.query(Img.facetag).filter(
        Img.user == u.user, Img.deletetime == None).group_by(Img.facetag).all()
    for x in r:
        tag = x[0]
        if tag == None or tag == '':
            continue
        else:
            result[tag] = session.query(Img).filter(Img.user == u.user, Img.deletetime == None,
                                                    Img.facetag == tag).first()
    return result


def group_by_class(session, u: User):
    result = {}
    r = session.query(Img.classes).filter(
        Img.user == u.user, Img.deletetime == None).group_by(Img.classes).all()
    for x in r:
        classes = x[0]
        if classes != "" and classes != "waiting" and classes is not None:
            result[classes] = session.query(Img).filter(Img.user == u.user, Img.deletetime == None,
                                                        Img.classes == classes).first()
    return result


def group_by_album(session, u: User):
    result = {}
    for x in session.query(Album).filter(Album.user == u.user).all():
        cover = x.imgs.first()
        if cover is None:
            cover = 'none'
        result[x.name] = cover
    return result


def group_by_special_class(session, u: User, classes):
    result = {classes: session.query(Img).filter(Img.user == u.user, Img.deletetime == None,
                                                 Img.classes == classes).all()}

    return result


def group_by_special_tag(session, u: User, classes):
    result = {classes: session.query(Img).filter(Img.user == u.user, Img.deletetime == None,
                                                 Img.facetag == classes).all()}

    return result


def group_by_special_album(session, u: User, album):
    r = session.query(Album).filter(Album.user == u.user, Album.name == album).first()
    if r is not None:
        result = {album: r.imgs.all()}
        return result
    else:
        return None


# 修改个人信息
def update_users(session, user: str, data):
    temp = data.pop('username')
    data['user'] = temp
    session.query(User).filter(User.user == user).update(data)
    session.commit()
    r = session.query(User).filter(User.user == user).first()
    return r


# 移动人脸
def update_facetag(session, u, id_list, tagName):
    old_tagName = ''
    for x in id_list:
        r = session.query(Img).filter(Img.id == x).first()
        if r is None:
            continue
        old_tagName = r.facetag
        r.facetag = tagName
        if r.faceid != None:
            rr = session.query(Img).filter(Img.facetag == r.facetag, Img.user == u.user, Img.id != r.id).first()
            if rr is not None:
                rr.faceid = r.faceid
            r.faceid = None
    session.commit()
    res = session.query(Img).filter(Img.user == u.user, Img.facetag == old_tagName).first()
    if res is None:
        return False
    else:
        return True


# 修改人脸标识face_tag
def update_tagName(session, old_tagName, new_tagName):
    session.query(Img).filter(Img.facetag == old_tagName).update({'facetag': new_tagName})
    session.commit()
    return True


# 用户创建自定义相册
def create_album(session, u: User, albumName):
    r = session.query(Album).filter(Album.name == albumName).first()
    if r is None:
        album = Album(user=u.user, name=albumName)
        session.add(album)
        session.commit()
        return True
    else:
        return False


# 用户删除自定义相册 已级联删除相关关联
def delete_album(session, u: User, album_name):
    session.query(Album).filter(Album.name == album_name).delete()
    session.commit()


# 用户相册添加照片
def add_imgs(session, id_list, album_name):
    a = session.query(Album).filter(Album.name == album_name).first()
    if a is None:
        return
    for x in id_list:
        r = session.query(Img).filter(Img.id == x).first()
        if r is not None:
            a.imgs.append(r)
    session.commit()


# 用户相册移动照片
def move_imgs(session, id_list, album_name1, album_name2):
    a = session.query(Album).filter(Album.name == album_name1).first()
    b = session.query(Album).filter(Album.name == album_name2).first()
    if a is None:
        return
    for x in id_list:
        r = session.query(Img).filter(Img.id == x).first()
        if r is not None:
            a.imgs.remove(r)
            b.imgs.append(r)
    session.commit()


# 用户相册移除照片
def remove_imgs(session, id_list, album_name):
    a = session.query(Album).filter(Album.name == album_name).first()
    if a is None:
        return
    for x in id_list:
        r = session.query(Img).filter(Img.id == x).first()
        if r is not None:
            a.imgs.remove(r)
    session.commit()


# 用户相册重命名
def rename_album(session, name1, name2):
    r = session.query(Album).filter(Album.name == name2).first()
    if r is not None:
        return False
    r = session.query(Album).filter(Album.name == name1).first()
    r.name = name2
    session.commit()
    return True


# 回收站
def recycle_bin(session, u: User):
    """返回[{'delete_time','left_time','id','name','content'}]"""
    r = session.query(Img).filter(Img.user == u.user, Img.deletetime != None).all()
    now = dt.now().replace(microsecond=0)
    mes_list = []
    for x in r:
        d = {}
        left = now - x.deletetime
        d['delete_time'] = x.deletetime
        d['left_time'] = '剩余{}天'.format(10 - left.days)
        d['id'] = x.id
        d['name'] = x.name
        d['content'] = x.content
        mes_list.append(d)
    return mes_list


# 回收站还原
def restore_img(session, u: User, id_list):
    for x in id_list:
        r = session.query(Img).filter(Img.id == x).first()
        if r is not None:
            r.deletetime = None
    session.commit()


def insert(session, entity):
    session.add(entity)
    session.commit()


# 搜索人脸
def search_face(session, user, imageFile, confidence=0.5):
    f = fapi.FaceAPI()
    r = session.query(Img).filter(Img.user == user, Img.deletetime == None, Img.faceid != None).all()  # 人脸库
    max_m = -1
    faceid = None
    facetag = None
    for x in r:
        result = f.match_face(x.content, imageFile)
        print(x.name, result)
        if result is not None and result >= confidence and result > max_m:
            max_m = result
            faceid = x.faceid
            facetag = x.facetag
    if max_m == -1:
        return None
    else:
        return [faceid, facetag]


# 自动分类人物
def classification(session, u: User):
    f = fapi.FaceAPI()
    tt = time.time()
    while True:
        img = session.query(Img).filter(Img.user == u.user, Img.facetag == '其它', Img.classes == 'human',
                                        Img.faceid == None,
                                        Img.deletetime == None).first()
        if img is not None:
            print(img.name)
            r = search_face(session=session, user=u.user, imageFile=img.content)
            if r is None:  # 新增人脸
                while True:
                    new = f.add_face()
                    temp = session.query(Img).filter(Img.faceid == new, Img.deletetime == None).first()
                    if temp is None:
                        break
                img.facetag = new
                img.faceid = new
            else:  # 更改facetag
                img.facetag = r[1]
            session.commit()
        else:
            break
    print('分类结束，耗时：', time.time() - tt)


# 检测图片
def detection_img(session_, users_):
    """对用户上传图片进行后台检测 :物体识别 -> 人脸检测 -> 智能分类"""

    def doIt(session, users):
        f = fapi.FaceAPI()
        o = oapi.ObjectAPI()
        for u in users:
            tt = time.time()
            print("{0}用户{1}开始检测".format(u.name, tt))
            images = session.query(Img).filter(Img.user == u.user, Img.classes == 'waiting',
                                               Img.deletetime == None).all()
            for x in images:
                f_stream = x.content
                classes = None
                if len(f_stream) < 3 * 1024 * 1024:  # 图片小于3MB，可上传
                    r1 = f.face_detection(f_stream)
                    if r1 > 0:
                        classes = 'human'
                    else:
                        classes = o.object_detection(f_stream)
                        print(classes)
                        # 物体检测代码
                x.classes = classes
                x.faceid = None
                x.facetag = '其它'
                session.commit()
            print('{}检测结束,耗时{}秒'.format(time.time(), time.time() - tt))
            classification(session=session, u=u)

    t = threading.Thread(target=doIt, args=(session_, users_))
    t.setDaemon(True)
    t.start()


# ! 图片放入回收站
def delete_img(session, u: User, img_id: list):  # todo
    f = fapi.FaceAPI()
    for x in img_id:
        img = session.query(Img).filter(Img.id == x).first()
        if img is None:
            continue
        if img.faceid != None:
            rr = session.query(Img).filter(Img.facetag == img.facetag, Img.user == u.user, Img.id != img.id,
                                           Img.deletetime == None).first()
            if rr is not None:
                rr.faceid = img.faceid
            img.faceid = None
        img.deletetime = dt.now()
    session.commit()


# 删除回收站内超过10天的图片
def delete_timeout(session, u: User = None, isAll=False):
    now = dt.now().replace(microsecond=0)
    if u is not None:
        r = session.query(Img).filter(Img.deletetime != None, Img.user == u.user).all()
        num = len(r)
        if not isAll:
            num = 0
            for x in r:
                if (now - x.deletetime).days >= 10:
                    session.delete(x)
                    num += 1
        else:
            for x in r:
                session.delete(x)
        print(num)
        session.commit()
        return num
    else:
        r = session.query(Img).filter(Img.deletetime != None).all()
        for x in r:
            session.delete(x)
        session.commit()
        return


# 精彩一刻
# def aiVideo(session, u: User):
#     styles = ['可爱宝贝', '美食一刻', '萌宠当家', '我爱动漫']
#     styles_of_labels = {styles[0]: [['孩子', '学步的儿童'], []], styles[1]: [['食物', '菜式'], []], styles[2]: [['狗'], []],
#                         styles[3]: [['漫画', '日本动画片', '漫画草图'], []]}
#     r = session.query(Img).filter(Img.user == u.user, Img.deletetime == None, Img.description != None).all()
#     for x in r:
#         description = x.description.split(' ')
#         for y in styles_of_labels:
#             if len(set(description).intersection(set(styles_of_labels[y][0]))) > 0:
#                 styles_of_labels[y][1].append(x)
#
#     return styles_of_labels
def aiVideo(session, u: User):
    r = session.query(Img.facetag).filter(Img.user == u.user).group_by(Img.facetag).all()
    styles = [x.facetag for x in r]
    styles_of_labels = {}
    for x in styles:
        styles_of_labels[x] = []
    r = session.query(Img).filter(Img.user == u.user, Img.deletetime == None, Img.facetag != None).all()
    for x in r:
        styles_of_labels[x.facetag].append(x)
    return styles_of_labels

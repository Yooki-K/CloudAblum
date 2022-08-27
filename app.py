import re
import requests
from datetime import timedelta
from json import JSONEncoder

from flask import *
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

# from EditPhoto.imgToVedio import *

app = Flask(__name__)
from DataSQL.DBUtil import *
from EditPhoto.EditImg import *
from flask_cors import cross_origin

# git config --global http.sslVerify "false"


'''配置数据库'''
app.config['SECRET_KEY'] = 'hard to guess'  # 一个字符串，密码。也可以是其他如加密过的

# 在此登录的是root用户，要填上密码如123456，MySQL默认端口是3306。并填上创建的数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(CONF.get('mysql', 'root'),
                                                                                     CONF.get('mysql', 'passwd'),
                                                                                     CONF.get('mysql', 'host'),
                                                                                     CONF.get('mysql', 'port'),
                                                                                     CONF.get('mysql', 'db')
                                                                                     )

# 设置下方这行code后，在每次请求结束后会自动提交数据库中的变动
# app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# 设置session过期时间为7天
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
# 配置邮箱
app.config.update(
    DEBUG=True,
    MAIL_SERVER=CONF.get('mail', 'MAIL_SERVER'),
    MAIL_PROT=CONF.getint('mail', 'MAIL_PORT'),
    MAIL_USE_TLS=CONF.getboolean('mail', 'MAIL_USE_TLS'),
    MAIL_USE_SSL=CONF.getboolean('mail', 'MAIL_USE_SSL'),
    MAIL_USERNAME=CONF.get('mail', 'MAIL_USERNAME'),
    MAIL_PASSWORD=CONF.get('mail', 'MAIL_PASSWORD')
)


def tag_list(userid, tt, op='add'):
    user = db.session.query(User.user).filter(User.id == userid).first()[0]
    if tt == 2 and op == 'move':  # 获得人物tag列表
        r = db.session.query(Img.facetag).filter(Img.user == user).group_by(Img.facetag).all()
        l = []
        for x in r:
            if x.facetag is None:
                l.append('其它')
            else:
                l.append(x.facetag)
        r = l
    elif tt == 4 or tt == 1 or tt == 2:  # 获得相册列表
        r = db.session.query(Album.name).filter(Album.user == user).all()
        r = [x[0] for x in r]
        pass
    else:
        r = []
        pass
    return r


# 编写自己的json编码器，并继承原有的
class MyJSONEncoder(JSONEncoder):
    # 在jsonify中不能直接序列化该类型的时候，才会调用default方法，并进入分类执行
    def default(self, obj):
        if isinstance(obj, User):
            # 自定义返回字典
            return dict(obj)
        if isinstance(obj, Img):
            # 自定义返回字典
            temp = dict(obj)
            temp['content'] = ImgHandler.getBase64(temp['content'])
            temp.pop('datetime')
            return temp
        return super(MyJSONEncoder, self).default(obj)


def addone(i, l):
    if i >= l:
        i = 0
    else:
        i = i + 1
    return i


app.json_encoder = MyJSONEncoder  # 将自定义的json编码器赋给flask原有的
db = SQLAlchemy(app)  # 实例化数据库对象，它提供访问Flask-SQLAlchemy的所有功能
mail = Mail(app)  # 实例化邮件对象
# jinja调用自定义函数
app.jinja_env.globals.update(getbase64=ImgHandler.getBase64)
app.jinja_env.globals.update(tagList=tag_list)
app.jinja_env.globals.update(list=list)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(addone=addone)


# 登录界面，发送
@app.route('/sign-in-page', methods=('GET', 'POST'))
def sign_in_page():
    if session.get('User') is not None:
        result1 = session.get('User')
        result2 = db.session.query(User).filter(User.user == result1['user']).first()
        if result2 is not None:
            return redirect(url_for('index', userid=result1['id'], tt=1))
        else:
            session.clear()
            return render_template("sign_in.html")
    else:
        return render_template('sign_in.html')


# 登录   username -用户名 pwd -登录密码 rem -七天内自动登录
@app.route('/sign-in', methods=['post'])
def sign_in():
    user = request.form.get('username')
    pwd = request.form.get('pwd')
    rem = request.form.get('rem')
    result = db.session.query(User).filter(User.user == user).first()
    if result is None:
        return render_template('message.html', title='Error', state_code=404, mes='该用户不存在',
                               action='signing in fails!!!',
                               back=url_for('sign_in_page'))
    if result.pwd != pwd:
        return render_template('message.html', title='Error', state_code="登录失败", mes='密码错误',
                               action='signing in fails!!!', back=url_for('sign_in_page'))
    session['User'] = result
    if rem == 'on':
        session.permanent = True  # 设置session永久有效(7天内免登录)
    return redirect(url_for('index', userid=result['id'], tt=1))


# 注册
@app.route('/operate/users/<string:t>', methods=['post'])
def operateUsers(t):
    user = request.form.get('username')
    name = request.form.get('name')
    pwd = request.form.get('pwd')
    code = request.form.get('code')
    sendType = request.form.get('sendType')
    if sendType is str:
        sendType = int(sendType)
    if t == 'update':
        file = request.files.get('avatar')
        r = request.form.to_dict()
        c = file.stream.read()
        if len(c) != 0:
            r['avatar'] = c
        rr = update_users(db.session, user, r)
        session.pop('User')
        session['User'] = rr
        return jsonify({'state': True, 'mes': '操作成功'})
        pass
    result = db.session.query(Code).filter(Code.user == user, Code.sendType == sendType).first()
    if result is None:
        return jsonify({'state': False, 'mes': '验证码发送失败'})
    real_code = result.code
    st_time = result.sendTime
    if int(time.time()) > st_time + 60:  # 超时
        return jsonify({'state': False, 'mes': '超时，验证码已失效'})
    if code != real_code:
        return jsonify({'state': False, 'mes': '验证码错误'})
    # 验证码正确
    db.session.delete(result)
    db.session.commit()
    if t == 'add':
        while True:
            facesetid = generate_random_str(6)
            f = db.session.query(User).filter(facesetid == facesetid).first()
            if f is not None:
                break
        user = User(user=user, pwd=pwd, name=name, facesetid=facesetid)
        db.session.add(user)
        db.session.commit()
    if t == 'forget':
        session.pop('User')
        session['User'] = update_users(db.session, user, request.form.to_dict())
    return jsonify({'state': True, 'mes': '操作成功'})


# 登出页面
@app.route('/logout', methods=['get'])
def logout():
    if session.get('User') is not None:
        session.pop('User')
    return redirect(url_for('sign_in_page'))


# 获得用户个人信息
@app.route('/get/user', methods=['POST'])
def getUser():
    u = session.get('User')
    if u is not None:
        r = db.session.query(User).filter(User.user == u['user']).first()
        rr = {
            'user': r.user,
            'name': r.name,
            'pwd': r.pwd,
            'avatar': r.avatar,
            'facesetid': r.facesetid
        }
        if r.avatar is not None and len(r.avatar) != 0:
            rr['avatar'] = ImgHandler.getBase64(r.avatar)
        return jsonify(rr)
    else:
        return redirect(url_for('sign_in_page'))


# 用户主界面
@app.route('/<int:userid>/index/<int:tt>', methods=['GET'])
def index(userid, tt):
    u = session.get('User')
    if u is not None:
        path = []
        u = User.from_dict(u)
        # if u.id == userid:
        #     name_list = os.listdir('static/temp/video')
        #     p = '{}#'.format(u.id)
        #     for x in name_list:
        #         r = re.search(p, x)
        #         if r is not None:
        #             path.append('static/temp/video/' + x)
        #             # path.append(url_for('static', filename='temp/video/' + x))
        r = None
        tttt = time.time()
        if tt == 1:  # 按天分类
            return render_template("index.html", userid=userid, username=u.name, tt=tt, path=path)
        elif tt == 2:  # 按人物标签分类
            r = group_by_tag(db.session, u)
            print(time.time() - tttt)
            return render_template("face_album.html", userid=userid, username=u.name, file_list=r, tt=tt, path=path)
        elif tt == 3:  # 按分类标签分类
            r = group_by_class(db.session, u)
            print(time.time() - tttt)
            return render_template("album.html", userid=userid, username=u.name, file_list=r, tt=tt, path=path)
        elif tt == 4:  # 按相册分类
            r = group_by_album(db.session, u)
            print(time.time() - tttt)
            return render_template("album.html", userid=userid, username=u.name, file_list=r, tt=tt, path=path)
        return render_template("index.html", userid=userid, username=u.name, file_list=r, tt=tt, path=path)
    else:
        return redirect(url_for('sign_in_page'))


# 获取上传图像
@app.route('/getImageBefore', methods=['POST'])
def getSpecialImageBefore():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        r = None
        tt = request.json.get('tt')
        if tt == 1:  # 按天分类
            r = group_by_date(db.session, u, '', 0, 'before')
        else:
            classes = request.json.get('label')
            if tt == 2:
                r = group_by_special_tag(db.session, u, classes, 0, 'before')  # {'',[] }
                if len(r['data']) == 0:
                    r = {}
            elif tt == 3:
                r = group_by_special_class(db.session, u, classes, 0, 'before')
            elif tt == 4:
                r = group_by_special_album(db.session, u, classes, 0, 'before')
                if r is None:
                    r = {}
        return r
    else:
        return {}


# 获取上传图像
@app.route('/getImage', methods=['POST'])
def getSpecialImage():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        r = None
        tt = request.json.get('tt')
        index = request.json.get('index')
        label = request.json.get('label')
        tttt = time.time()
        if tt == 1:  # 按天分类
            r = group_by_date(db.session, u, label, index, '')
        else:
            if tt == 2:
                r = group_by_special_tag(db.session, u, label, index, '')  # {'',[] }
                if len(r['data']) == 0:
                    r = {}
            elif tt == 3:
                r = group_by_special_class(db.session, u, label, index, '')
            elif tt == 4:
                r = group_by_special_album(db.session, u, label, index, '')
                if r is None:
                    r = {}
        print(time.time() - tttt)

        return r
    else:
        return {}


# 操作用户自定义相册
@app.route('/operate/album/<string:t>', methods=['POST'])
def operate_album(t):
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        if t == 'create':
            name = request.json.get('albumName')
            if name is None:
                return '相册名为空请重新命名'
            r = create_album(db.session, u, name)
            if not r:
                return '该相册已存在，请重新命名'
        elif t == 'delete':
            name = request.json.get('albumName')
            delete_album(db.session, u, name)
        elif t == 'move':
            name1 = request.json.get('albumName1')
            name2 = request.json.get('albumName2')
            id_list = request.json.get('id_list')
            move_imgs(db.session, u, id_list, name1, name2)
        elif t == 'add':
            id_list = request.json.get('id_list')
            name = request.json.get('albumName')
            add_imgs(db.session, u, id_list, name)
        elif t == 'remove':
            id_list = request.json.get('id_list')
            name = request.json.get('albumName')
            remove_imgs(db.session, u, id_list, name)
        elif t == 'rename':
            name1 = request.json.get('albumName1')
            name2 = request.json.get('albumName2')
            r = rename_album(db.session, u, name1, name2)
            if not r:
                return '该相册已存在,请重新命名'
        else:
            return '操作失败'
        return '操作成功'
    else:
        return "请登录"


@app.route('/<int:userid>/album/<int:tt>/<string:classes>', methods=['GET'])
def album_class(userid, tt, classes):
    u = session.get('User')
    u = User.from_dict(u)
    if tt == 2 or tt == 3:
        return render_template("index.html", userid=userid, username=u.name, tt=tt, classes=classes)
    elif tt == 4:
        return render_template("index.html", userid=userid, username=u.name, tt=4, albumName=classes)


# 发送邮件
@app.route("/mail", methods=['post'])
def send_mail():
    # sender 发送方，recipients邮件接收方列表 cloudalbum_xfy@163.com网易发送不出去
    email = request.json.get('email')
    sendType = request.json.get('sendType')
    msg = Message(subject="小福言-云相册", sender='1486147017@qq.com', recipients=[email])
    # 删除此前发送验证码
    result = db.session.query(Code).filter(Code.user == email, Code.sendType == sendType).all()
    delete_all(db.session, result)
    r = generate_random_str(4)
    msg.body = '欢迎注册小福言-云相册，您的验证码为 %s。一分钟后失效。-- %s' % (r, dt.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        mail.send(msg)
    except Exception as e:
        print("send error：" + str(e))
        return jsonify({'result': "error", 'mes': '发送验证码失败'})
    else:
        ecode = Code(user=email, code=r, sendType=sendType, sendTime=int(time.time()))
        insert(db.session, ecode)
        return jsonify({'result': 'success', 'mes': '登录成功'})


# 显示用户图片
@app.route('/<int:userid>/Image/<int:imgid>', methods=['post', 'get'])
def showImage(userid, imgid):
    u = session.get('User')
    if u is not None:
        result = db.session.query(Img).filter(Img.id == imgid).first()
        if result is not None and u['id'] == userid and result.user == u['user']:
            return render_template("show_image.html", img=result)
        else:
            return render_template('message.html', title='Error', state_code=404, mes='当前资源不存在',
                                   action='{0} don\'t exist!!!'.format(request.url),
                                   back=url_for('index', userid=userid, tt=1))
    else:
        return redirect(url_for('sign_in_page'))


# 对图片进行P图
@app.route('/editImage/<type>', methods=['post'])
def editImage(type):
    """type 1素描 2手绘 3磨皮"""
    type = int(type)
    img_id = request.json.get('id')
    image = db.session.query(Img).filter(Img.id == img_id).first()
    t = ImgHandler.getType(image.content)
    if type == 1:
        depth = int(request.json.get('depth'))
        image_base = ImgHandler.getBase64(pil_to_bits(to_sketch_pil(pil_open(image.content), depth), t), t)
    elif type == 2:
        image_base = ImgHandler.getBase64(cv_to_bits(to_freehand_cv(cv_open(image.content)), t), t)
    else:
        image_base = ImgHandler.getBase64(cv_to_bits(p_chart_cv(cv_open(image.content)), t), t)
    return image_base


@app.route('/renameImage', methods=['post'])
def renameImage():
    img_id = request.json.get('id')
    img_name = request.json.get('name')
    image = db.session.query(Img).filter(Img.id == img_id).first()
    image.name = img_name
    db.session.commit()
    return '更改\'%s\'成功' % img_name


# 批量移入回收站
@app.route('/deleteImage', methods=['post'])
def deleteImage():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        img_id = request.json.get('id')
        if type(img_id) is list:
            delete_img(db.session, u, img_id)
        else:
            delete_img(db.session, u, [img_id])
        return "已移入回收站，十天后删除"
    else:
        return redirect(url_for('sign_in_page'))


# app.route('/<int:userid>/videos')
# def get_videos(userid):
#     u = session.get('User')
#     if u is not None:
#         u = User.from_dict(u)
#         if u.id == userid:
#             name_list = os.listdir('static/temp/video')
#             p = '{}_'.format(u.id)
#             path = []
#             for x in name_list:
#                 r = re.search(p, x)
#                 if r is not None:
#                     print(r)
#                     print(x)
#                     path.append('temp/video/' + x)
#             return render_template('video.html', path=path)
#         else:
#             return render_template('message.html', title='Error', state_code=404, mes='当前资源不存在',
#                                    action='{0} don\'t exist!!!'.format(request.url),
#                                    back=url_for('index', userid=userid))
#     else:
#         return redirect(url_for('sign_in_page'))


# 自动分类
@app.route('/classify', methods=['post', 'get'])
def classify():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        thread1 = threading.Thread(target=detection_img, args=(db.session, [u]), daemon=True, name="检测_" + str(u.id))
        thread1.start()
        # clearVideos(u)
        # createVideos(u)
        return {"threadName": "检测_" + str(u.id)}
    else:
        return '请登录'


# 判断检测是否结束
@app.route('/judgeclassify', methods=['post'])
def judgeIsFinished():
    name = request.json.get('threadName')
    for x in threading.enumerate():
        if x.name == name:
            return {'isFinished': False}
    return {'isFinished': True}


# 清空回收站
def clear():
    delete_timeout(db.session)
    return '清空回收站完成'


# 显示回收站页面
@app.route('/<int:userid>/recycle')
def recycle(userid):
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        if u.id == userid:
            results = recycle_bin(session=db.session, u=u)
            return render_template('recycle.html', file_list=results, userid=userid, username=u.name)
        else:
            return render_template('message.html', title='Error', state_code=404, mes='当前资源不存在',
                                   action='{0} don\'t exist!!!'.format(request.url),
                                   back=url_for('index', userid=userid, tt=1))
    else:
        return redirect(url_for('sign_in_page'))


# 还原回收站
@app.route('/restore', methods=['post'])
def restoreImgs():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        img_id = request.json.get('id')
        if type(img_id) is list:
            restore_img(db.session, u, img_id)
        else:
            restore_img(db.session, u, [img_id])
        return "已移入回收站，十天后删除"
    else:
        return redirect(url_for('sign_in_page'))


# 修改标签
@app.route('/update/facetag/<int:t>', methods=['post'])
def update_tag(t):
    u = session.get('User')
    if u is None:
        return 'fail,请登录'
    u = User.from_dict(u)
    tag1 = request.json.get('old_tagName')
    tag2 = request.json.get('new_tagName')
    print(tag1, tag2)
    if t == 1:  # 修改人脸标签
        update_tagName(db.session, u, tag1, tag2)
        return '修改成功！'
    elif t == 3:  # 移动
        id_list = request.json.get('id_list')
        if update_facetag(db.session, u, id_list, tag2):
            return request.referrer
        else:
            return url_for('index', userid=u.id, tt=2)


# 批量下载图片
@app.route('/download/images/<int:id>')
def download(id):
    r = db.session.query(Img).filter(Img.id == id).first()
    print(id)
    if r is not None:
        response = make_response(r.content)
        response.headers["Pragma"] = "public"
        response.headers["Expires"] = "0"
        response.headers["Cache-Control"] = "must-revalidate, post-check=0, pre-check=0"
        response.headers["Content-Type"] = "application/force-download"
        response.headers["Content-Disposition"] = "attachment;filename={}.{}".format(urllib.parse.quote(r.name),
                                                                                     ImgHandler.getType(r.content))
        response.headers["Content-Transfer-Encoding"] = "binary"
    else:
        response = make_response('', 404)
    return response


# 批量上传图片
@app.route('/upload/<int:tt>/<string:txt>', methods=['POST'])
def upload(tt, txt):
    u = session.get('User')
    u = User.from_dict(u)
    files = request.files.values()
    if tt == 2 or tt == 3:
        lastId = upload_img(db.session, u.user, files, tt, txt)
    else:
        lastId = upload_img(db.session, u.user, files, tt, None)
    if tt == 4:
        add_imgs(db.session, u, [lastId], txt)
    return jsonify({'upload': True})


# # 生成精彩一刻视频
# def createVideos(u):
#     print('开始生成视频')
#     return  # todo videos
#     styles = aiVideo(session=db.session, u=u)
#     i = 0
#     for x in styles:
#         write_video(db.session, u.id, styles[x], i, False, False)
#         i = i + 1
#
#
# # 清理精彩一刻视频
# def clearVideos(u):
#     path = 'static/temp/video'
#     # path = url_for('static', filename='temp/video')
#     p = re.compile("{}_".format(u.id))
#     for x in os.listdir(path):
#         r = re.search(p, x)
#         if r is not None and r.regs[0][0] == 0:
#             os.remove(os.path.join(path, x))


# 手动清空回收站
@app.route('/clear', methods=['post'])
def clear_recycle():
    print('清空回收站')
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        return str(delete_timeout(db.session, u, True))
    else:
        return '请先登录'


@app.route('/addImageFromUrl', methods=['post', 'get'])
@cross_origin()
def addImageFromUrl():
    if request.method == 'GET':
        return ''
    else:
        hhh = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38',
        }
        txt = request.data.decode()
        data = []
        txts = txt.split(',,,')
        facesetid = txts.pop(0)
        u = db.session.query(User).filter(facesetid == facesetid).first()
        for x in txts:  # todo 插件API
            d = {}
            if 'data:image' in x:
                a = x.split('base64,')[1]
                d['filename'] = a[:7]
                d['stream'] = decode(a)
                data.append(d)
            if 'http' in x:
                temp = x.split('/')[-1]
                d['filename'] = re.findall('(.*?)\.', temp)[0]
                r = requests.get(url=x, headers=hhh, timeout=10)
                if '<!DOCTYPE html>' not in r.text:
                    d['stream'] = r.content
                    data.append(d)
        upload_img(db.session, u.user, data, 10, None, True)
        return '成功'


@app.route('/', methods=['GET', 'POST'])
def mainPage():
    return redirect(url_for('sign_in_page'))


if __name__ == '__main__':
    delete_timeout(db.session)
    # reset()
    app.run(host='127.0.0.1', port=80)
    pass

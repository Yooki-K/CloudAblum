import re
import os
from datetime import timedelta
from json import JSONEncoder
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask import *

# from API.FaceDetectionAPI import face_recognition
from EditPhoto.imgToVedio import *

app = Flask(__name__)

from DataSQL.DBUtil import *
from EditPhoto.EditImg import *

# from EditPhoto.imgToVedio import *

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
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
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


def tag_list(userid, tt):
    user = db.session.query(User.user).filter(User.id == userid).first()[0]
    if tt == 3:  # 获得人物tag列表
        r = db.session.query(Img.facetag).filter(Img.user == user).group_by(Img.facetag).all()
        print(r)
        r = [x.facetag for x in r]
    elif tt == 4 or tt == 1:  # 获得相册列表
        r = db.session.query(Ablum.name).filter(Ablum.user == user).all()
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


# 清除session
@app.route('/remove')
def remove():
    if session.get('User') is not None:
        session.pop('User')
    return redirect(url_for('sign_in_page'))


# 登录界面，发送
@app.route('/sign-in-page', methods=('GET', 'POST'))
def sign_in_page():
    if session.get('User') is not None:
        result = session.get('User')
        return redirect(url_for('index', userid=result['id'], tt=1))
    else:
        return render_template('login/sign_in.html')


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


# 注册页面
@app.route('/sign-up-page')
def sign_up_page():
    return render_template('login/sign_up.html')


# 注册
@app.route('/sign-up', methods=['post'])
def sign_up():
    user = request.form.get('username')
    name = request.form.get('name')
    pwd = request.form.get('pwd')
    code = request.form.get('code')
    result = db.session.query(Code).filter(Code.user == user, Code.sendType == -1).first()
    if result is None:
        return render_template('message.html', title='Error', state_code=404, mes='验证码发送失败',
                               action='signing up fails!!!',
                               back=url_for('sign_up_page'))
    real_code = result.code
    st_time = result.sendTime
    if int(time.time()) > st_time + 60:  # 超时
        return render_template('message.html', title='Error', state_code=403, mes='超时，验证码已失效',
                               action='signing up fails!!!',
                               back=url_for('sign_up_page'))
    if code != real_code:
        return render_template('message.html', title='Error', state_code='注册失败', mes='验证码错误',
                               action='signing up fails!!!',
                               back=url_for('sign_up_page'))
    # 验证码正确
    f = fapi.FaceAPI()
    f.get_token()
    result = f.create_face_set(name)
    if result is None:
        return render_template('message.html', title='Error', state_code=403, mes='网络拥堵', action='signing up fails!!!',
                               back=url_for('sign_up_page'))
    else:
        facesetid = result
        user = User(user=user, pwd=pwd, name=name, facesetid=facesetid)
        db.session.add(user)
        db.session.commit()
        print(user)
        return render_template('login/sign_up_ok.html')


# 登出页面
@app.route('/logout', methods=['get'])
def logout():
    # 清空session
    session.clear()
    return render_template("login/sign_in.html")


# 忘记密码
@app.route('/forget-pwd-page')
def forget_pwd_page():
    return render_template('forget_pwd.html')


# 用户主界面
@app.route('/<int:userid>/index/<int:tt>', methods=('GET', 'POST'))
def index(userid, tt):
    u = session.get('User')
    if u is not None:
        path = []
        u = User.from_dict(u)
        if u.id == userid:
            name_list = os.listdir('static/temp/video')
            p = '{}#'.format(u.id)
            for x in name_list:
                r = re.search(p, x)
                if r is not None:
                    path.append('static/temp/video/' + x)
                    # path.append(url_for('static', filename='temp/video/' + x))
        r = None
        if tt == 1:  # 按天分类
            r = group_by_date(db.session, u)
        elif tt == 2:  # 按人物标签分类
            r = group_by_tag(db.session, u)
            return render_template("face_album.html", userid=userid, username=u.name, file_list=r, type=1, path=path)
        elif tt == 3:
            r = group_by_class(db.session, u)
            return render_template("album.html", userid=userid, username=u.name, file_list=r, type=2, path=path)
        elif tt == 4:
            r = group_by_album(db.session, u)
            return render_template("album.html", userid=userid, username=u.name, file_list=r, type=3, path=path)
        return render_template("index.html", userid=userid, username=u.name, file_list=r, tt=tt, path=path)
    else:
        return redirect(url_for('sign_in_page'))


# 操作用户自定义相册
@app.route('/operate/ablum/<string:t>', methods=['POST'])
def operate_ablum(t):
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        if t == 'create':
            name = request.form.get('ablumName')
            r = create_ablum(db.session, u, name)
            if not r:
                return '该相册已存在，请重新命名'
        elif t == 'delete':
            name = request.json.get('ablumName')
            delete_ablum(db.session, u, name)
        elif t == 'add':
            id_list = request.json.get('id_list')
            name = request.json.get('ablumName')
            add_imgs(db.session, id_list, name)
        elif t == 'remove':
            id_list = request.json.get('id_list')
            name = request.json.get('ablumName')
            remove_imgs(db.session, id_list, name)
        elif t == 'rename':
            name1 = request.json.get('ablumName1')
            name2 = request.json.get('ablumName2')
            r = rename_ablum(db.session, name1, name2)
            if not r:
                return '该相册已存在,请重新命名'
        else:
            return '操作失败'
        return '操作成功'
    else:
        return "请登录"


@app.route('/<int:userid>/album/<int:tt>/<string:classes>', methods=('GET', 'POST'))
def album_class(userid, tt, classes):
    u = session.get('User')
    u = User.from_dict(u)
    if tt == 3:
        r = group_by_special_tag(db.session, u, classes)
        return render_template("index.html", userid=userid, username=u.name, file_list=r, tt=3)
    elif tt == 4:
        r = group_by_special_class(db.session, u, classes)
        return render_template("index.html", userid=userid, username=u.name, file_list=r, tt=5)
    elif tt == 5:
        r = group_by_special_ablum(db.session, u, classes)
        if r is None:
            return render_template('message.html', title='Error', state_code=404, mes='当前资源不存在',
                                   action='{0} don\'t exist!!!'.format(classes),
                                   back=url_for('index', userid=userid, tt=1))
        else:
            return render_template("index.html", userid=userid, username=u.name, file_list=r, tt=4)
    else:
        return 'error'


# 发送邮件
@app.route("/mail", methods=['post'])
def send_mail():
    # sender 发送方，recipients邮件接收方列表 cloudablum_xfy@163.com网易发送不出去
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
        print("send error" + str(e))
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


@app.route('/<int:userid>/videos')
def get_videos(userid):
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        if u.id == userid:
            name_list = os.listdir('static/temp/video')
            p = '{}#'.format(u.id)
            path = []
            for x in name_list:
                r = re.search(p, x)
                if r is not None:
                    path.append('temp/video/' + x)
            return render_template('video.html', path=path)
        else:
            return render_template('message.html', title='Error', state_code=404, mes='当前资源不存在',
                                   action='{0} don\'t exist!!!'.format(request.url),
                                   back=url_for('index', userid=userid))
    else:
        return redirect(url_for('sign_in_page'))


# 自动分类
@app.route('/classify', methods=['post', 'get'])
def classify():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        thread1 = threading.Thread(target=detection_img, args=(db.session, [u]), daemon=True, name="检测_" + str(u.id))
        thread1.start()
        clearVideos(u)
        createVideos(u)
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
            return render_template('recycle.html', file_list=results, userid=userid)
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
    tag1 = request.form.get('old_tagName')
    tag2 = request.form.get('new_tagName')
    if t == 1:  # 修改人脸标签
        result = update_tagName(db.session, tag1, tag2)
        if not result:
            return '该人物label已存在'
    elif t == 3:  # 移动
        id_list = request.json.get('id_list')
        tag2 = request.json.get('new_tagName')
        update_facetag(db.session, u, id_list, tag2)
    return redirect(url_for('index', userid=u.id, tt=2))


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
@app.route('/upload', methods=['POST'])
def upload():
    u = session.get('User')
    u = User.from_dict(u)
    files = request.files.values()
    upload_img(db.session, u, files)
    return jsonify({'upload': True})


# 生成精彩一刻视频
def createVideos(u):
    styles = aiVideo(session=db.session, u=u)
    for x in styles:
        write_video(db.session, u.id, styles[x][1], x, False, False)


# 清理精彩一刻视频
def clearVideos(u):
    path = 'static/temp/video'
    # path = url_for('static', filename='temp/video')
    p = re.compile("{}#".format(u.id))
    for x in os.listdir(path):
        r = re.search(p, x)
        if r is not None and r.regs[0][0] == 0:
            os.remove(os.path.join(path, x))


# 手动清空回收站
@app.route('/clear', methods=['POST'])
def clear_recycle():
    u = session.get('User')
    if u is not None:
        u = User.from_dict(u)
        return str(delete_timeout(session, u))
    else:
        return '请先登录'


#
# @app.route('/face/compare', methods=['GET', 'POST'])
# def faceCompared():
#     files = request.files.getlist("files")
#     face = face_recognition()
#     goal = face.score_api(files)
#     print(goal)
#     if goal < 0.6:
#         return "同一人"
#         # return True
#     else:
#         return "非同一人"
#         # return False
#
#
# @app.route('/face/detection', methods=['GET', 'POST'])
# def faceDetect():
#     files = request.files.getlist('files')
#     face = face_recognition()
#     faceNumList = face.face_detect_api(files[0].stream.read())
#     # return faceNumList
#     return str(faceNumList)
#
#
@app.route('/', methods=['GET', 'POST'])
def mainPage():
    return redirect(url_for('sign_in_page'))


# end


if __name__ == '__main__':
    # delete_timeout(db.session)
    # detection_img(db.session, db.session.query(User).all())
    # app.run(host='192.168.1.11', port=80, debug=True)
    # reset()
    app.run(host='127.0.0.1', port=80)
    pass

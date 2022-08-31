from datetime import datetime as dt
from app import db


class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    pwd = db.Column(db.String(64))
    avatar = db.Column(db.LargeBinary(length=65536))  # 二进制图片流 头像
    # points = db.Column(db.Integer, default=0)
    # space = db.Column(db.Integer, default=1024 * 1024 * 1024)  # 内存初始1GB
    # excluded = db.Column(db.Integer, default=0)
    imgs = db.relationship('Img', backref='master', lazy='dynamic')
    albums = db.relationship('Album', backref='myalbums', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.user)

    # dict(user)，会先调用keys方法，这里重写，自定义获取返回的字段
    def keys(self):
        return ['id', 'user', 'name', 'pwd']

    # dict(user)获取完字段后，会取出对应字段的值，这里使用__getitem__，这里getattr(self, item)拿到值信息，item为key名
    def __getitem__(self, item):
        return getattr(self, item)

    @staticmethod
    def from_dict(u: dict):
        return User(user=u['user'], id=u['id'], name=u['name'])


tb_album_img = db.Table('album_img',
                        db.Column('imgid', db.Integer, db.ForeignKey('UserImg.id', ondelete='CASCADE'),
                                  primary_key=True),
                        db.Column('albumid', db.Integer, db.ForeignKey('UserAlbum.id', ondelete='CASCADE'),
                                  primary_key=True)
                        )


class Img(db.Model):
    # 定义表名
    __tablename__ = 'UserImg'

    # 定义对象
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(64), db.ForeignKey('Users.user', ondelete='CASCADE'))
    name = db.Column(db.String(64))
    content = db.Column(db.LargeBinary(length=65536))  # 二进制图片流
    datetime = db.Column(db.DateTime, index=True, nullable=False, default=dt.now)
    classes = db.Column(db.String(64))
    description = db.Column(db.String(128))  # 标签详细分类
    faceid = db.Column(db.String(64))
    facetag = db.Column(db.String(64))
    deletetime = db.Column(db.DateTime)
    albums = db.relationship('Album', secondary=tb_album_img,
                             backref='userimgs', lazy='dynamic')

    # __repr__()方法显示一个可读字符串，虽然不是完全必要，不过用于调试、测试是很不错的。
    def __repr__(self):
        return '<UserImg {}>'.format(self.name)

    # dict(img)，会先调用keys方法，这里重写，自定义获取返回的字段
    def keys(self):
        return ['id', 'user', 'name', 'content', 'datetime', 'classes', 'description', 'faceid', 'facetag',
                'deletetime']

    # dict(img)获取完字段后，会取出对应字段的值，这里使用__getitem__，这里getattr(self, item)拿到值信息，item为key名
    def __getitem__(self, item):
        return getattr(self, item)


class Code(db.Model):
    __tablename__ = 'EmailCode'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(64), nullable=False)
    sendType = db.Column(db.Integer)  # -1 注册 1 登录 0 忘记密码
    code = db.Column(db.String(4), nullable=False)
    sendTime = db.Column(db.Integer)

    def __repr__(self):
        return '<EmailCode {} {} {}>'.format(self.user, self.code, self.sendTime)


class Album(db.Model):
    __tablename__ = 'UserAlbum'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(64), db.ForeignKey('Users.user', ondelete='CASCADE'))
    name = db.Column(db.String(64))
    imgs = db.relationship(Img, secondary=tb_album_img,
                           backref=db.backref('userAlbums', lazy='dynamic'), lazy='dynamic',
                           )

    def __repr__(self):
        return '<UserAlbum {} {} {}>'.format(self.user, self.id, self.name)


# 重新创建表
def reset():
    db.drop_all()
    db.create_all()
    db.session.commit()

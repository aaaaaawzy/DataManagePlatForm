from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
from connect_database import Oprations_of_Database    #引入我们的数据库操作类

#创建数据库操作类实例
op_mysql = Oprations_of_Database("***","***")
app = Flask(__name__)
CORS(app)
# 路由
@app.route('/')    
def first():        # 视图函数
    return 'hello world!!!!!!!!!!!!!!!!!!!!'

@app.route('/login',methods=['POST','OPTIONS'])    
def login():        # 视图函数 从request中接收到的值是bytes 字节码，需要decode('utf8')用utf-8解码
    response = Response()
    if request.method == 'POST':
        containt = request.data.decode('utf8')
        containt = eval(containt)
        Username = containt['username']
        Password = containt['password']
        op_mysql.Username = Username
        op_mysql.Password = Password
        print(op_mysql.Username)
        print(type(Password))
        isLogin = op_mysql.build_connection()
        if isLogin is True:
            response.data = "登陆成功"
            response.status_code = 200
        else:
            response.data = "登录失败"
            response.status_code = 408
        return response

    else:
        return 'way -> OPTIONS'


if __name__ == '__main__' :
    app.run(host="127.0.0.1",port= 8080,debug=True)
import os
import urllib.parse
import json
import uuid
import pymysql
import socket  # 导入 socket 模块
import threading

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
# 打开数据库连接
db = pymysql.connect(host='10.254.159.48',
                     port=3306,
                     user='root',
                     password='123456',
                     database='bbs',
                     autocommit=True)

print("程序启动，使用 http://127.0.0.1:8888/ 访问")

session = {}

class Request:
    def __init__(self, method, url, cookie, data):
        self.method = method
        self.url = url
        self.cookie = cookie
        self.data = data

    def dictquery(self):
        return urllib.parse.parse_qs(self.url.query)
    
    def dictdata(self):
        try:
            return json.loads(self.data)
        except:
            return urllib.parse.parse_qs(self.data)
    
    def dictcookie(self):
        cookie = {}
        for key,value in urllib.parse.parse_qs(self.cookie.replace(";", "&")).items():
            cookie[key.strip()] = value
        return cookie

def sock_server():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #打开一个网络连接

    #   server.sendto() udp的发送形式
    # server.recvfrom() udp接收数据
    server.bind(('0.0.0.0',8888)) #绑定要监听的端口

    server.listen(5)  # 设置最大的连接数量为5
    while True:
        sock, addr = server.accept()  # 建立客户端连接
        t=threading.Thread(target=tcp_link,args=(sock,addr))
        t.start()

def tcp_link(sock,addr):
    data = sock.recv(8192).decode('utf-8').split('\r\n')#接收TCP数据，数据以字符串的形式返还
    if not data[0]:
        return
    method = data[0].split()[0].upper()
    url = urllib.parse.urlparse(data[0].split()[1])
    cookie = ""
    for i in data:
        if not i == "":
            line = i.split(":")
            if line[0].lower() == "cookie":
                cookie = cookie + line[1]
        else:
            break
    
    if method == "POST":
        postdata = data[-1]
    else:
        postdata = ""
    print(addr, method, url.path)
    request = Request(method, url, cookie, postdata)
    db.ping(reconnect=True)
    try:
        header, body = processor(request, db.cursor())
    except Exception as e:
        header, body = (["HTTP/1.0 500 Internal Server Error", "Content-Type: text/html; charset=utf-8"], repr(e))
    for head in header:
        sock.send((head + '\r\n').encode('utf-8'))
    sock.send('\r\n'.encode('utf-8'))
    sock.send(body.encode('utf-8')) #发送TCP数据
    sock.close()  # 关闭连接
    
def processor(request, cursor):
    userinfo = {}
    nologin = (["HTTP/1.0 401 Auth Require", "Content-Type: text/html; charset=utf-8"], "Auth Require")
    cookies = request.dictcookie()
    if "session" in cookies:
        if cookies["session"][0] in session:
            userinfo = session[cookies["session"][0]]
    if request.url.path == "/":
        if userinfo:
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>location.href="/forum.html"</script>')
        else:
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>location.href="/login.html"</script>')
        
    elif request.url.path == "/page/login":
        postdata = request.dictdata()
        if ("username" not in postdata) or ("password" not in postdata):
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>alert("登录失败！请输入用户名和密码。");history.back();</script>')
        cursor.execute("SELECT id FROM users WHERE username = %s AND `password` = password(%s)",(postdata["username"][0], postdata["password"][0],))
        logindata = cursor.fetchone()
        if logindata:
            session_id = str(uuid.uuid4())
            session[session_id] = {"uid": logindata[0], "username": postdata["username"][0]}
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8", "Set-Cookie: session=" + session_id + ";path=/"], '<script>alert("登录成功！");localStorage.setItem("username", "' + postdata["username"][0] + '");location.href="/";</script>')
        else:
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>alert("登录失败！用户名或密码错误。");history.back();</script>')
            
    elif request.url.path == "/page/reg":
        postdata = request.dictdata()
        try:
            cursor.execute("INSERT INTO users(username, `password`) VALUES (%s, password(%s))",(postdata["username"][0], postdata["password"][0],))
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>alert("注册成功！");location.href="/login.html";</script>')
        except:
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>alert("注册失败！");history.back();</script>')
        
    elif request.url.path == "/api/forum":
        if not userinfo:
            return nologin
        cursor.execute("SELECT * FROM forum")
        forumdata = cursor.fetchall()
        return (["HTTP/1.0 200 OK", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 0, 'data': forumdata}))
        
    elif request.url.path == "/api/postlist":
        if not userinfo:
            return nologin
        query = request.dictquery()
        if "id" not in query:
            return (["HTTP/1.0 404 Not Found", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 1, 'data': 'Not Found'}))
        if not query["id"][0]:
            return (["HTTP/1.0 404 Not Found", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 1, 'data': 'Not Found'}))
        cursor.execute("SELECT post.id as pid, post.title, users.username, (SELECT COUNT(id) FROM post WHERE parent_post_id = pid) AS counum, CAST(post.time AS CHAR) FROM post INNER JOIN users ON post.author_id = users.id WHERE post.forum_id = %s AND post.parent_post_id = 0",(query["id"][0],))
        postsdata = cursor.fetchall()
        return (["HTTP/1.0 200 OK", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 0, 'data': postsdata}))
    
    elif request.url.path == "/page/newpost":
        if not userinfo:
            return nologin
        forum_id = request.dictquery()["id"][0]
        post_title = request.dictdata()["title"][0]
        post_content = request.dictdata()["content"][0]
        author_id = userinfo["uid"]
        try:
            cursor.execute("INSERT INTO post(`title`, `content`, `author_id`, `forum_id`, `time`) VALUES (%s, %s, %s, %s, now())",(post_title, post_content, author_id, forum_id,))
            info = "发帖成功！"
        except:
            info = "发帖失败！"
        return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], '<script>alert("' + info + '");location.href = "/postlist.html?id=' + forum_id + '";</script>')
        
    elif request.url.path == "/api/showpost":
        if not userinfo:
            return nologin
        query = request.dictquery()
        if "id" not in query:
            return (["HTTP/1.0 404 Not Found", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 1, 'data': 'Not Found'}))
        if not query["id"][0]:
            return (["HTTP/1.0 404 Not Found", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 1, 'data': 'Not Found'}))
        cursor.execute("SELECT post.title, users.username, post.content, CAST(post.time AS CHAR) FROM post INNER JOIN users ON post.author_id = users.id WHERE post.id = %s",(query["id"][0],))
        mainpost = cursor.fetchone()
        cursor.execute("SELECT users.username, post.content, CAST(post.time AS CHAR) FROM post INNER JOIN users ON post.author_id = users.id WHERE post.parent_post_id = %s",(query["id"][0],))
        postreply = cursor.fetchall()
        return (["HTTP/1.0 200 OK", "Content-Type: application/json; charset=utf-8"], json.dumps({'code': 0, 'data': {'mainpost': mainpost, 'postreply': postreply}}))

    elif request.url.path == "/api/replypost":
        if not userinfo:
            return nologin
        post_id = request.dictquery()["id"][0]
        post_content = request.data
        author_id = userinfo["uid"]
        try:
            cursor.execute("INSERT INTO post(`content`, `author_id`, `parent_post_id`, `forum_id`, `time`) VALUES (%s, %s, %s, (SELECT temp.forum_id from (SELECT `forum_id` FROM post WHERE `id` = %s) temp), now())",(post_content, author_id, post_id, post_id,))
            return (["HTTP/1.0 200 OK", "Content-Type: text/html; charset=utf-8"], 'OK')
        except Exception as e:
            return (["HTTP/1.0 500 Fail", "Content-Type: text/html; charset=utf-8"], repr(e))
        
        
    else:
        fileaddr = PROJECT_PATH + request.url.path
        if os.path.isfile(fileaddr):
            statictype = {"js": "application/javascript", "css": "text/css", "html": "text/html", "txt": "text/plain"}
            questtype = request.url.path.rsplit(".", 1)[-1]
            if questtype in statictype:
                contenttype = statictype[questtype]
            else:
                return (["HTTP/1.0 500 Not Support", "Content-Type: text/html; charset=utf-8"], "The file content is Not Support")
            staticfile = open(fileaddr)
            staticcontent = staticfile.read()
            staticfile.close()
            return (["HTTP/1.0 200 OK", "Content-Type: " + contenttype + "; charset=utf-8", "Cache-Control: max-age=300"], staticcontent)
        else:
            return (["HTTP/1.0 404 Not Found", "Content-Type: text/html; charset=utf-8"], "404")
    cursor.close()

sock_server()

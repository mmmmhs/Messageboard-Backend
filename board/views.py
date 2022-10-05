from unicodedata import name
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
from .models import User, Message
from django.core.exceptions import ValidationError
from pathlib import Path
from django.core.files import File

# Create your views here.
def message(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)

    if request.method == 'GET':
        limit = request.GET.get('limit', default='100')
        offset = request.GET.get('offset', default='0')
        if not limit.isdigit():
            return gen_response(400, '{} is not a number'.format(limit))
        if not offset.isdigit():
            return gen_response(400, '{} is not a number'.format(offset))

        return gen_response(200, [
                {
                    'title': msg.title,
                    'content': msg.content,
                    'user': msg.user.name,
                    'timestamp': int(msg.pub_date.timestamp())
                }
                for msg in Message.objects.all().order_by('-pub_date')[int(offset) : int(offset) + int(limit)]
            ])

    elif request.method == 'POST':
        # 从cookie中获得user的名字，如果user不存在则新建一个
        # 如果cookie中没有user则使用"Unknown"作为默认用户名
        name = request.COOKIES['user'] if 'user' in request.COOKIES else 'Unknown'
        user = User.objects.filter(name=name).first()
        if not user: # 找不到对应name的user
            user = User(name = name)
            try:
                user.full_clean()
                user.save()
            except ValidationError as e:
                return gen_response(400, "Validation Error of user: {}".format(e))


        # 验证请求的数据格式是否符合json规范，如果不符合则返回code 400
        # -------------------------------------------------------------------------------
        req_content = request.body
        try:
            reqjson = json.loads(req_content)
        except Exception as e:
            return gen_response(400, "Request is not appropriate")

        # 验证请求数据是否满足接口要求，若通过所有的验证，则将新的消息添加到数据库中
        # PS: {"title": "something", "content": "someting"} title和content均有最大长度限制
        # -------------------------------------------------------------------------------
        if "title" in reqjson:
            title = reqjson["title"]
            if not title:
                return gen_response(400, "Title is not available")
            if len(title) > 100:
                return gen_response(400, "Title is too long")
        else:
            return gen_response(400, "Title is not available")
        if "content" in reqjson:
            content = reqjson["content"]
            if not content:
                return gen_response(400, "Content is not available")
            if len(content) > 100:
                return gen_response(400, "Content is too long")                
        else:
            return gen_response(400, "Content is not available")
        Message.objects.create(user=user, title=title, content=content)
        # 添加成功返回code 201
        return gen_response(201, "message was sent successfully")

    else:
        return gen_response(405, 'method {} not allowed'.format(request.method))


# 一键清空留言板接口 TODO
def clearmessage(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
    if request.method == 'GET':
        Message.objects.all().delete()
        return gen_response(200, "Message cleared")

# 返回某个用户的所有留言 TODO
def messages_for_user(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
    try:
        reqjson = json.loads(request.body)
    except Exception as e:
        return gen_response(400, "Request is not appropriate")
    if 'user' in reqjson:
        user = reqjson['user']
    else:
        return gen_response(400, "Request is not appropriate")
    if not user:   
        return gen_response(400, "Request is not appropriate")
    requser = User.objects.filter(name=user).first()
    if not requser:
        return gen_response(400, "User does not exist")
    return gen_response(200, [
            {
                'title': msg.title,
                'content': msg.content,
                'timestamp': int(msg.pub_date.timestamp())
            }
            for msg in Message.objects.filter(user=requser).order_by('-pub_date')
        ])            

# AVATAR 用户头像 TODO
def avatar(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
    if request.method == 'GET':
        if 'user' in request.GET:
            # 找到头像
            user = request.GET['user']
            if not user:   
                return gen_response(400, "Request is not appropriate") 
            requser = User.objects.filter(name=user).first() 
            if not requser:
                return gen_response(400, "User does not exist")
            pic = requser.avatar
            if not pic:
                return gen_response(400, "Avatar does not exist")
            path = Path(pic.path)
            if path.is_file():
                with open(path, 'rb') as f:
                    file = f.read()
                return HttpResponse(file, content_type='image/png')         
            # return HttpResponse(???, content_type='image/png')
            else:
                return gen_response(400, "File is not available")
        else:
            return gen_response(400, "Request is not appropriate")

    elif request.method == 'POST':
        #   提示：
        #   user = request.POST['user'] 
        #   pic = request.FILES['pic']
        if 'user' in request.POST and 'pic' in request.FILES:
            user = request.POST['user'] 
            pic = request.FILES['pic']
            if not user or not pic:
                return gen_response(400, "Request is not appropriate")
            requser = User.objects.filter(name=user).first()
            if not requser:
                return gen_response(400, "User does not exist")
            requser.avatar = pic
            requser.save()
            return gen_response(200, "Avatar uploaded")                          
        else:
            return gen_response(400, "Request is not appropriate")
    else:
        return HttpResponse('method {} not allowed'.format(request.method), status=405)

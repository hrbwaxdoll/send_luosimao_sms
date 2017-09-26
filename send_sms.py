# -*- coding: utf-8 -*-
import random
from flask import Flask, request, jsonify
import redis
import requests
import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

APIKEY = "key-"
APIURI = "http://sms-api.luosimao.com/v1/send.json"
REDISSERVER = redis.Redis(host='0.0.0.0', port=6379)


app = Flask(__name__)


# 设置 Redis 缓存，2分钟失效
def code_redis_set(r_name, r_content):
    REDISSERVER.setex(r_name, r_content, '120')


# 删除 Redis 缓存
def code_redis_unset(r_name):
    REDISSERVER.delete(r_name)


# 获取 Redis 缓存状态
def code_redis_get(r_name):
    if REDISSERVER.get(r_name):
        return True
    return False


# 创建验证码并存入 Redis
def create_code(mobile=''):
    tem = ""
    for i in range(6):
        num = random.randrange(1, 9)
        num = str(num)  
        tem += num
    r_name = "%s:%s" % (mobile, tem)
    code_redis_set(r_name, tem)
    # print("%s - %s" % (r_name,code_redis_get(r_name)))
    return tem


# 真正获取验证码的接口
@app.route('/getsms', methods=['POST'])
def getsmscode():
    if 'mobile' in request.json.keys() and 'signname' in request.json.keys():
        mobile_num = request.json['mobile']
        sign_name = request.json['signname']
        code = create_code(mobile_num)
        r = send_message(mobile_num, code, sign_name)
        return jsonify(r)
    return '{"error": -1, "msg": "Please input mobile number & content"}'


# 校验 Redis
@app.route('/checksms', methods=['POST'])
def verify_code():
    mobile = request.json['mobile']
    code = request.json['code']
    redis_code_name = "%s:%s" % (mobile, code)
    if code_redis_get(redis_code_name):
        code_redis_unset(redis_code_name)
        return '{"error": 0, "msg": "ok"}'
    return '{"error": -1, "msg": "The verification code does not exist"}'


# 发送短信 API
def send_message(mobile, smscode, signname):
    content = "验证码 %s 在2分钟后失效，请确认为本人操作，如非本人操作请忽略本条信息，谢谢。【%s】" % (smscode,signname)
    resp = requests.post(
        APIURI,
        auth=("api", APIKEY),
        data={
            "mobile": mobile,
            "message": content
        },
        timeout=3,
        verify=False
    )
    result = resp.json()
    return result


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)

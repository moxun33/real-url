# 获取斗鱼直播间的真实流媒体地址，默认最高画质
# 使用 https://github.com/wbt5/real-url/issues/185 中两位大佬@wjxgzz @4bbu6j5885o3gpv6ss8找到的的CDN，在此感谢！
import hashlib
import re
import time
import sys
import execjs
import requests
from urllib.parse import urlparse


class DouYu:
    """
    可用来替换返回链接中的主机部分
    两个阿里的CDN：
    dyscdnali1.douyucdn.cn
    dyscdnali3.douyucdn.cn
    墙外不用带尾巴的akm cdn：
    hls3-akm.douyucdn.cn
    hlsa-akm.douyucdn.cn
    hls1a-akm.douyucdn.cn
    """

    def __init__(self, rid):
        """
        房间号通常为1~8位纯数字，浏览器地址栏中看到的房间号不一定是真实rid.
        Args:
            rid:
        """
        self.did = '10000000000000000000000000001501'
        self.t10 = str(int(time.time()))
        self.t13 = str(int((time.time() * 1000)))

        self.s = requests.Session()
        self.res = self.s.get('https://m.douyu.com/' + str(rid)).text
        result = re.search(r'rid":(\d{1,8}),"vipId', self.res)

        if result:
            self.rid = result.group(1)
        else:
            raise Exception('房间号错误')

    @staticmethod
    def md5(data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def get_pre(self):
        url = 'https://playweb.douyucdn.cn/lapi/live/hlsH5Preview/' + self.rid
        data = {
            'rid': self.rid,
            'did': self.did
        }

        auth = DouYu.md5(self.rid + self.t13)
        headers = {
            'rid': self.rid,
            'time': self.t13,
            'auth': auth
        }
        res = self.s.post(url, headers=headers, data=data).json()
        error = res['error']
        data = res['data']
        key = ''
        if data:
            rtmp_live = data['rtmp_live']
            key = re.search(r'(\d{1,8}[0-9a-zA-Z]+)_?\d{0,4}(/playlist|.m3u8)', rtmp_live).group(1)
        return error, key

    def get_js(self):
        result = re.search(r'(function ub98484234.*)\s(var.*)', self.res).group()
        func_ub9 = re.sub(r'eval.*;}', 'strc;}', result)
        js = execjs.compile(func_ub9)
        res = js.call('ub98484234')

        v = re.search(r'v=(\d+)', res).group(1)
        rb = DouYu.md5(self.rid + self.did + self.t10 + v)

        func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
        func_sign = func_sign.replace('(function (', 'function sign(')
        func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

        js = execjs.compile(func_sign)
        params = js.call('sign', self.rid, self.did, self.t10)
        params += '&ver=219032101&rid={}&rate=-1'.format(self.rid)

        url = 'https://m.douyu.com/api/room/ratestream'
        res = self.s.post(url, params=params).json()

        return res

    def get_pc_js(self, cdn='ws-h5', rate=0):
        """
        通过PC网页端的接口获取完整直播源。
        :param cdn: 主线路ws-h5、备用线路tct-h5
        :param rate: 1流畅；2高清；3超清；4蓝光4M；0蓝光8M或10M
        :return: JSON格式
        """
        res = self.s.get('https://www.douyu.com/' + str(self.rid)).text
        result = re.search(r'(vdwdae325w_64we[\s\S]*function ub98484234[\s\S]*?)function', res).group(1)
        func_ub9 = re.sub(r'eval.*?;}', 'strc;}', result)
        js = execjs.compile(func_ub9)
        res = js.call('ub98484234')

        v = re.search(r'v=(\d+)', res).group(1)
        rb = DouYu.md5(self.rid + self.did + self.t10 + v)

        func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
        func_sign = func_sign.replace('(function (', 'function sign(')
        func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

        js = execjs.compile(func_sign)
        params = js.call('sign', self.rid, self.did, self.t10)

        params += '&cdn={}&rate={}'.format(cdn, rate)
        url = 'https://www.douyu.com/lapi/live/getH5Play/{}'.format(self.rid)
        res = self.s.post(url, params=params).json()

        return res

    def get_real_url(self):
        error, key = self.get_pre()
        url = ''
        url_obj = {}
        if error == 0:
            rateRes = self.get_js()
            if rateRes['code']==0:
               url = rateRes['data']['url']
               key = re.search(r'(\d{1,8}[0-9a-zA-Z]+)_?\d{0,4}(.m3u8|/playlist)', url).group(1)
               url_obj = urlparse(url)

        elif error == 102:
            raise Exception('房间不存在')
        elif error == 104:
            raise Exception('房间未开播')
        #else:
            #key = self.get_js()
        domain='openflv-huos.douyucdn2.cn'
        # 若key后缀存在_900等码率参数，可自行去掉
        real_url = {}
        real_url["m3u8"] = "http://{}/live/{}.m3u8?uuid=".format(domain,key)
        real_url["flv"] = "http://{}/live/{}.flv?uuid=".format(domain,key)
        real_url["x-p2p"] = "http://{}/live/{}.xs?uuid=".format(domain,key)
        room_name=''#s.get_room_info()
        real_url["name"]=room_name
        return real_url





if __name__ == '__main__':
    try:
        try:
            r=sys.argv[1]
        except:
            r = input('输入斗鱼直播间号：\n')

        s = DouYu(r)
        res=s.get_real_url()
        print(res)
    except Exception as e:
        print(str(e))






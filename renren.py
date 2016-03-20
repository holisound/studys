#!/usr/bin/env python
#coding=utf-8
from requests import Session, Request
import re
import json

class RenRenClient:
    headers = {
        'Host':'www.renren.com',
        'Origin':'http://www.renren.com',
        'Referer':'http://www.renren.com/',
        'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/48.0.2564.82 Chrome/48.0.2564.82 Safari/537.36'
    }

    def __init__(self):
        self.session = Session()
        self.params = dict(
            requestToken = None,
            _rtk = None
        )
        self._html = None

    def _extract_params(self):
        # requestToken : '-1006092579',
        # _rtk : '8fc93d37'
        pat_requestToken = re.compile(r"requestToken[ ]*:[ ]*'([-]?[0-9]+)'")
        pat_rtk = re.compile(r"_rtk[ ]*:[ ]*'([\w]+)'")
        find_result1 = pat_requestToken.findall(self._html)
        find_result2 = pat_rtk.findall(self._html)
        self.params.update(dict(
            requestToken= find_result1 and find_result1[0] or None,
            _rtk= find_result2 and find_result2[0] or None
        ))

    def login(self, username, password):
        url = 'http://www.renren.com/PLogin.do'

        data = {
            'email':username,
            'password':password,
            'icode':'',
            'origURL':'ttp://www.renren.com/home',
            'domain':'renren.com',
            'key_id':1,
            'captcha_type':'web_login',
        }
        req = Request('POST', url,
            data=data,
            headers=self.headers
        )
        prepped = req.prepare()

        # do something with prepped.body
        # do something with prepped.headers
        resp = self.session.send(prepped,
            # stream=stream,
            # verify=verify,
            # proxies=proxies,
            # cert=cert,
            # timeout=timeout
        )
        self._html =  resp.text
        self._extract_params()
        # login success:
        # ver=7.0; domain=.renren.com; path=/, loginfrom=null; domain=.renren.com; path=/, JSESSIONID=abcnxywIfD6yF6Gelpsov; path=/
        print 'login succeeded!' if u'王那' in resp.text  else 'login failed'

    def comment(self, content):
        # http://comment.renren.com/comment/xoa2/create
        # content:aaa
        # replyTo:0
        # whisper:0
        # replaceUBBLarge:true
        # type:photo
        # entryId:7164718849
        # entryOwnerId:262933209
        # requestToken:-1088845467
        # _rtk:8ada87bf
        url = 'http://comment.renren.com/comment/xoa2/create'
        data = dict(
            content=content,
            replyTo= 0,
            whisper=0,
            replaceUBBLarge=True,
            type="photo",
            entryId=7164718849,
            entryOwnerId=262933209,
            requestToken=self.params['requestToken'],
            _rtk=self.params['_rtk'],
        )
        # req = Request('POST', url,
        #     data=data,
        #     cookies=self.session.cookies
        #     # headers=self.headers
        # )
        # prepped = req.prepare()
        #
        # # do something with prepped.body
        # # do something with prepped.headers
        # resp = self.session.send(prepped,
        #     # stream=stream,
        #     # verify=verify,
        #     # proxies=proxies,
        #     # cert=cert,
        #     # timeout=timeout
        # )
        resp = self.session.post(url, data=data)
        # print '='*40 + "\n\n\n%s\n\n\n" % resp.status_code + '=' *40
        if resp.status_code == 200:
            json_resp = json.loads(resp.text)
            if json_resp['code'] == '0':
                return True
def test():
    rclient = RenRenClient()
    rclient.login(
        # '896476116@qq.com',
        'edwardw163@163.com',
        'huo112358'
    )
    if rclient.comment('Such a bitch'):
        print 'comment success!'


if __name__ == '__main__':
    test()
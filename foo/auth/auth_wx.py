#!/usr/bin/env python
# _*_ coding: utf-8_*_
#
# Copyright 2016 7x24hs.com
# thomas@7x24hs.com
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import tornado.web
import logging
import time
import sys
import os
import uuid
import smtplib
import hashlib
import json as JSON # 启用别名，不会跟方法里的局部变量混淆
from bson import json_util
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))

from tornado.escape import json_encode, json_decode
from tornado.httpclient import *
from tornado.httputil import url_concat

from comm import *
from global_const import *
from foo.dao import vendor_wx_dao
from foo.wx import wx_wrap
from foo.wx import xml_parser


# /bf/wxpub/auth/login
class AuthWxLoginHandler(BaseHandler):
    def get(self):
        logging.info("GET %r", self.request)

        club_id = self.get_secure_cookie("club_id")
        logging.info("got club_id=[%r] from cookie", club_id)
        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        logging.info("got wx_app_info=[%r]", wx_app_info)
        wx_app_id = wx_app_info['wx_app_id']
        wx_notify_domain = wx_app_info['wx_notify_domain']

        redirect_url= "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" +\
            wx_app_id + "&redirect_uri=" +\
            wx_notify_domain +"/bf/wxpub/auth/login/step2&response_type=code&scope=snsapi_userinfo&state=1#wechat_redirect"
        self.redirect(redirect_url)


# /bf/wxpub/auth/login/step2
class AuthWxLoginStep2Handler(BaseHandler):
    def get(self):
        logging.info("GET %r", self.request)

        user_agent = self.request.headers["User-Agent"]
        lang = self.request.headers["Accept-Language"]
        wx_code = self.get_argument("code", "")

        if not wx_code:
            club_id = self.get_secure_cookie("club_id")
            logging.info("got club_id=[%r] from cookie", club_id)
            wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
            logging.info("got wx_app_info=[%r]", wx_app_info)
            wx_app_id = wx_app_info['wx_app_id']
            wx_notify_domain = wx_app_info['wx_notify_domain']

            redirect_url= "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" +\
                wx_app_id + "&redirect_uri=" +\
                wx_notify_domain +"/bf/wxpub/auth/login/step2&response_type=code&scope=snsapi_userinfo&state=1#wechat_redirect"
            self.redirect(redirect_url)
            return

        accessToken = wx_wrap.getAccessToken(WX_APP_ID, WX_APP_SECRET, wx_code);
        access_token = accessToken["access_token"];
        logging.info("got access_token %r", access_token)
        wx_openid = accessToken["openid"];
        logging.info("got wx_openid %r", wx_openid)

        wx_userInfo = wx_wrap.getUserInfo(access_token, wx_openid)
        nickname = wx_userInfo["nickname"]
        #nickname = unicode(nickname).encode('utf-8')
        logging.info("got nickname=[%r]", nickname)
        avatar = wx_userInfo["headimgurl"]
        logging.info("got avatar=[%r]", avatar)

        session_ticket = self.wx_register(wx_openid, nickname, avatar)
        self.set_secure_cookie("access_token", session_ticket['access_token'])
        self.set_secure_cookie("expires_at", str(session_ticket['expires_at']))
        self.set_secure_cookie("account_id", session_ticket['account_id'])
        self.create_club_user(CLUB_ID, session_ticket['account_id'])

        login_next = self.get_secure_cookie("login_next")
        self.redirect(login_next)

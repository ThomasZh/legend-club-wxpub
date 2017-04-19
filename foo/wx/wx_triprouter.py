#!/usr/bin/env python
# _*_ coding: utf-8_*_
#
# Copyright 2016 planc2c.com
# dev@tripc2c.com
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
import uuid
import time
import re
import json as JSON # 启用别名，不会跟方法里的局部变量混淆
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))

from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPClient
from tornado.httputil import url_concat
from bson import json_util

from comm import *
from dao import budge_num_dao
from dao import category_dao
from dao import activity_dao
from dao import group_qrcode_dao
from dao import cret_template_dao
from dao import bonus_template_dao
from dao import bonus_dao
from dao import apply_dao
from dao import order_dao
from dao import group_qrcode_dao
from dao import vendor_member_dao
from dao import voucher_dao
from dao import insurance_template_dao
from dao import contact_dao
from dao import vendor_hha_dao
from dao import voucher_pay_dao
from dao import vendor_wx_dao
from dao import voucher_order_dao
from dao import trip_router_dao
from dao import triprouter_share_dao
from dao import club_dao
from dao import activity_share_dao

from auth import auth_email
from auth import auth_phone

from wx_wrap import getAccessTokenByClientCredential
from wx_wrap import getJsapiTicket
from wx_wrap import Sign
from wx_wrap import getNonceStr
from wx_wrap import getOrderSign
from wx_wrap import getPaySign
from wx_wrap import getAccessToken
from wx_wrap import getUserInfo
from xml_parser import parseWxOrderReturn, parseWxPayReturn
from global_const import *


# 线路市场首页
class WxTriprouterMarketHandler(tornado.web.RequestHandler):
    def get(self,vendor_id):

        # _array = trip_router_dao.trip_router_dao().query_by_open(vendor_id)
        triprouters_me = trip_router_dao.trip_router_dao().query_by_vendor(vendor_id)
        triprouters_share = triprouter_share_dao.triprouter_share_dao().query_by_vendor(vendor_id)

        # 处理一下自己线路
        for triprouter in triprouters_me:
            club = club_dao.club_dao().query(triprouter['vendor_id'])
            triprouter['club'] = club['club_name']
            triprouter['share'] = False

        _array = triprouters_me + triprouters_share

        self.render('wx/triprouter-index.html',
                vendor_id=vendor_id,
                triprouters=_array)


class WxTriprouterInfoHandler(tornado.web.RequestHandler):
    def get(self, vendor_id, triprouter_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got triprouter_id %r in uri", triprouter_id)

        _triprouter = trip_router_dao.trip_router_dao().query(triprouter_id)

        # 详细介绍 判断是否有article_id
        try:
            _triprouter['article_id']
        except:
            _triprouter['article_id']=''

        if(_triprouter['article_id']!=''):

            url = "http://"+STP+"/blogs/my-articles/" + _triprouter['article_id'] + "/paragraphs"
            http_client = HTTPClient()
            response = http_client.fetch(url, method="GET")
            logging.info("got response %r", response.body)
            _paragraphs = json_decode(response.body)

            _triprouter_desc = ""
            for _paragraph in _paragraphs:
                if _paragraph["type"] == 'raw':
                    _triprouter_desc = _paragraph['content']
                    break
            _triprouter_desc = _triprouter_desc.replace('&', "").replace('mdash;', "").replace('<p>', "").replace("</p>"," ").replace("<section>","").replace("</section>"," ").replace("\n"," ")
            _triprouter['desc'] = _triprouter_desc + '...'

        else:
            _triprouter['desc'] = '...'


        # 相关活动
        categorys = category_dao.category_dao().query_by_vendor(vendor_id)
        activitys = activity_dao.activity_dao().query_by_triprouter(triprouter_id)
        for activity in activitys:
            activity['begin_time'] = timestamp_date(float(activity['begin_time'])) # timestamp -> %m/%d/%Y
            activity['end_time'] = timestamp_date(float(activity['end_time'])) # timestamp -> %m/%d/%Y
            for category in categorys:
                if category['_id'] == activity['category']:
                    activity['category'] = category['title']
                    break

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(vendor_id)
        wx_app_id = wx_app_info['wx_app_id']
        logging.info("got wx_app_id %r in uri", wx_app_id)
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']

        logging.info("------------------------------------uri: "+self.request.uri)
        _access_token = getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = getJsapiTicket(_access_token)
        _sign = Sign(_jsapi_ticket, wx_notify_domain+self.request.uri).sign()
        logging.info("------------------------------------nonceStr: "+_sign['nonceStr'])
        logging.info("------------------------------------jsapi_ticket: "+_sign['jsapi_ticket'])
        logging.info("------------------------------------timestamp: "+str(_sign['timestamp']))
        logging.info("------------------------------------url: "+_sign['url'])
        logging.info("------------------------------------signature: "+_sign['signature'])

        # _logined = False
        # wechat_open_id = self.get_secure_cookie("wechat_open_id")
        # if wechat_open_id:
        #     _logined = True

        _account_id = self.get_secure_cookie("account_id")

        self.render('wx/triprouter-info.html',
                vendor_id=vendor_id,
                triprouter=_triprouter,activitys=activitys,
                wx_app_id=wx_app_secret,
                wx_notify_domain=wx_notify_domain,
                sign=_sign, account_id=_account_id)

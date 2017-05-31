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

from foo.wx import wx_wrap
from xml_parser import parseWxOrderReturn, parseWxPayReturn
from global_const import *


# 俱乐部首页
class WxVendorInfoHandler(BaseHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_detail_info(club_id)
        logging.info("GET club=[%r]", club)

        self.render('comm/about-us.html',
                club=club)


# 俱乐部管理员绑定微信号码
class WxVendorBindingHandler(BaseHandler):
    def get(self, club_id, account_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)
        logging.info("GET club=[%r]", club)

        self.render('ops/binding-wx.html',
                club=club,
                account_id=account_id)


# 俱乐部管理员绑定微信号码
class WxVendorBindingStep1Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, account_id):
        logging.info("GET %r", self.request.uri)

        access_token = self.get_access_token()
        headers = {"Authorization":"Bearer "+access_token}

        club = self.get_club_basic_info(club_id)
        logging.info("GET club=[%r]", club)

        myinfo = self.get_myinfo_login()
        wx_openid = myinfo['login']

        url = API_DOMAIN + "/api/clubs/"+ club_id +"/operators/"+ account_id +"/binding"
        http_client = HTTPClient()
        _json = json_encode({'binding_type':'wx', 'binding_id':wx_openid})
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("got response.body %r", response.body)

        self.render('ops/binding-wx-success.html',
                club=club,
                account_id=account_id)


# 联盟管理员绑定微信号码
class WxLeagueBindingHandler(BaseHandler):
    def get(self, league_id, account_id):
        logging.info("GET %r", self.request.uri)

        # club = self.get_club_basic_info(club_id)
        # logging.info("GET club=[%r]", club)
        # ops = self.get_admin_info()
        # logging.info("GET ops %r", ops)

        self.render('ops/league-building-wx.html',
                league_id=league_id,
                account_id=account_id)


# 联盟管理员绑定微信号码
class WxLeagueBindingStep1Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, league_id, account_id):
        logging.info("GET %r", self.request.uri)

        access_token = self.get_access_token()
        headers = {"Authorization":"Bearer "+access_token}

        myinfo = self.get_myinfo_login()
        wx_openid = myinfo['login']

        url = API_DOMAIN + "/api/clubs/"+ league_id +"/operators/"+ account_id +"/binding"
        http_client = HTTPClient()
        _json = json_encode({'binding_type':'wx', 'binding_id':wx_openid})
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("got response.body %r", response.body)

        self.render('ops/league-building-wx-success.html',
                league_id=league_id,
                account_id=account_id)

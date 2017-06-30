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


# 分类列表
class WxItemsListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)
        private = 0
        activities = self.get_activities(club_id, ACTIVITY_STATUS_RECRUIT, private)
        logging.info("GET activities %r", activities)

        for activity in activities:
            # 格式化显示时间
            activity['begin_time'] = timestamp_friendly_date(activity['begin_time']) # timestamp -> %m月%d 星期%w
            activity['end_time'] = timestamp_friendly_date(activity['end_time']) # timestamp -> %m月%d 星期%w

            # 格式化价格
            activity['amount'] = float(activity['amount']) / 100

        self.render('items/main.html',
                club=club,
                activities=activities)


# 产品详情
class WxItemsDetailHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self,club_id,activity_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")
        club = self.get_club_basic_info(club_id)

        activity = self.get_activity(activity_id)
        logging.info("got activity %r", activity)
        # 格式化价格
        for activity['base_fee'] in activity['base_fee_template']:
            activity['base_fee']['fee'] = float(activity['base_fee']['fee'])/100

        self.render('items/product-details.html',
                club=club,
                club_id=club_id,
                activity_id=activity_id,
                activity=activity)

    # 添加商品到购物车
    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self, club_id, activity_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        access_token = self.get_secure_cookie("access_token")
        
        fee_template_id = self.get_argument('fee_template_id',"")
        logging.info("got fee_template_id %r in uri", fee_template_id)
        product_num = self.get_argument('product_num',"")
        logging.info("got product_num %r in uri", product_num)

        item_type =  [{item_id:activity_id, fee_template_id:fee_template_id, quantity:product_num}]
        headers = {"Authorization":"Bearer "+access_token}

        url = API_DOMAIN + "/api/clubs/"+ club_id +"/cart/items"
        _json = json_encode(item_type)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("update activity response.body=[%r]", response.body)

        self.redirect('/bf/wx/vendors/'+ club_id +'/activitys/'+activity_id)

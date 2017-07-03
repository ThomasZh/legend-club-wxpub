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
        # 查询分类
        _array = category_dao.category_dao().query_by_vendor(club_id)
        logging.info("got categories=[%r]", _array)
        category_num = len(_array)
        logging.info("got category_num", category_num)

        club = self.get_club_basic_info(club_id)
        private = 0
        items = self.get_items(club_id, ACTIVITY_STATUS_RECRUIT, private)
        logging.info("GET items %r", items)

        for item in items:
            # 格式化价格
            item['amount'] = float(item['amount']) / 100

        self.render('items/main.html',
                club=club,
                items=items,
                category_num=category_num)


# 产品详情
class WxItemsDetailHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self,club_id,item_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")
        club = self.get_club_basic_info(club_id)

        item = self.get_item(item_id)
        logging.info("got item %r", item)

        # 格式化价格
        for item['base_fee'] in item['base_fee_template']:
            item['base_fee']['fee'] = float(item['base_fee']['fee'])/100

        # 获取产品说明
        article = self.get_article(item_id)
        if not article:
            article = {'_id':activity_id, 'title':activity['title'], 'subtitle':[], 'img':activity['img'],'paragraphs':''}
            self.create_article(article)
        logging.info("got article %r", article)

        self.render('items/product-details.html',
                club=club,
                club_id=club_id,
                item_id=item_id,
                item=item,
                article=article)

    # 添加商品到购物车
    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self, club_id, item_id):
        logging.info("got club_id %r in uri", club_id)
        access_token = self.get_secure_cookie("access_token")

        fee_template_id = self.get_argument('fee_template_id',"")
        logging.info("got fee_template_id %r in uri", fee_template_id)
        product_num = self.get_argument('product_num',"")
        logging.info("got product_num %r in uri", product_num)

        item_type =  [{"item_id":item_id, "fee_template_id":fee_template_id, "quantity":product_num}]
        headers = {"Authorization":"Bearer "+access_token}

        url = API_DOMAIN + "/api/clubs/"+ club_id +"/cart/items"
        _json = json_encode(item_type)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("update item response.body=[%r]", response.body)

        self.redirect('/bf/wx/vendors/'+ club_id +'/items/'+item_id)


# 结算
class WxItemsCheckoutHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")

        params = {"page":1, "limit":20,}
        url = url_concat(API_DOMAIN + "/api/clubs/"+ club_id +"/cart/items", params)
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        items = rs['data']

        for item in items:
            item['fee'] = float(item['fee'])/100

        self.render('items/checkout.html',api_domain=API_DOMAIN,club_id=club_id,items=items,access_token=access_token)

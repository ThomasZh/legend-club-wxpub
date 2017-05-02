#!/usr/bin/env python
# _*_ coding: utf-8_*_
#
# Copyright 2016 planc2c.com
# thomas@time2box.com
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
import json as JSON # 启用别名，不会跟方法里的局部变量混淆
from bson import json_util
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))

from comm import *
from global_const import *

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


class EshopHomeHandler(tornado.web.RequestHandler):
    def get(self):
        logging.info(self.request)

        self.redirect("/webapp/eshop/clubs/"+CLUB_ID)


class EshopIndexHandler(tornado.web.RequestHandler):
    def get(self, club_id):
        logging.info(self.request)
        logging.info("got club_id %r--------", club_id)
        vendor_id = club_id

        # club
        url = API_DOMAIN + "/api/clubs/" + club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got club response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        self.render('eshop/index.html',
                API_DOMAIN=API_DOMAIN,
                club=club)


class EshopArticleHandler(tornado.web.RequestHandler):
    def get(self, club_id, article_id):
        logging.info(self.request)
        logging.info("got article_id %r in uri", article_id)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        # update read_num
        url = API_DOMAIN + "/api/articles/"+article_id+"/read"
        http_client = HTTPClient()
        _body = {"read_num": 1}
        _json = json_encode(_body)
        response = http_client.fetch(url, method="POST", body=_json)
        logging.info("got update read_num response %r", response.body)

        self.render('eshop/article.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                article_id=article_id)


class EshopProductHandler(BaseHandler):
    def get(self, club_id, product_id):
        logging.info(self.request)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        activity = self.get_activity(product_id)
        # 金额转换成元 默认将第一个基本服务的费用显示为活动价格
        activity['amount'] = float(activity['amount']) / 100

        article_id = product_id
        # update read_num
        url = API_DOMAIN + "/api/articles/"+article_id+"/read"
        http_client = HTTPClient()
        _body = {"read_num": 1}
        _json = json_encode(_body)
        response = http_client.fetch(url, method="POST", body=_json)
        logging.info("got update read_num response %r", response.body)

        self.render('eshop/product.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                article_id=article_id,
                activity=activity)


class EshopArticleAddCommentHandler(tornado.web.RequestHandler):
    def get(self, club_id, article_id):
        logging.info(self.request)
        logging.info("got article_id %r in uri", article_id)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        self.render('eshop/add-comment.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                article_id=article_id)


class EshopProductPlaceOrderHandler(AuthorizationHandler):
    def get(self, club_id, product_id):
        logging.info(self.request)
        logging.info("got product_id %r in uri", product_id)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        activity = self.get_activity(product_id)
        # 金额转换成元 默认将第一个基本服务的费用显示为活动价格
        activity['amount'] = float(activity['amount']) / 100

        self.render('eshop/place-order.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                activity=activity)

    def post(self, club_id, product_id):
        logging.info(self.request)
        logging.info("got product_id %r in uri", product_id)
        vendor_id = club_id
        activity_id = product_id

        #基本服务
        base_fee_id = self.get_argument("base_fees", "")
        logging.info("got base_fee_id %r", base_fee_id)
        date = self.get_argument("date", "")
        logging.info("got date %r from argument", date)
        phone = self.get_argument("phone", "")
        logging.info("got phone %r from argument", phone)
        note = self.get_argument("note", "")
        logging.info("got note %r from argument", note)

        # 活动金额，即已选的基本服务项金额
        amount = 0
        actual_payment = 0
        quantity = 1
        timestamp = time.time()

        activity = self.get_activity(activity_id)
        bonus_template = bonus_template_dao.bonus_template_dao().query(activity_id)
        bonus_points = int(bonus_template['activity_shared'])

        #基本服务
        base_fee_id = self.get_body_argument("base_fees", "")
        logging.info("got base_fee_id %r", base_fee_id)
        base_fees = []
        base_fee_template = activity['base_fee_template']
        for template in base_fee_template:
            if base_fee_id == template['_id']:
                base_fee = {"_id":base_fee_id, "name":template['name'], "fee":template['fee']}
                base_fees.append(base_fee)
                amount = amount + int(template['fee']) * quantity
                actual_payment = actual_payment + int(template['fee']) * quantity
                break;
        logging.info("got actual_payment %r", actual_payment)

        order_id = str(uuid.uuid1()).replace('-', '')
        _status = ORDER_STATUS_BF_INIT
        if actual_payment == 0:
            _status = ORDER_STATUS_WECHAT_PAY_SUCCESS

        # 创建订单索引
        order_index = {
            "_id": order_id,
            "order_type": "buy_activity",
            "club_id": vendor_id,
            "item_type": "activity",
            "item_id": activity_id,
            "item_name": activity['title'],
            "distributor_type": "user",
            "distributor_id": DEFAULT_USER_ID,
            "create_time": timestamp,
            "pay_type": "wxpay",
            "pay_status": _status,
            "quantity": quantity,
            "amount": amount, #已经转换为分，注意转为数值
            "actual_payment": actual_payment, #已经转换为分，注意转为数值
            "base_fees": base_fees,
            "ext_fees": [],
            "insurances": [],
            "vouchers": [],
            "points_used": 0,
            "bonus_points": bonus_points, # 活动奖励积分
            'booking_time': date,
        }
        self.create_order(order_index)

        # budge_num increase
        self.counter_increase(vendor_id, "activity_order")
        self.counter_increase(activity_id, "order")
        # TODO notify this message to vendor's administrator by SMS

        apply_index = {
            'club_id': vendor_id,
            'item_type': "activity",
            'item_id': activity_id,
            'item_name': activity['title'],
            'order_id': order_id,
            'booking_time': date,
            'group_name': base_fees[0]['name'],
            'real_name': activity['title'],
            'gender': 'male',
            'id_code': phone,
            'phone': phone,
            'height': '200',
            'note': note
        }
        logging.info("create apply=[%r]", apply_index)
        apply_id = self.create_apply(apply_index)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        self.render('eshop/place-order-success.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                activity=activity)


class EshopProductPlaceOrderSuccessHandler(tornado.web.RequestHandler):
    def get(self, club_id, product_id):
        logging.info(self.request)
        logging.info("got product_id %r in uri", product_id)

        # club
        url = API_DOMAIN + "/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        rs = json_decode(response.body)
        club = rs['rs']

        _activity = activity_dao.activity_dao().query(product_id)
        # 金额转换成元 默认将第一个基本服务的费用显示为活动价格
        # _activity['amount'] = float(_activity['amount']) / 100
        if not _activity['base_fee_template']:
            _activity['amount'] = 0
        else:
            for base_fee_template in _activity['base_fee_template']:
                base_fee_template['fee'] = float(base_fee_template['fee']) / 100
                _activity['amount'] = float(base_fee_template['fee']) / 100
        logging.info("got _activity response %r", _activity)

        self.render('eshop/place-order-success.html',
                API_DOMAIN=API_DOMAIN,
                club=club,
                activity=_activity)

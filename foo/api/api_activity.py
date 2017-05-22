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
import json as JSON # 启用别名，不会跟方法里的局部变量混淆
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))

from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPClient
from tornado.httputil import url_concat
from bson import json_util

from global_const import *
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


# 受欢迎活动列表
class ApiActivityPopularListXHR(tornado.web.RequestHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        headers = {"Authorization":"Bearer "+DEFAULT_USER_ID}

        _status = ACTIVITY_STATUS_RECRUIT
        popular = 1
        params = {"filter":"club", "club_id":club_id, "_status":_status, "popular":popular, "page":1, "limit":20}
        url = url_concat(API_DOMAIN + "/api/activities", params)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got get_activities response.body=[%r]", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        activities = rs['data']

        # _array = activity_dao.activity_dao().query_by_popular(vendor_id)
        for activity in activities:
            activity['begin_time'] = timestamp_friendly_date(float(activity['begin_time'])) # timestamp -> %m月%d 星期%w
            activity['end_time'] = timestamp_friendly_date(float(activity['end_time'])) # timestamp -> %m月%d 星期%w

        docs_list = list(activities)
        self.write(JSON.dumps(docs_list, default=json_util.default))
        self.finish()


# 完成活动列表
class ApiActivityCompletedListXHR(tornado.web.RequestHandler):
    def get(self, vendor_id):
        logging.info("GET %r", self.request.uri)

        before = float(self.get_argument("before", ""))
        # limit = int(self.get_argument("limit", ""))
        _array = activity_dao.activity_dao().query_pagination_by_status(
                vendor_id, ACTIVITY_STATUS_COMPLETED, before, PAGE_SIZE_LIMIT)
        categorys = category_dao.category_dao().query_by_vendor(vendor_id)

        for _activity in _array:
            _activity['begin_time'] = timestamp_date(float(_activity['begin_time'])) # timestamp -> %m月%d 星期%w
            _activity['end_time'] = timestamp_date(float(_activity['end_time'])) # timestamp -> %m月%d 星期%w
            for category in categorys:
                if category['_id'] == _activity['category']:
                    _activity['category'] = category['title']
                    break
        docs_list = list(_array)
        self.write(JSON.dumps(docs_list, default=json_util.default))
        self.finish()


# 获取参加某活动的成员
class ApiActivityMemberListXHR(tornado.web.RequestHandler):
    def get(self, vendor_id, activity_id):
        logging.info("GET %r", self.request.uri)

        headers = {"Authorization":"Bearer "+DEFAULT_USER_ID}

        _status = ACTIVITY_STATUS_RECRUIT
        popular = 1
        params = {"filter":"item", "item_id":activity_id, "page":1, "limit":20}
        url = url_concat(API_DOMAIN + "/api/applies", params)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got get_activities response.body=[%r]", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        applies = rs['data']

        # _array = apply_dao.apply_dao().query_by_activity(activity_id)
        # for data in _array:
        #     _member = vendor_member_dao.vendor_member_dao().query_not_safe(vendor_id, data['account_id'])
        #     try:
        #         logging.info("got account_avatar %r", _member['account_avatar'])
        #         data['account_avatar'] = _member['account_avatar']
        #     except:
        #         logging.warn("got account_avatar is null")

        docs_list = list(applies)
        logging.info("got json %r", JSON.dumps(docs_list, default=json_util.default))
        self.write(JSON.dumps(docs_list, default=json_util.default))
        self.finish()


# 获取参加某活动的费用信息
class ApiActivityInfoXHR(BaseHandler):
    def get(self, vendor_id, activity_id):
        logging.info("GET %r", self.request.uri)

        activity = self.get_activity(activity_id)
        # activity = activity_dao.activity_dao().query(activity_id)

        # 金额转换成元
        # activity['amount'] = float(activity['amount']) / 100
        for base_fee_template in activity['base_fee_template']:
            base_fee_template['fee'] = float(base_fee_template['fee']) / 100
        for ext_fee_template in activity['ext_fee_template']:
            ext_fee_template['fee'] = float(ext_fee_template['fee']) / 100

        self.write(JSON.dumps(activity, default=json_util.default))
        self.finish()


# 分享活动获得积分
class ApiActivityShareXHR(BaseHandler):
    def get(self, vendor_id, activity_id):
        logging.info("GET %r", self.request.uri)

        _account_id = self.get_argument("account_id", "")
        logging.info("got _account_id %r", _account_id)

        # 一个活动分享，只能获取一次积分奖励
        points_logs = self.get_points_log(_account_id, activity_id, "share_activity")
        if len(points_logs) == 0:
            activity = self.get_activity(activity_id)
            # _activity = activity_dao.activity_dao().query(activity_id)
            _bonus_template = bonus_template_dao.bonus_template_dao().query(activity_id)
            points = int(_bonus_template['activity_shared'])
            # 修改个人积分信息
            bonus_points = {
                'org_id':vendor_id,
                'org_type':'club',
                'account_id':_account_id,
                'account_type':'user',
                'action': 'share_activity',
                'item_type': 'activity',
                'item_id': activity_id,
                'item_name': activity['title'],
                'bonus_type':'bonus',
                'points': points,
                'order_id': DEFAULT_USER_ID
            }
            self.create_points(bonus_points)

        _json = {'rs':'success'}
        logging.info("got result code>>>>>>>>>>>>>>>>>>> %r", _json)
        self.write(_json)
        self.finish()

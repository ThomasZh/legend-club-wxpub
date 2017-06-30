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


# 受欢迎商品列表
class ApiItemsPopularListXHR(tornado.web.RequestHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        headers = {"Authorization":"Bearer "+DEFAULT_USER_ID}

        _status = ACTIVITY_STATUS_RECRUIT
        popular = 1
        params = {"filter":"club", "club_id":club_id, "_status":_status, "popular":popular, "page":1, "limit":20}
        url = url_concat(API_DOMAIN + "/api/items", params)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got get_items response.body=[%r]", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        items = rs['data']

        docs_list = list(items)
        self.write(JSON.dumps(docs_list, default=json_util.default))
        self.finish()

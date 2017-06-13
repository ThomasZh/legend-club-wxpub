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


#推荐活动列表
class WxResaleActivityIndexHandler(BaseHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)

        headers = {"Authorization":"Bearer "+DEFAULT_USER_ID}
        params = {"page":1, "limit":20}
        url = url_concat(API_DOMAIN + "/api/distributors/" + club['_id'] + "/items", params)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got resale activities response.body=[%r]", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        activities = rs['data']

        _now = time.time()
        # 按报名状况查询每个活动的当前状态：
        # 0: 报名中, 1: 已成行, 2: 已满员, 3: 已结束
        # @2016/06/06
        #
        # 当前时间大于活动结束时间 end_time， 已结束
        # 否则
        # member_max: 最大成行人数, member_min: 最小成行人数
        # 小于member_min, 报名中
        # 大于member_min，小于member_max，已成行
        # 大于等于member_max，已满员
        for activity in activities:
            # _member_min = int(activity['member_min'])
            # _member_max = int(activity['member_max'])
            activity['phase'] = '0'
            if _now > activity['end_time']:
                activity['phase'] = '3'
            # else:
            #     _applicant_num = 0
            #     activity_counter = self.get_counter(activity_id)
            #     if activity_counter:
            #         _applicant_num = int(activity_counter['apply'])
            #
            #     activity['phase'] = '2' if _applicant_num >= _member_max else '1'
            #     activity['phase'] = '0' if _applicant_num < _member_min else '1'

            # 格式化显示时间
            activity['begin_time'] = timestamp_friendly_date(activity['begin_time']) # timestamp -> %m月%d 星期%w
            activity['end_time'] = timestamp_friendly_date(activity['end_time']) # timestamp -> %m月%d 星期%w

            # 格式化价格
            activity['amount'] = float(activity['amount']) / 100

        self.render('resale/activities.html',
                club=club,
                activities=activities)


# 推荐活动详情
class WxResaleActivityInfoHandler(BaseHandler):
    def get(self, vendor_id, activity_id, guest_club_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got activity_id %r in uri", activity_id)
        logging.info("got guest_club_id %r in uri", guest_club_id)

        _activity = self.get_activity(activity_id)
        _applicant_num = 0
        activity_counter = self.get_counter(activity_id)
        if activity_counter and activity_counter.has_key('apply'):
            _applicant_num = int(activity_counter['apply'])

        # 按报名状况查询每个活动的当前状态：
        # 0: 报名中, 1: 已成行, 2: 已满员, 3: 已结束
        # @2016/06/06
        #
        # 当前时间大于活动结束时间 end_time， 已结束
        # 否则
        # member_max: 最大成行人数, member_min: 最小成行人数
        # 小于member_min, 报名中
        # 大于member_min，小于member_max，已成行
        # 大于等于member_max，已满员
        _now = time.time();
        _member_min = int(_activity['member_min'])
        _member_max = int(_activity['member_max'])
        logging.info("got _member_min %r in uri", _member_min)
        logging.info("got _member_max %r in uri", _member_max)

        if _now > _activity['end_time']:
            _activity['phase'] = '3'
        else:
            # _applicant_num = apply_dao.apply_dao().count_by_activity(_activity['_id'])
            logging.info("got _applicant_num %r in uri", _applicant_num)
            _activity['phase'] = '2' if _applicant_num >= _member_max else '1'
            _activity['phase'] = '0' if _applicant_num < _member_min else '1'

        # 格式化时间显示
        _activity['begin_time'] = timestamp_friendly_date(float(_activity['begin_time'])) # timestamp -> %m月%d 星期%w
        _activity['end_time'] = timestamp_friendly_date(float(_activity['end_time'])) # timestamp -> %m月%d 星期%w

        # 格式化价格
        _activity['amount'] = float(_activity['amount']) / 100

        article = self.get_article(activity_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(vendor_id)
        wx_app_id = wx_app_info['wx_app_id']
        logging.info("got wx_app_id %r in uri", wx_app_id)
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']

        logging.info("------------------------------------uri: "+self.request.uri)
        _access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(_access_token)
        _sign = wx_wrap.Sign(_jsapi_ticket, wx_notify_domain+self.request.uri).sign()
        logging.info("------------------------------------nonceStr: "+_sign['nonceStr'])
        logging.info("------------------------------------jsapi_ticket: "+_sign['jsapi_ticket'])
        logging.info("------------------------------------timestamp: "+str(_sign['timestamp']))
        logging.info("------------------------------------url: "+_sign['url'])
        logging.info("------------------------------------signature: "+_sign['signature'])

        _account_id = self.get_secure_cookie("account_id")
        _bonus_template = bonus_template_dao.bonus_template_dao().query(_activity['_id'])

        self.render('resale/activity-info.html',
                guest_club_id = guest_club_id,
                vendor_id=vendor_id,
                activity=_activity,
                article=article,
                wx_app_id=wx_app_id,
                wx_notify_domain=wx_notify_domain,
                sign=_sign, account_id=_account_id,
                bonus_template=_bonus_template)


# 供应商列表
class WxResaleSupplerListHandler(BaseHandler):
    def get(self, league_id):
        logging.info("GET %r", self.request.uri)

        access_token = self.get_secure_cookie("access_token")

        headers = {"Authorization":"Bearer "+DEFAULT_USER_ID}
        params = {"filter":"league","franchise_type":"供应商","page":1, "limit":100}
        url = url_concat(API_DOMAIN + "/api/leagues/" + league_id + "/clubs", params)
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got resale suppliers response.body=[%r]", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        suppliers = rs['data']

        self.render('resale/supplier-list.html',
                api_domain= API_DOMAIN,
                access_token=access_token,
                league_id=league_id,
                suppliers=suppliers)


# 单个供应商
class WxResaleSupplerHandler(BaseHandler):
    def get(self,league_id):
        logging.info("GET %r", self.request.uri)

        access_token = self.get_secure_cookie("access_token")
        id = self.get_argument("s","")

        url = API_DOMAIN+"/api/leagues/"+ league_id +"/franchises/"+id
        http_client = HTTPClient()
        headers={"Authorization":"Bearer "+access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response %r", response.body)
        data = json_decode(response.body)
        franchise = data['rs']
        franchise['create_time'] = timestamp_datetime(franchise['create_time'])
        if not franchise['club'].has_key('img'):
            franchise['club']['img'] = ''

        self.render('resale/supplier.html',
                api_domain = API_DOMAIN,
                access_token=access_token,
                league_id=league_id,
                franchise=franchise)


# 供给分销的单个产品详情
class WxResaleGoodsDetailHandler(AuthorizationHandler):
    def get(self,league_id,club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")
        club = self.get_club_basic_info(club_id)
        activity_id = self.get_argument("item_id","")

        activity = self.get_activity(activity_id)
        logging.info("got activity %r", activity)

        self.render('resale/goods-detail.html',
                club=club,
                league_id=league_id,
                club_id=club_id,
                activity_id=activity_id,
                activity=activity)

    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self, league_id, vendor_id):
        logging.info("got league_id %r in uri", league_id)
        logging.info("got vendor_id %r in uri", vendor_id)

        is_login = False
        access_token = self.get_secure_cookie("access_token")
        if access_token:
            is_login = True
        # 判断是否注册了分销商
        try:
            params = {"filter":"ops"}
            url = url_concat(API_DOMAIN+"/api/myinfo", params)
            http_client = HTTPClient()
            headers={"Authorization":"Bearer "+access_token}
            response = http_client.fetch(url, method="GET", headers=headers)
            logging.info("got response %r", response.body)
            # account_id,nickname,avatar,club_id,club_name,league_id,_rank
            data = json_decode(response.body)
            ops = data['rs']

            activity_id = self.get_argument("item_id","")
            logging.info(" got activity_id %r", activity_id)

            item_type = {"item_type": "activity"}
            headers = {"Authorization":"Bearer "+access_token}

            url = API_DOMAIN + "/api/distributors/"+ club_id + "/items/"+ activity_id + "/takeon"
            _json = json_encode(item_type)
            http_client = HTTPClient()
            response = http_client.fetch(url, method="POST", headers=headers, body=_json)
            logging.info("update activity response.body=[%r]", response.body)

            # 加share属性，区别一个自己是否已经分享了别人开放的这个活动
            # for activity in activitys:
            #     # 取俱乐部名称
            #     club_id = activity['vendor_id']
            #     club = get_club_info(access_token,club_id)
            #     if club:
            #         activity['club'] = club['name']
            #     else:
            #         activity['club'] = ""
            #     activity['share'] = False
            #
            #     activity['begin_time'] = timestamp_date(float(activity['begin_time'])) # timestamp -> %m/%d/%Y
            #
            #     for activity_share in activitys_share:
            #         if(activity['_id']==activity_share['activity']):
            #             activity['share'] = True
            #             break

        except:
            err_title = str( sys.exc_info()[0] );
            err_detail = str( sys.exc_info()[1] );
            logging.error("error: %r info: %r", err_title, err_detail)
            if err_detail == 'HTTP 404: Not Found':
                err_msg = "您还不是分销商，请先注册!"
                self.redirect("/bf/wx/vendors/register-distributor")
            else:
                err_msg = "系统故障, 请稍后尝试!"
                self.redirect("/bf/wx/vendors/register-distributor")



class WxResaleRegisterDistributorHandler(BaseHandler):
    def get(self):
        logging.info("GET %r", self.request.uri)
        err_msg = ""
        self.render('resale/register-distributor.html',err_msg=err_msg)

    def post(self):
        logging.info(self.request)
        logging.info(self.request.body)
        phone = self.get_argument("reg_phone", "")
        pwd = self.get_argument("reg_pwd", "")
        logging.info("try register as phone:[%r] pwd:[%r]", phone, pwd)

        code = self.get_code()

        # register
        try:
            url = API_DOMAIN+"/api/auth/accounts"
            http_client = HTTPClient()
            headers={"Authorization":"Bearer "+code}
            data = {"login_type":"phone",
                    "phone":phone,
                    "pwd":pwd}
            _json = json_encode(data)
            logging.info("request %r body %r", url, _json)
            response = http_client.fetch(url, method="POST", headers=headers, body=_json)
            logging.info("got response %r", response.body)
            data = json_decode(response.body)
            session_ticket = data['rs']
        except:
            err_title = str( sys.exc_info()[0] );
            err_detail = str( sys.exc_info()[1] );
            logging.error("error: %r info: %r", err_title, err_detail)
            if err_detail == 'HTTP 409: Conflict':
                err_msg = "此手机号码已经注册!"
                self.render('resale/register-distributor.html', err_msg=err_msg)
                return

        err_msg = "注册成功，请登录!"
        self.render('resale/register-success.html', err_msg=err_msg)



class WxResaleDistributorPersonalHandler(BaseHandler):
    def get(self, resale_id):
        logging.info("GET %r", self.request.uri)

        self.render('resale/distributor-personal.html')

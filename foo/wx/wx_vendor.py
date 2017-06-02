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

        self.render('ops/ops-binding-wx.html',
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

        self.render('ops/ops-binding-wx-success.html',
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

        self.render('ops/admin-building-wx.html',
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

        url = API_DOMAIN + "/api/leagues/"+ league_id +"/administrators/"+ account_id +"/binding"
        http_client = HTTPClient()
        _json = json_encode({'binding_type':'wx', 'binding_id':wx_openid})
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("got response.body %r", response.body)

        self.render('ops/admin-building-wx-success.html',
                league_id=league_id,
                account_id=account_id)


# 分销商发起提现申请
# /bf/wx/vendors/{club_id}/ops/{apply_account_id}/apply-cash-out/suppliers/{supplier_id}
class WxVendorResellerApplyCashoutHandler(BaseHandler):
    def get(self, club_id, apply_account_id, supplier_id):
        logging.info("GET %r", self.request.uri)

        supplier = self.get_club_basic_info(supplier_id)
        logging.info("GET supplier=[%r]", supplier)

        # 查询我在此供应商的积分余额
        distributor = self.get_distributor(supplier_id, club_id)

        self.render('ops/apply-cashout.html',
                club_id=club_id,
                apply_account_id=apply_account_id,
                distributor=distributor,
                supplier=supplier)


# 分销商发起提现申请
# /bf/wx/vendors/{club_id}/ops/{apply_account_id}/apply-cash-out/suppliers/{supplier_id}/step1
class WxVendorResellerApplyCashoutStep1Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, apply_account_id, supplier_id):
        logging.info("GET %r", self.request.uri)

        access_token = self.get_access_token()
        headers = {"Authorization":"Bearer "+access_token}

        myinfo = self.get_myinfo_login()
        apply_wx_openid = myinfo['login']

        club = self.get_club_basic_info(club_id)
        league_id = club['league_id']

        # 查询我在此供应商的积分余额
        distributor = self.get_distributor(supplier_id, club_id)

        supplier = self.get_club_basic_info(supplier_id)
        logging.info("GET supplier=[%r]", supplier)

        url = API_DOMAIN + "/api/points/leagues/"+ league_id +"/apply-cash-out"
        http_client = HTTPClient()
        _json = json_encode({'apply_account_id':apply_account_id,
                'apply_org_id':club_id,
                'apply_org_type':'distributor',
                'apply_wx_openid':apply_wx_openid,
                'org_id':supplier_id,
                'org_type':'supplier',
                'bonus_type':'bonus',
                'bonus_point':distributor['accumulated_points']})
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("got response.body %r", response.body)
        rs = json_decode(response.body)
        apply_cashout = rs['data']

        # budge_num increase
        self.counter_increase(league_id, "apply_cashout")
        # TODO notify this message to vendor's administrator by SMS

        # notify this message to league's administrators by wx_template
        wx_access_token = wx_wrap.getAccessTokenByClientCredential(WX_APP_ID, WX_APP_SECRET)
        logging.info("got wx_access_token %r", wx_access_token)
        # 通过wxpub，给联盟管理员发送通知
        admins = self.get_league_admin_wx(league_id)
        for admin in admins:
            wx_openid = admin['binding_id']
            logging.info("got wx_openid %r", wx_openid)
            wx_wrap.sendApplyCashoutToAdminMessage(wx_access_token, WX_NOTIFY_DOMAIN, wx_openid, apply_cashout)

        # 通过wxpub，给俱乐部操作员发送通知
        wx_wrap.sendApplyCashoutToOpsMessage(wx_access_token, WX_NOTIFY_DOMAIN, apply_wx_openid, apply_cashout)

        self.render('ops/apply-cashout-success.html',
                supplier=supplier)


# 查看提现申请详情
# /bf/wx/vendors/{club_id}/apply-cashout/{apply_id}
class WxVendorApplyCashoutInfoHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, apply_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)
        logging.info("GET club=[%r]", club)
        league_id = club['league_id']
        apply_cashout = self.get_apply_cashout(league_id, apply_id)
        apply_cashout['bonus_point'] = float(apply_cashout['bonus_point'] / 100)
        apply_cashout['create_time'] = timestamp_datetime(apply_cashout['create_time'])
        if apply_cashout['_status'] == 0:
            apply_cashout['_status'] = u"待审核"
        elif apply_cashout['_status'] == 10:
            apply_cashout['_status'] = u"接受"
        elif apply_cashout['_status'] == 20:
            apply_cashout['_status'] = u"拒绝"
        if apply_cashout['org_type'] = "supplier":
            apply_cashout['org_type'] = u"供应商"
        elif apply_cashout['org_type'] = "league":
            apply_cashout['org_type'] = u"联盟"
        if apply_cashout['apply_org_type'] = "supplier":
            apply_cashout['apply_org_type'] = u"供应商"
        elif apply_cashout['apply_org_type'] = "distributor":
            apply_cashout['apply_org_type'] = u"分销商"

        supplier = self.get_club_basic_info(apply_cashout['org_id'])
        logging.info("GET supplier=[%r]", supplier)

        # 查询我在此供应商的积分余额
        distributor = self.get_distributor(apply_cashout['org_id'], apply_cashout['apply_org_id'])
        distributor['remaining_points'] = float(distributor['remaining_points'] / 100)

        self.render('ops/apply-cashout-detail.html',
                apply_cashout=apply_cashout,
                supplier=supplier,
                distributor=distributor)

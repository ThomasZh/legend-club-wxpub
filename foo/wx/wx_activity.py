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


# 活动首页
class WxActivityListHandler(BaseHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)
        private = 0
        activities = self.get_activities(club_id, ACTIVITY_STATUS_RECRUIT, private)

        _now = time.time()
        # # 查询结果，不包含隐藏的活动

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

        self.render('activity/index.html',
                club=club,
                activities=activities)


# 活动历史列表
class WxActivityHistoryListHandler(BaseHandler):
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)

        club = self.get_club_basic_info(club_id)
        private = 0
        activities = self.get_activities(club_id, ACTIVITY_STATUS_COMPLETED, private)
        logging.info("GET activities %r", activities)

        _now = time.time()
        # # 查询结果，不包含隐藏的活动

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
            activity['phase'] = '3'
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

        self.render('activity/index.html',
                club=club,
                activities=activities)


# 活动详情
class WxActivityInfoHandler(BaseHandler):
    def get(self, vendor_id, activity_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got activity_id %r in uri", activity_id)

        _activity = self.get_activity(activity_id)
        _applicant_num = 0
        activity_counter = self.get_counter(activity_id)
        if activity_counter and activity_counter.has_key('apply'):
            _applicant_num = int(activity_counter['apply'])

        # _activity = activity_dao.activity_dao().query(activity_id)
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

        if not _activity.has_key('_status'):
            _activity['_status'] = ACTIVITY_STATUS_DRAFT

        if _activity['_status'] < ACTIVITY_STATUS_RECRUIT:
            _activity['phase'] = '3'
        elif _activity['_status'] > ACTIVITY_STATUS_RECRUIT:
            _activity['phase'] = '3'
        else:
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

        self.render('activity/activity-info.html',
                guest_club_id = GUEST_CLUB_ID,
                vendor_id=vendor_id,
                activity=_activity,
                article=article,
                wx_app_id=wx_app_id,
                wx_notify_domain=wx_notify_domain,
                sign=_sign, account_id=_account_id,
                bonus_template=_bonus_template)


# 活动二维码
class WxActivityQrcodeHandler(BaseHandler):
    def get(self, vendor_id, activity_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got activity_id %r in uri", activity_id)

        activity = self.get_activity(activity_id)

        # _activity = activity_dao.activity_dao().query(activity_id)
        _qrcode = group_qrcode_dao.group_qrcode_dao().query(activity_id)
        # 为活动添加二维码属性
        activity['wx_qrcode_url'] = _qrcode['wx_qrcode_url']
        logging.debug(_qrcode)

        self.render('activity/activity-qrcode.html',
                vendor_id=vendor_id,
                activity=activity)


class WxActivityApplyStep0Handler(BaseHandler):
    def get(self, vendor_id, activity_id, guest_club_id):
        logging.info("GET %r", self.request.uri)

        activity = self.get_activity(activity_id)
        club_id = activity['club_id']

        # activity = activity_dao.activity_dao().query(activity_id)
        logging.info("got club_id=[%r]", club_id)
        # 不是我的活动 直接跳走（此时guest_club_id肯定不是0）
        if vendor_id != club_id:
            wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
            wx_notify_domain = wx_app_info['wx_notify_domain']

            redirect_url = wx_notify_domain + "/bf/wx/vendors/" +\
                club_id +\
                "/activitys/" + activity_id +\
                "_" + vendor_id + "/apply/step0"
            logging.info("redirect to=[%r]", redirect_url)
            self.redirect(redirect_url)
        else:
            self.set_secure_cookie("club_id", club_id)

            redirect_url = "/bf/wx/vendors/" + club_id +\
                "/activitys/" + activity_id +\
                "_" + guest_club_id + "/apply/step1"
            logging.info("redirect to=[%r]", redirect_url)
            self.redirect(redirect_url)


class WxActivityApplyStep1Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id, activity_id, guest_club_id):
        logging.info("GET %r", self.request.uri)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(vendor_id)
        wx_app_id = wx_app_info['wx_app_id']
        logging.info("got wx_app_id %r in uri", wx_app_id)

        activity = self.get_activity(activity_id)
        logging.info("got activity %r", activity)
        # activity = activity_dao.activity_dao().query(activity_id)
        activity['begin_time'] = timestamp_friendly_date(float(activity['begin_time'])) # timestamp -> %m月%d 星期%w
        activity['end_time'] = timestamp_friendly_date(float(activity['end_time'])) # timestamp -> %m月%d 星期%w

        self.render('activity/activity-apply-step1.html',
                guest_club_id = guest_club_id,
                vendor_id=vendor_id,
                wx_app_id=wx_app_id,
                activity=activity)


class WxActivityApplyStep2Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self):
        vendor_id = self.get_argument("vendor_id", "")
        logging.info("got vendor_id %r", vendor_id)
        activity_id = self.get_argument("activity_id", "")
        logging.info("got activity_id %r", activity_id)
        _account_id = self.get_secure_cookie("account_id")
        guest_club_id = self.get_argument("guest_club_id")
        logging.info("got guest_club_id %r", guest_club_id)

        access_token = self.get_access_token()

        # 取得自己的最后一笔订单
        params = {"filter":"account", "account_id":_account_id, "page":1, "limit":1,}
        url = url_concat(API_DOMAIN + "/api/orders", params)
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        orders = rs['data']

        _timestamp = time.time()
        # 一分钟内不能创建第二个订单,
        # 防止用户点击回退按钮，产生第二个订单
        if len(orders) > 0:
            for order in orders:
                if (_timestamp - order['create_time']) < 60:
                    self.redirect('/bf/wx/orders/wait')
                    return

        # 订单总金额
        _total_amount = self.get_argument("total_amount", 0)
        logging.info("got _total_amount %r", _total_amount)
        # 价格转换成分
        _total_amount = int(float(_total_amount) * 100)
        logging.info("got _total_amount %r", _total_amount)
        # 订单申报数目
        _applicant_num = self.get_argument("applicant_num", 1)
        # 活动金额，即已选的基本服务项金额
        amount = 0
        actual_payment = 0
        quantity = int(_applicant_num)
        logging.info("got quantity %r", quantity)

        _activity = self.get_activity(activity_id)
        # _activity = activity_dao.activity_dao().query(activity_id)
        _bonus_template = bonus_template_dao.bonus_template_dao().query(activity_id)
        bonus_points = int(_bonus_template['activity_shared'])

        #基本服务
        _base_fee_ids = self.get_body_argument("base_fees", [])
        logging.info("got _base_fee_ids %r", _base_fee_ids)
        # 转为列表
        _base_fee_ids = JSON.loads(_base_fee_ids)
        _base_fees = []
        base_fee_template = _activity['base_fee_template']
        for _base_fee_id in _base_fee_ids:
            for template in base_fee_template:
                if _base_fee_id == template['_id']:
                    _base_fee = {"_id":_base_fee_id, "name":template['name'], "fee":template['fee']}
                    _base_fees.append(_base_fee)
                    activity_amount = template['fee']
                    amount = amount + int(template['fee']) * quantity
                    actual_payment = actual_payment + int(template['fee']) * quantity
                    break;
        logging.info("got actual_payment %r", actual_payment)

        # 附加服务项编号数组
        # *** 接受json数组用这个 ***
        _ext_fee_ids = self.get_body_argument("ext_fees", [])
        logging.info("got _ext_fee_ids %r", _ext_fee_ids)
        # 转为列表
        _ext_fee_ids = JSON.loads(_ext_fee_ids)
        _ext_fees = []
        ext_fee_template = _activity['ext_fee_template']
        for _ext_fee_id in _ext_fee_ids:
            for template in ext_fee_template:
                if _ext_fee_id == template['_id']:
                    _ext_fee = {"_id":_ext_fee_id, "name":template['name'], "fee":template['fee']}
                    _ext_fees.append(_ext_fee)
                    amount = amount + int(template['fee']) * quantity
                    actual_payment = actual_payment + int(template['fee']) * quantity
                    break;
        logging.info("got actual_payment %r", actual_payment)

        # 保险选项,数组
        _insurance_ids = self.get_body_argument("insurances", [])
        _insurance_ids = JSON.loads(_insurance_ids)
        _insurances = []
        _insurance_templates = insurance_template_dao.insurance_template_dao().query_by_vendor(vendor_id)
        for _insurance_id in _insurance_ids:
            for _insurance_template in _insurance_templates:
                if _insurance_id == _insurance_template['_id']:
                    _insurance = {"_id":_insurance_id, "name":_insurance_template['title'], "fee":_insurance_template['amount']}
                    _insurances.append(_insurance)
                    amount = amount + int(_insurance['fee']) * quantity
                    actual_payment = actual_payment + int(_insurance['fee']) * quantity
                    break;
        logging.info("got actual_payment %r", actual_payment)

        #代金券选项,数组
        _vouchers_ids = self.get_body_argument("vouchers", [])
        _vouchers_ids = JSON.loads(_vouchers_ids)
        _vouchers = []
        for _vouchers_id in _vouchers_ids:
            logging.info("got _vouchers_id %r", _vouchers_id)
            _voucher = voucher_dao.voucher_dao().query_not_safe(_vouchers_id)
            _json = {'_id':_vouchers_id, 'fee':_voucher['amount']}
            _vouchers.append(_json)
            actual_payment = actual_payment - int(_json['fee']) * quantity
        logging.info("got actual_payment %r", actual_payment)

        # 积分选项,数组
        _bonus = 0
        _bonus_array = self.get_body_argument("bonus", [])
        if _bonus_array:
            _bonus_array = JSON.loads(_bonus_array)
            if len(_bonus_array) > 0:
                _bonus = _bonus_array[0]
                # 价格转换成分
                _bonus = - int(float(_bonus) * 100)
        logging.info("got _bonus %r", _bonus)
        points = _bonus
        actual_payment = actual_payment + points
        logging.info("got actual_payment %r", actual_payment)

        _order_id = str(uuid.uuid1()).replace('-', '')
        _status = ORDER_STATUS_BF_INIT
        if actual_payment == 0:
            _status = ORDER_STATUS_WECHAT_PAY_SUCCESS

        # 创建订单索引
        order_index = {
            "_id": _order_id,
            "order_type": "buy_activity",
            "club_id": vendor_id,
            "item_type": "activity",
            "item_id": activity_id,
            "item_name": _activity['title'],
            "distributor_type": "club",
            "distributor_id": guest_club_id,
            "create_time": _timestamp,
            "pay_type": "wxpay",
            "pay_status": _status,
            "quantity": quantity,
            "amount": amount, #已经转换为分，注意转为数值
            "actual_payment": actual_payment, #已经转换为分，注意转为数值
            "base_fees": _base_fees,
            "ext_fees": _ext_fees,
            "insurances": _insurances,
            "vouchers": _vouchers,
            "points_used": points,
            "bonus_points": bonus_points, # 活动奖励积分
            "booking_time": _activity['begin_time'],
        }
        self.create_order(order_index)

        # budge_num increase
        self.counter_increase(vendor_id, "activity_order")
        self.counter_increase(activity_id, "order")
        # TODO notify this message to vendor's administrator by SMS

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(vendor_id)
        wx_app_id = wx_app_info['wx_app_id']
        logging.info("got wx_app_id %r in uri", wx_app_id)
        wx_mch_key = wx_app_info['wx_mch_key']
        wx_mch_id = wx_app_info['wx_mch_id']
        wx_notify_domain = wx_app_info['wx_notify_domain']

        _timestamp = (int)(time.time())
        if actual_payment != 0:
            # wechat 统一下单
            myinfo = self.get_myinfo_login()
            _openid = myinfo['login']
            _store_id = 'Aplan'
            logging.info("got _store_id %r", _store_id)
            _product_description = _activity['title']
            logging.info("got _product_description %r", _product_description)
            #_ip = self.request.remote_ip
            _remote_ip = self.request.headers['X-Real-Ip']
            _order_return = wx_wrap.getUnifiedOrder(_remote_ip, wx_app_id, _store_id, _product_description, wx_notify_domain, wx_mch_id, wx_mch_key, _openid, _order_id, actual_payment, _timestamp)

            # wx统一下单记录保存
            _order_return['_id'] = _order_return['prepay_id']
            self.create_symbol_object(_order_return)

            # 微信统一下单返回成功
            order_unified = None
            if(_order_return['return_msg'] == 'OK'):
                order_unified = {'_id':_order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_SUCCESS}
            else:
                order_unified = {'_id':_order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_FAILED}
            # 微信统一下单返回成功
            # TODO: 更新订单索引中，订单状态pay_status,prepay_id
            self.update_order_unified(order_unified)

            # FIXME, 将服务模板转为字符串，客户端要用
            _servTmpls = _activity['ext_fee_template']
            _activity['json_serv_tmpls'] = json_encode(_servTmpls);
            _activity['begin_time'] = timestamp_friendly_date(float(_activity['begin_time'])) # timestamp -> %m月%d 星期%w
            _activity['end_time'] = timestamp_friendly_date(float(_activity['end_time'])) # timestamp -> %m月%d 星期%w
            # 金额转换成元
            # _activity['amount'] = float(activity_amount) / 100
            for base_fee in order_index['base_fees']:
                # 价格转换成元
                order_index['activity_amount'] = float(base_fee['fee']) / 100

            self.render('wx/order-confirm.html',
                    vendor_id=vendor_id,
                    return_msg=response.body, order_return=_order_return,
                    activity=_activity, order_index=order_index)
        else: #actual_payment == 0:
            # FIXME, 将服务模板转为字符串，客户端要用
            _servTmpls = _activity['ext_fee_template']
            _activity['json_serv_tmpls'] = tornado.escape.json_encode(_servTmpls);
            _activity['begin_time'] = timestamp_friendly_date(float(_activity['begin_time'])) # timestamp -> %m月%d 星期%w
            _activity['end_time'] = timestamp_friendly_date(float(_activity['end_time'])) # timestamp -> %m月%d 星期%w
            # 金额转换成元
            # _activity['amount'] = float(activity_amount) / 100
            for base_fee in order_index['base_fees']:
                # 价格转换成元
                order_index['activity_amount'] = float(base_fee['fee']) / 100

            # 如使用积分抵扣，则将积分减去
            if order_index['points_used'] < 0:
                # 修改个人积分信息
                bonus_points = {
                    'club_id':vendor_id,
                    'account_id':_account_id,
                    'account_type':'user',
                    'action': 'buy_activity',
                    'item_type': 'activity',
                    'item_id': activity_id,
                    'item_name': _activity['title'],
                    'bonus_type':'bonus',
                    'points': points,
                    'order_id': order_index['_id']
                }
                self.create_points(bonus_points)
                # self.points_decrease(vendor_id, order_index['account_id'], order_index['points_used'])

            # 如使用代金券抵扣，则将代金券减去
            for _voucher in _vouchers:
                # status=2, 已使用
                voucher_dao.voucher_dao().update({'_id':_voucher['_id'], 'status':2, 'last_update_time':_timestamp})
                _customer_profile = vendor_member_dao.vendor_member_dao().query_not_safe(vendor_id, order_index['account_id'])
                # 修改个人代金券信息
                _voucher_amount = int(_customer_profile['vouchers']) - int(_voucher['fee'])
                if _voucher_amount < 0:
                    _voucher_amount = 0
                _json = {'vendor_id':vendor_id, 'account_id':order_index['account_id'], 'last_update_time':_timestamp,
                        'vouchers':_voucher_amount}
                vendor_member_dao.vendor_member_dao().update(_json)

            self.render('wx/order-confirm.html',
                    vendor_id=vendor_id,
                    return_msg='OK',
                    order_return={'timestamp':_timestamp,
                        'nonce_str':'',
                        'pay_sign':'',
                        'prepay_id':'',
                        'app_id': wx_app_id,
                        'return_msg':'OK'},
                    activity=_activity,
                    order_index=order_index)


# 添加当前订单的成员
class WxActivityApplyStep3Handler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id, activity_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got activity_id %r in uri", activity_id)

        _order_id = self.get_argument("order_id", "")
        logging.info("got _order_id %r", _order_id)

        activity = self.get_activity(activity_id)
        # activity = activity_dao.activity_dao().query(activity_id)

        # FIXME, 返回账号给前端，用来ajax查询当前用户的联系人
        # @2016/06/14
        _account_id = self.get_secure_cookie("account_id")

        self.render('activity/activity-apply-step3.html',
                vendor_id=vendor_id,
                activity=activity,
                order_id=_order_id,
                account_id=_account_id)


    def post(self, vendor_id, activity_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got activity_id %r in uri", activity_id)

        _account_id = self.get_secure_cookie("account_id")
        _order_id = self.get_argument("order_id", "")

        # 查询过去是否填报，有则跳过此步骤。主要是防止用户操作回退键，重新回到此页面
        _old_order = self.get_symbol_object(_order_id)
        if _old_order['pay_status'] > 30:
            activity = self.get_activity(activity_id)
            # _activity = activity_dao.activity_dao().query(activity_id)
            _qrcode = group_qrcode_dao.group_qrcode_dao().query(activity_id)
            # 为活动添加二维码属性
            activity['wx_qrcode_url'] = _qrcode['wx_qrcode_url']
            logging.info(_qrcode)
            self.render('activity/activity-apply-step3.html',
                    vendor_id=vendor_id,
                    activity=activity,
                    order_id=_order_id,
                    account_id=_account_id)
            return
        else:
            activity = self.get_activity(activity_id)
            # _activity = activity_dao.activity_dao().query(activity_id)

            _applicantstr = self.get_body_argument("applicants", [])
            _applicantList = JSON.loads(_applicantstr);
            # 处理多个申请人
            for apply_index in _applicantList:
                apply_index["club_id"] = vendor_id
                apply_index["item_type"] = "activity"
                apply_index["item_id"] = activity_id
                apply_index["item_name"] = activity['title']
                apply_index["order_id"] = _order_id
                apply_index["booking_time"] = activity['begin_time']
                # 取活动基本服务费用信息
                apply_index["group_name"] = _old_order['base_fees'][0]['name']
                logging.info("create apply=[%r]", apply_index)
                apply_id = self.create_apply(apply_index)

                # budge_num increase
                self.counter_increase(vendor_id, "activity_apply")
                self.counter_increase(activity_id, "apply")
                # TODO notify this message to vendor's administrator by SMS

                # 更新联系人资料
                apply_index['account_id'] = _account_id
                _contact = contact_dao.contact_dao().query_by_realname(_account_id, apply_index["real_name"])
                logging.info("got old contact=[%r]", _contact)
                if not _contact: # 如果不存在
                    apply_index["_id"] = apply_id
                    contact_dao.contact_dao().create(apply_index)
                    logging.info("create contact=[%r]", apply_index)
                else: # 用新资料更新
                    apply_index["_id"] = _contact["_id"]
                    contact_dao.contact_dao().update(apply_index)
                    logging.info("update contact=[%r]", apply_index)

            _bonus_template = bonus_template_dao.bonus_template_dao().query(activity_id)
            _qrcode = group_qrcode_dao.group_qrcode_dao().query(activity_id)
            # 为活动添加二维码属性
            activity['wx_qrcode_url'] = _qrcode['wx_qrcode_url']
            logging.info(_qrcode)
            self.render('activity/activity-apply-step4.html',
                    vendor_id=vendor_id,
                    activity=activity,
                    bonus_template=_bonus_template)


# 微信支付结果通用通知
# 该链接是通过【统一下单API】中提交的参数notify_url设置，如果链接无法访问，商户将无法接收到微信通知。
# 通知url必须为直接可访问的url，不能携带参数。示例：notify_url：“https://pay.weixin.qq.com/wxpay/pay.action”
class WxOrderNotifyHandler(BaseHandler):
    def post(self):
        # 返回参数
        #<xml>
        # <appid><![CDATA[wxaa328c83d3132bfb]]></appid>\n
        # <attach><![CDATA[Aplan]]></attach>\n
        # <bank_type><![CDATA[CFT]]></bank_type>\n
        # <cash_fee><![CDATA[1]]></cash_fee>\n
        # <fee_type><![CDATA[CNY]]></fee_type>\n
        # <is_subscribe><![CDATA[Y]]></is_subscribe>\n
        # <mch_id><![CDATA[1340430801]]></mch_id>\n
        # <nonce_str><![CDATA[jOhHjqDfx9VQGmU]]></nonce_str>\n
        # <openid><![CDATA[oy0Kxt7zNpZFEldQmHwFF-RSLNV0]]></openid>\n
        # <out_trade_no><![CDATA[e358738e30fe11e69a7e00163e007b3e]]></out_trade_no>\n
        # <result_code><![CDATA[SUCCESS]]></result_code>\n
        # <return_code><![CDATA[SUCCESS]]></return_code>\n
        # <sign><![CDATA[6291D73149D05F09D18C432E986C4DEB]]></sign>\n
        # <time_end><![CDATA[20160613083651]]></time_end>\n
        # <total_fee>1</total_fee>\n
        # <trade_type><![CDATA[JSAPI]]></trade_type>\n
        # <transaction_id><![CDATA[4007652001201606137183943151]]></transaction_id>\n
        #</xml>
        _xml = self.request.body
        logging.info("got return_body %r", _xml)
        _pay_return = parseWxPayReturn(_xml)
        # wx支付结果记录保存
        _pay_return['_id'] = _pay_return['transaction_id']
        self.create_symbol_object(_pay_return)

        logging.info("got result_code %r", _pay_return['result_code'])
        logging.info("got total_fee %r", _pay_return['total_fee'])
        logging.info("got time_end %r", _pay_return['time_end'])
        logging.info("got transaction_id %r", _pay_return['transaction_id'])
        logging.info("got out_trade_no %r", _pay_return['out_trade_no'])

        _order_id = _pay_return['out_trade_no']
        _result_code = _pay_return['result_code']
        if _result_code == 'SUCCESS' :
            # 查询过去是否填报，有则跳过此步骤。主要是防止用户操作回退键，重新回到此页面
            order_index = self.get_order_index(_order_id)
            logging.info("got order_index=[%r]", order_index)
            # 用于更新积分、优惠券
            vendor_id = order_index['club_id']
            if order_index['pay_status'] == 30:
                return
            else:
                # 调用微信支付接口，返回成功
                # TODO: 更新订单索引中，订单状态pay_status,transaction_id,payed_total_fee
                order_payed = {
                    '_id':_order_id,
                    "pay_status": ORDER_STATUS_WECHAT_PAY_SUCCESS,
                    'transaction_id':_pay_return['transaction_id'],
                    'actual_payment':_pay_return['total_fee']
                }
                self.update_order_payed(order_payed)

                # 如使用积分抵扣，则将积分减去
                points = int(order_index['points_used'])
                if points < 0:
                    # 修改个人积分信息
                    bonus_points = {
                        'club_id':vendor_id,
                        'account_id':order_index['account_id'],
                        'account_type':'user',
                        'action': 'buy_activity',
                        'item_type': order_index['item_type'],
                        'item_id': order_index['item_id'],
                        'item_name': order_index['item_name'],
                        'bonus_type':'bonus',
                        'points': points,
                        'order_id': order_index['_id']
                    }
                    self.create_points(bonus_points)
                    # self.points_increase(vendor_id, order_index['account_id'], bonus)

                # 如使用代金券抵扣，则将代金券减去
                _vouchers = order_index['vouchers']
                for _voucher in _vouchers:
                    # status=2, 已使用
                    voucher_dao.voucher_dao().update({'_id':_voucher['_id'], 'status':2, 'last_update_time':_timestamp})
                    _customer_profile = mongodao().query_vendor_member_not_safe(vendor_id, order_index['account_id'])
                    # 修改个人代金券信息
                    _voucher_amount = int(_customer_profile['vouchers']) - int(_voucher['fee'])
                    if _voucher_amount < 0:
                        _voucher_amount = 0
                    _json = {'vendor_id':vendor_id, 'account_id':order_index['account_id'], 'last_update_time':_timestamp,
                        'vouchers':_voucher_amount}
                    vendor_member_dao.vendor_member_dao().update(_json)
        else:
            # 调用微信支付接口，返回成功
            # TODO: 更新订单索引中，订单状态pay_status,transaction_id,payed_total_fee
            order_payed = {'_id':_order_id,
                "pay_status": ORDER_STATUS_WECHAT_PAY_FAILED,
                'transaction_id':DEFAULT_USER_ID,
                'actual_payment':0}
            self.update_order_payed(order_payed)


class WxOrderWaitHandler(tornado.web.RequestHandler):
    def get(self):
        logging.info("wait for a moments")

        self.render('wx/orders-wait.html')


# 添加当前订单的成员
class WxHhaHandler(tornado.web.RequestHandler):
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        vendor_hha = vendor_hha_dao.vendor_hha_dao().query(vendor_id)

        self.render('wx/hold-harmless-agreements.html',
                vendor_id=vendor_id,
                vendor_hha=vendor_hha)

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
class WxItemsCategoryListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        category_id = self.get_argument("category_id", "")
        logging.info("got category_id %r", category_id)
        second_category_id = self.get_argument("second_category_id", "")
        logging.info("got second_category_id %r", second_category_id)
        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        url = API_DOMAIN + "/api/def/leagues/"+ LEAGUE_ID +"/categories"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        categorys = data['rs']

        if not category_id:
            category_id = categorys[0]['_id']

        url = API_DOMAIN + "/api/def/categories/" + category_id + "/level2"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        second_categorys = data['rs']

        # 获取商品数量
        cart_goods = self.get_cart(club_id)
        logging.info("got cart_goods %r", cart_goods)
        cart_goods_num = 0
        for cart_good in cart_goods:
            cart_goods_num += cart_good['quantity']
        logging.info("got cart_goods_num %r", cart_goods_num)

        second_specs = None
        second_brands = None
        if not second_category_id:
            second_category_id = second_categorys[0]['_id']

        url = API_DOMAIN + "/api/def/categories/"+ second_category_id +"/specs"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        second_specs = data['rs']

        url = API_DOMAIN + "/api/def/categories/"+ second_category_id +"/brands"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        second_brands = data['rs']

        club = self.get_club_basic_info(club_id)
        self.render('items/category.html',
                API_DOMAIN=API_DOMAIN,
                access_token=access_token,
                club=club,
                club_id=club_id,
                category_id=category_id,
                second_category_id=second_category_id,
                second_categorys=second_categorys,
                second_specs=second_specs,
                second_brands=second_brands,
                categorys=categorys,
                cart_goods_num=cart_goods_num)


# old分类列表
class WxItemsListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        # 查询分类
        _array = category_dao.category_dao().query_by_vendor(club_id)
        logging.info("got categories=[%r]", _array)
        category_num = len(_array)
        logging.info("got category_num", category_num)

        cart_goods = self.get_cart(club_id)
        logging.info("got cart_goods %r", cart_goods)
        # 获取商品数量
        cart_goods_num = 0
        for cart_good in cart_goods:
            cart_goods_num += cart_good['quantity']
        logging.info("got cart_goods_num %r", cart_goods_num)

        club = self.get_club_basic_info(club_id)
        private = 0
        items = self.get_items(club_id, ACTIVITY_STATUS_RECRUIT, private)
        logging.info("GET items %r", items)

        for item in items:
            # 格式化价格
            item['amount'] = float(item['amount']) / 100

        self.render('items/main.html',
                club=club,
                club_id=club_id,
                items=items,
                cart_goods_num=cart_goods_num,
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

        # url = API_DOMAIN + "/api/def/categories/"+ activity['level2_category_id'] +"/specs"
        # http_client = HTTPClient()
        # headers = {"Authorization":"Bearer " + access_token}
        # response = http_client.fetch(url, method="GET", headers=headers)
        # logging.info("got response.body %r", response.body)
        # data = json_decode(response.body)
        # specs = data['rs']

        url = API_DOMAIN + "/api/items/"+ item_id +"/specs"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        item_specs = data['rs']

        for item_spec in item_specs:
            item_spec['amount'] = float(item_spec['amount']) / 100

        # 获取购物车商品详情
        cart_goods = self.get_cart(club_id)
        logging.info("got cart_goods %r", cart_goods)

        # 获取商品数量
        cart_goods_num = 0
        for cart_good in cart_goods:
            cart_goods_num += cart_good['quantity']
        logging.info("got cart_goods_num %r", cart_goods_num)

        # 获取产品说明
        article = self.get_article(item_id)
        if not article:
            article = {'_id':activity_id, 'title':activity['title'], 'subtitle':[], 'img':activity['img'],'paragraphs':''}
            self.create_article(article)
        logging.info("got article %r", article)

        self.render('items/prodetail.html',
                api_domain= API_DOMAIN,
                access_token=access_token,
                cart_goods_num=cart_goods_num,
                club=club,
                club_id=club_id,
                item_id=item_id,
                item=item,
                item_specs=item_specs,
                article=article)

    # 添加商品到购物车
    # @tornado.web.authenticated  # if no session, redirect to login page
    # def post(self, club_id, item_id):
    #     logging.info("got club_id %r in uri", club_id)
    #     access_token = self.get_secure_cookie("access_token")
    #
    #     fee_template_id = self.get_argument('fee_template_id',"")
    #     logging.info("got fee_template_id %r in uri", fee_template_id)
    #     product_num = self.get_argument('product_num',"")
    #     logging.info("got product_num %r in uri", product_num)
    #
    #     item_type =  [{"item_id":item_id, "fee_template_id":fee_template_id, "quantity":product_num}]
    #     headers = {"Authorization":"Bearer "+access_token}
    #
    #     url = API_DOMAIN + "/api/clubs/"+ club_id +"/cart/items"
    #     _json = json_encode(item_type)
    #     http_client = HTTPClient()
    #     response = http_client.fetch(url, method="POST", headers=headers, body=_json)
    #     logging.info("update item response.body=[%r]", response.body)
    #
    #     self.redirect('/bf/wx/vendors/'+ club_id +'/items/'+item_id)


# 购物车
class WxItemsCartHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")

        self.render('items/cart.html',api_domain=API_DOMAIN,club_id=club_id,access_token=access_token)


# 提交订单页
class WxItemsSubmitOrderHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")

        self.render('items/submit-order.html',api_domain=API_DOMAIN,club_id=club_id,access_token=access_token)


# 调用wechat pay
class WxItemsOrderCheckoutHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self):
        club_id = self.get_argument("club_id", "")
        logging.info("got club_id %r", club_id)
        _account_id = self.get_secure_cookie("account_id")
        guest_club_id = self.get_argument("guest_club_id")
        logging.info("got guest_club_id %r", guest_club_id)

        access_token = self.get_access_token()
        item_id = "00000000000000000000000000000000"

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
        # logging.info("got _total_amount %r", _total_amount)
        # 订单申报数目
        quantity = 0

        bonus_points = 0
        #购物车商品json
        items = self.get_body_argument("items", [])
        logging.info("got items %r", items)
        items = JSON.loads(items)
        logging.info("got items %r", items)
        #收获地址
        addr = self.get_argument("addr", {})
        logging.info("got addr %r", addr)
        addr = JSON.loads(addr)
        logging.info("got addr %r", addr)
        #基本服务
        _base_fees = []

        # 附加服务项编号数组
        _ext_fees = []

        # 保险选项,数组
        _insurances = []

        #代金券选项,数组
        _vouchers = []

        # 积分选项,数组
        points = 0
        actual_payment = _total_amount + points
        logging.info("got actual_payment %r", actual_payment)

        _order_id = str(uuid.uuid1()).replace('-', '')
        _status = ORDER_STATUS_BF_INIT
        if actual_payment == 0:
            _status = ORDER_STATUS_WECHAT_PAY_SUCCESS

        # 创建订单索引
        order_index = {
            "_id": _order_id,
            "order_type": "buy_item",
            "club_id": club_id,
            "item_type": "items",
            "item_id": item_id,
            "item_name": "cart000",
            "distributor_type": "item",
            "items":items,
            "shipping_addr":addr,
            "distributor_id": "00000000000000000000000000000000",
            "create_time": _timestamp,
            "pay_type": "wxpay",
            "pay_status": _status,
            "quantity": quantity,
            "amount": _total_amount, #已经转换为分，注意转为数值
            "actual_payment": actual_payment, #已经转换为分，注意转为数值
            "base_fees": _base_fees,
            "ext_fees": _ext_fees,
            "insurances": _insurances,
            "vouchers": _vouchers,
            "points_used": points,
            "bonus_points": bonus_points, # 活动奖励积分
            "booking_time": _timestamp,
        }
        order_id = self.create_order(order_index)

        order = self.get_symbol_object(order_id)
        logging.info("GET order %r", order)
        order['create_time'] = timestamp_datetime(float(order['create_time']))
        items = order['items']
        logging.info("GET items %r", items)
        address = order['shipping_addr']
        logging.info("GET address %r", address)

        for item in items:
            item['amount'] = float(item['amount'])/100

        # 清空购物车
        headers = {"Authorization":"Bearer "+access_token}

        url = API_DOMAIN + "/api/clubs/"+ club_id +"/cart/items"
        http_client = HTTPClient()
        response = http_client.fetch(url, method="DELETE", headers=headers)
        logging.info("update item response.body=[%r]", response.body)

        # budge_num increase
        self.counter_increase(club_id, "item_order")
        # self.counter_increase(order_id, "order")
        # TODO notify this message to vendor's administrator by SMS

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        logging.info("got wx_app_id %r in uri", wx_app_id)
        wx_app_secret = wx_app_info['wx_app_secret']
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
            _product_description = "order_title"
            # logging.info("got _product_description %r", _product_description)
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

            self.render('items/order-confirm.html',
                    access_token = access_token,
                    api_domain = API_DOMAIN,
                    address=address,
                    club_id=club_id,
                    return_msg=response.body, order_return=_order_return,
                    order=order, items=items, order_index=order_index)
            # self.redirect('/bf/wx/vendors/'+ club_id +'/items/checkout/orders/'+order_id)

        else: #actual_payment == 0:
            # 如使用积分抵扣，则将积分减去
            if order_index['points_used'] < 0:
                # 修改个人积分信息
                bonus_points = {
                    'org_id':club_id,
                    'org_type':'club',
                    'account_id':_account_id,
                    'account_type':'user',
                    'action': 'buy_activity',
                    'item_type': 'activity',
                    'item_id': "00000000000000000000000000000000",
                    'item_name': 'order_title',
                    'bonus_type':'bonus',
                    'points': points,
                    'order_id': order_index['_id']
                }
                self.create_points(bonus_points)
                # self.points_decrease(club_id, order_index['account_id'], order_index['points_used'])

            # 如使用代金券抵扣，则将代金券减去
            for _voucher in _vouchers:
                # status=2, 已使用
                voucher_dao.voucher_dao().update({'_id':_voucher['_id'], 'status':2, 'last_update_time':_timestamp})
                _customer_profile = vendor_member_dao.vendor_member_dao().query_not_safe(club_id, order_index['account_id'])
                # 修改个人代金券信息
                _voucher_amount = int(_customer_profile['vouchers']) - int(_voucher['fee'])
                if _voucher_amount < 0:
                    _voucher_amount = 0
                _json = {'vendor_id':club_id, 'account_id':order_index['account_id'], 'last_update_time':_timestamp,
                        'vouchers':_voucher_amount}
                vendor_member_dao.vendor_member_dao().update(_json)

            # send message to wx 公众号客户 by template
            wx_access_token = wx_wrap.getAccessTokenByClientCredential(WX_APP_ID, WX_APP_SECRET)
            logging.info("got wx_access_token %r", wx_access_token)
            # 通过wxpub，给俱乐部操作员发送通知
            ops = self.get_club_ops_wx(club_id)
            for op in ops:
                wx_openid = op['binding_id']
                logging.info("got wx_openid %r", wx_openid)
                wx_wrap.sendOrderPayedToOpsMessage(wx_access_token, WX_NOTIFY_DOMAIN, wx_openid, order_index)
            self.render('items/order-confirm.html',
                    access_token = access_token,
                    api_domain = API_DOMAIN,
                    club_id=club_id,
                    address=address,
                    return_msg=response.body, order_return=_order_return,
                    order=order, items=items, order_index=order_index)


# 下单成功后的订单详情
class WxItemsOrderResultHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, order_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")
        order = self.get_symbol_object(order_id)
        logging.info("GET order %r", order)
        pay_status = order['pay_status']
        order['create_time'] = timestamp_datetime(float(order['create_time']))
        items = order['items']
        logging.info("GET items %r", items)
        address= order['shipping_addr']
        order['amount'] = float(order['amount'])/100
        for item in items:
            item['amount'] = float(item['amount'])/100

        self.render('items/order-result.html',
                        api_domain=API_DOMAIN,
                        club_id=club_id,
                        items=items,
                        address=address,
                        access_token=access_token,
                        order_id=order_id,
                        order=order)


# 订单中心
class WxItemsMyordersHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        params = {"club_id":club_id, "filter":"mine", "page":1, "limit":20, "order_type":"buy_item", "pay_status":"all"}
        url = url_concat(API_DOMAIN + "/api/orders", params)
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        orders = rs['data']

        params = {"club_id":club_id, "filter":"mine", "page":1, "limit":20, "order_type":"buy_item", "pay_status":30}
        url = url_concat(API_DOMAIN + "/api/orders", params)
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        payed_orders = rs['data']

        params = {"club_id":club_id, "filter":"mine", "page":1, "limit":20, "order_type":"buy_item", "pay_status":20}
        url = url_concat(API_DOMAIN + "/api/orders", params)
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        nopay_orders = rs['data']

        for order in orders:
            order['create_time'] = timestamp_datetime(float(order['create_time']))
            order['amount'] = float(order['amount'])/100
            order['actual_payment'] = float(order['actual_payment'])/100

        for order in payed_orders:
            order['create_time'] = timestamp_datetime(float(order['create_time']))
            order['amount'] = float(order['amount'])/100
            order['actual_payment'] = float(order['actual_payment'])/100

        for order in nopay_orders:
            order['create_time'] = timestamp_datetime(float(order['create_time']))
            order['amount'] = float(order['amount'])/100
            order['actual_payment'] = float(order['actual_payment'])/100

        self.render('items/myorders.html',
                club_id=club_id,
                orders=orders,
                payed_orders=payed_orders,
                nopay_orders=nopay_orders)


# 预估分类列表
class WxItemsRecommendListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        club = self.get_club_basic_info(club_id)
        self.render('items/recommend-category.html',
                API_DOMAIN=API_DOMAIN,
                access_token=access_token,
                LEAGUE_ID=LEAGUE_ID,
                club=club,
                club_id=club_id)


# 预估商品列表
class WxItemsRecommendProductsHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, recommend_category_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)
        logging.info("got recommend_category_id %r", recommend_category_id)

        self.render('items/recommend-products.html',
                     api_domain=API_DOMAIN,
                     club_id=club_id,
                     access_token=access_token,
                     recommend_category_id=recommend_category_id)

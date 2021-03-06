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
from dao import vendor_wx_dao

from foo.wx import wx_wrap
from xml_parser import parseWxOrderReturn, parseWxPayReturn
from global_const import *


# 俱乐部首页
class WxItemsIndexHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("got club_id %r", club_id)
        access_token = self.get_access_token()

        guest_id = DEFAULT_USER_ID
        if len(club_id) == 32:
            guest_id = DEFAULT_USER_ID
        elif len(club_id) == 64:
            guest_id = club_id[32:64]
            club_id = club_id[0:32]
        else:
            guest_id = club_id[32:64]
            club_id = club_id[0:32]
        logging.info("got club_id=[%r]", club_id)
        logging.info("got guest_id=[%r]", guest_id)

        # club = self.get_club_basic_info(club_id)
        # logging.info("got club %r", club)

        url = API_DOMAIN+"/api/clubs/"+club_id
        http_client = HTTPClient()
        response = http_client.fetch(url, method="GET")
        logging.info("got response %r", response.body)
        data = json_decode(response.body)
        club = data['rs']
        if not club.has_key('img'):
            club['img'] = ''
        if not club.has_key('paragraphs'):
            club['paragraphs'] = ''

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/index"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        self.render('items/main.html',
                api_domain = API_DOMAIN,
                access_token=access_token,
                club_id = club_id,
                club=club,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)


# 默认分类列表
class WxItemsCategoryListDefaultHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self):
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("GET %r", self.request.uri)

        club_id = CLUB_ID
        last_visit_club_id = self.get_cookie("last_visit_club_id")
        logging.info("got last_visit_club_id=[%r]", last_visit_club_id)
        if last_visit_club_id == None:
            last_visit_club_id = club_id
            self.set_cookie("last_visit_club_id", last_visit_club_id)
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/category/items")
        else:
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/category/items")


# 分类列表
class WxItemsCategoryListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("GET %r", self.request.uri)

        self.set_cookie("last_visit_club_id", club_id)

        guest_id = DEFAULT_USER_ID
        if len(club_id) == 32:
            guest_id = DEFAULT_USER_ID
        elif len(club_id) == 64:
            guest_id = club_id[32:64]
            club_id = club_id[0:32]
        else:
            guest_id = club_id[32:64]
            club_id = club_id[0:32]
        logging.info("got club_id=[%r]", club_id)
        logging.info("got guest_id=[%r]", guest_id)

        category_id = self.get_argument("category_id", "")
        logging.info("got category_id %r", category_id)
        second_category_id = self.get_argument("second_category_id", "")
        logging.info("got second_category_id %r", second_category_id)
        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token=[%r]", access_token)
        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        club = self.get_club_basic_info(club_id)
        logging.info("get club %r",club)
        league_id = club['league_id']

        url = API_DOMAIN + "/api/def/leagues/"+ league_id +"/categories"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.debug("got categorys response.body %r", response.body)
        data = json_decode(response.body)
        categorys = data['rs']

        if not category_id:
            category_id = categorys[0]['_id']

        url = API_DOMAIN + "/api/def/categories/" + category_id + "/level2"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.debug("got second_categorys response.body %r", response.body)
        data = json_decode(response.body)
        second_categorys = data['rs']

        # 获取商品数量  /api/clubs/([a-z0-9]*)/cart/nums
        url = API_DOMAIN + "/api/clubs/" + club_id + "/cart/nums"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.debug("got cart_goods_num response.body %r", response.body)
        data = json_decode(response.body)
        cart_goods_num = data['data']['quantity']
        logging.info("got cart_goods_num %r", cart_goods_num)

        second_specs = None
        second_brands = None
        if not second_category_id:
            second_category_id = second_categorys[0]['_id']

        url = API_DOMAIN + "/api/def/categories/"+ second_category_id +"/specs"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.debug("got second_specs response.body %r", response.body)
        data = json_decode(response.body)
        second_specs = data['rs']

        url = API_DOMAIN + "/api/def/categories/"+ second_category_id +"/brands"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.debug("got second_brands response.body %r", response.body)
        data = json_decode(response.body)
        second_brands = data['rs']

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

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
                cart_goods_num=cart_goods_num,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)


# 规格分类列表
class WxItemsCategorySpecsListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, spec_id):
        logging.info("GET %r", self.request.uri)
        category_id = self.get_argument("category_id", "")
        logging.info("got category_id %r", category_id)
        second_category_id = self.get_argument("second_category_id", "")
        logging.info("got second_category_id %r", second_category_id)
        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        club = self.get_club_basic_info(club_id)
        logging.info("get club %r",club)
        league_id = club['league_id']

        url = API_DOMAIN + "/api/def/leagues/"+ league_id +"/categories"
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

        # 获取商品数量  /api/clubs/([a-z0-9]*)/cart/nums
        url = API_DOMAIN + "/api/clubs/" + club_id + "/cart/nums"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        cart_goods_num = data['data']['quantity']
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

        url = API_DOMAIN + "/api/def/specs/"+spec_id
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        _spec = data['rs']

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        club = self.get_club_basic_info(club_id)
        self.render('items/category-specs.html',
                API_DOMAIN=API_DOMAIN,
                access_token=access_token,
                club=club,
                club_id=club_id,
                spec_id=spec_id,
                category_id=category_id,
                second_category_id=second_category_id,
                second_categorys=second_categorys,
                second_specs=second_specs,
                second_brands=second_brands,
                categorys=categorys,
                _spec=_spec,
                cart_goods_num=cart_goods_num,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)


# 品牌分类列表
class WxItemsCategoryBrandsListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, brand_id):
        logging.info("GET %r", self.request.uri)
        category_id = self.get_argument("category_id", "")
        logging.info("got category_id %r", category_id)
        second_category_id = self.get_argument("second_category_id", "")
        logging.info("got second_category_id %r", second_category_id)
        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        club = self.get_club_basic_info(club_id)
        logging.info("get club %r",club)
        league_id = club['league_id']

        url = API_DOMAIN + "/api/def/leagues/"+ league_id +"/categories"
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

        # 获取商品数量  /api/clubs/([a-z0-9]*)/cart/nums
        url = API_DOMAIN + "/api/clubs/" + club_id + "/cart/nums"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        cart_goods_num = data['data']['quantity']
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

        url = API_DOMAIN + "/api/def/brands/"+brand_id
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        _brand = data['rs']

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        club = self.get_club_basic_info(club_id)
        self.render('items/category-brands.html',
                API_DOMAIN=API_DOMAIN,
                access_token=access_token,
                club=club,
                club_id=club_id,
                brand_id=brand_id,
                category_id=category_id,
                second_category_id=second_category_id,
                second_categorys=second_categorys,
                second_specs=second_specs,
                second_brands=second_brands,
                categorys=categorys,
                _brand=_brand,
                cart_goods_num=cart_goods_num,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)


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
            article = {'_id':item_id, 'title':item['title'], 'subtitle':[], 'img':item['img'],'paragraphs':''}
            self.create_article(article)
        logging.info("got article %r", article)

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        self.render('items/prodetail.html',
                api_domain= API_DOMAIN,
                access_token=access_token,
                cart_goods_num=cart_goods_num,
                club=club,
                club_id=club_id,
                item_id=item_id,
                item=item,
                item_specs=item_specs,
                article=article,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)

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


# 默认购物车
class WxItemsCartDefaultHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self):
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("GET %r", self.request.uri)

        last_visit_club_id = self.get_cookie("last_visit_club_id")
        logging.info("got last_visit_club_id=[%r]", last_visit_club_id)
        if last_visit_club_id == None:
            last_visit_club_id = CLUB_ID
            self.set_cookie("last_visit_club_id", last_visit_club_id)
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/items/cart")
        else:
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/items/cart")


# 购物车
class WxItemsCartHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")

        self.set_cookie("last_visit_club_id", club_id)

        self.render('items/cart.html',api_domain=API_DOMAIN,club_id=club_id,access_token=access_token)


# 提交订单页
class WxItemsSubmitOrderHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_secure_cookie("access_token")
        account_id = self.get_secure_cookie("account_id")

        club = self.get_club_basic_info(club_id)
        logging.info("get club %r",club)
        league_id = club['league_id']

        self.render('items/submit-order.html',api_domain=API_DOMAIN,league_id=league_id, club_id=club_id,access_token=access_token,account_id=account_id)


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

        _timestamp = int(time.time())
        # 一分钟内不能创建第二个订单,
        # 防止用户点击回退按钮，产生第二个订单
        if len(orders) > 0:
            for order in orders:
                if (_timestamp - order['create_time']) < 60:
                    self.redirect('/bf/wx/orders/wait')
                    return

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
        #是否需要发票
        billing = self.get_argument("billing",'0')
        logging.info("got billing %r", billing)
        billing_addr = {'tfn':'','company_title':''}
        # 发票信息
        if billing == '1':
            _addr = self.get_argument("billing_addr",{})
            logging.info("got _addr %r", _addr)
            billing_addr = JSON.loads(_addr)
            logging.info("got billing_addr %r", billing_addr)

        coupon = self.get_argument('coupon',0)
        logging.info("got coupon %r",coupon)
        coupon = JSON.loads(coupon)

        # 积分
        used_points = self.get_argument('used_points',0)
        logging.info("got used_points %r",used_points)

        order_id = str(uuid.uuid1()).replace('-', '')
        # 创建订单索引
        order_index = {
            "_id": order_id,
            "order_type": "buy_item",
            "club_id": club_id,
            "item_type": "items",
            "item_id": item_id,
            "item_name": "", # 由服务器端填写第一个商品名称
            "distributor_type": "item",
            "items":items,
            "shipping_addr":addr,
            "shipping_cost":0, # 由服务器端计算运费
            "billing_required":billing,
            "billing_addr":billing_addr,
            "coupon":coupon,
            "distributor_id": "00000000000000000000000000000000",
            "create_time": _timestamp,
            "pay_type": "wxpay",
            "pay_status": ORDER_STATUS_BF_INIT,
            "quantity": 0, # 由服务器端计算商品数量
            "amount": 0, # 由服务器端计算商品合计
            "actual_payment": 0, # 由服务器端计算实际支付金额
            "base_fees": [], #基本服务
            "ext_fees": [], # 附加服务项编号数组
            "insurances": [], # 保险选项,数组
            "vouchers": [], #代金券选项,数组
            "points_used": used_points, # 使用积分数量
            "bonus_points": 0, # 购买商品获得奖励积分
            "booking_time": _timestamp,
        }
        pay_id = self.create_order(order_index)

        order = self.get_symbol_object(order_id)
        logging.info("GET order %r", order)
        order['create_time'] = timestamp_datetime(float(order['create_time']))
        # order['shipping_cost'] = float(order['shipping_cost'])/100
        # order['actual_payment'] = float(order['actual_payment'])/100
        items = order['items']
        _product_description = items[0]['title']
        logging.info("GET items %r", items)
        shipping_addr = order['shipping_addr']
        logging.info("GET shipping_addr %r", shipping_addr)
        billing_addr = order['billing_addr']
        logging.info("GET billing_addr %r", billing_addr)

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

        # 如使用积分抵扣，则将积分减去
        if order_index['points_used'] > 0:
            # 修改个人积分信息
            bonus_points = {
                'org_id':club_id,
                'org_type':'club',
                'account_id':_account_id,
                'account_type':'user',
                'action': 'buy_item',
                'item_type': 'items',
                'item_id': order['item_id'],
                'item_name': order['item_name'],
                'bonus_type':'bonus',
                'points': used_points,
                'order_id': order_index['_id']
            }
            self.create_points(bonus_points)

        if order['actual_payment'] != 0:
            # wechat 统一下单
            myinfo = self.get_myinfo_login()
            _openid = myinfo['login']
            _store_id = 'Aplan'
            logging.info("got _store_id %r", _store_id)
            #_ip = self.request.remote_ip
            _remote_ip = self.request.headers['X-Real-Ip']
            _order_return = wx_wrap.getUnifiedOrder(_remote_ip, wx_app_id, _store_id, _product_description, wx_notify_domain, wx_mch_id, wx_mch_key, _openid, pay_id, order['actual_payment'], _timestamp)

            # wx统一下单记录保存
            _order_return['_id'] = _order_return['prepay_id']
            self.create_symbol_object(_order_return)

            # 微信统一下单返回成功
            order_unified = None
            if(_order_return['return_msg'] == 'OK'):
                order_unified = {'_id':order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_SUCCESS}
            else:
                order_unified = {'_id':order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_FAILED}
            # 微信统一下单返回成功
            # TODO: 更新订单索引中，订单状态pay_status,prepay_id
            self.update_order_unified(order_unified)

            for item in items:
                item['amount'] = float(item['amount'])/100

            self.render('items/order-confirm.html',
                    access_token = access_token,
                    api_domain = API_DOMAIN,
                    shipping_addr=shipping_addr,
                    billing_addr=billing_addr,
                    club_id=club_id,
                    return_msg=response.body, order_return=_order_return,
                    order=order, items=items,     )
            # self.redirect('/bf/wx/vendors/'+ club_id +'/items/checkout/orders/'+order_id)

        else: #actual_payment == 0:
            # send message to wx 公众号客户 by template
            wx_access_token = wx_wrap.getAccessTokenByClientCredential(WX_APP_ID, WX_APP_SECRET)
            logging.info("got wx_access_token %r", wx_access_token)
            # 通过wxpub，给俱乐部操作员发送通知
            ops = self.get_club_ops_wx(club_id)
            for op in ops:
                wx_openid = op['binding_id']
                logging.info("got wx_openid %r", wx_openid)
                if order_index['order_type'] == "buy_activity":
                    wx_wrap.sendActivityOrderPayedToOpsMessage(wx_access_token, WX_NOTIFY_DOMAIN, wx_openid, order_index)
                elif order_index['order_type'] == "buy_item":
                    logging.info("sendItemOrderPayedToOpsMessage=[%r]", WX_MESSAGE_TEMPLATE)
                    if WX_MESSAGE_TEMPLATE == "kkfcps":
                        wx_wrap.sendItemOrderPayedToOpsMessage_kkfcps(wx_access_token, WX_NOTIFY_DOMAIN, wx_openid, order_index)
                    else:
                        wx_wrap.sendItemOrderPayedToOpsMessage(wx_access_token, WX_NOTIFY_DOMAIN, wx_openid, order_index)

            self.render('items/order-result.html',
                        api_domain=API_DOMAIN,
                        club_id=club_id,
                        items=items,
                        shipping_addr=shipping_addr,
                        billing_addr=billing_addr,
                        access_token=access_token,
                        order_id=order['_id'],
                        order=order)


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
        shipping_addr= order['shipping_addr']
        billing_addr= order['billing_addr']

        self.render('items/order-result.html',
                        api_domain=API_DOMAIN,
                        club_id=club_id,
                        items=items,
                        shipping_addr=shipping_addr,
                        billing_addr=billing_addr,
                        access_token=access_token,
                        order_id=order_id,
                        order=order)


# 重新支付订单操作
class WxOrdersCheckoutHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self):
        club_id = self.get_argument("club_id", "")
        logging.info("got club_id %r", club_id)

        _account_id = self.get_secure_cookie("account_id")
        order_id = self.get_argument("order_id","")
        logging.info("got order_id %r",order_id)

        access_token = self.get_access_token()
        item_id = "00000000000000000000000000000000"
        guest_club_id = "00000000000000000000000000000000"

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

        # 更改pay_id
        url = API_DOMAIN + "/api/orders/"+order_id+"/payid"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        _json = json_encode(headers)
        response = http_client.fetch(url, method="POST", headers=headers, body=_json)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        rs = data['rs']
        pay_id = rs['pay_id']

        order = self.get_symbol_object(order_id)
        _product_description = order['items'][0]['title']
        actual_payment = order['actual_payment']
        _timestamp = (int)(time.time())
        items = order['items']

        order['create_time'] = timestamp_datetime(float(order['create_time']))
        # order['shipping_cost'] = float(order['shipping_cost'])/100
        # order['actual_payment'] = float(order['actual_payment'])/100

        shipping_addr = order['shipping_addr']
        logging.info("GET shipping_addr %r", shipping_addr)
        billing_addr = order['billing_addr']
        logging.info("GET billing_addr %r", billing_addr)

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
            #_ip = self.request.remote_ip
            _remote_ip = self.request.headers['X-Real-Ip']
            _order_return = wx_wrap.getUnifiedOrder(_remote_ip, wx_app_id, _store_id, _product_description, wx_notify_domain, wx_mch_id, wx_mch_key, _openid, pay_id, actual_payment, _timestamp)

            # wx统一下单记录保存
            _order_return['_id'] = _order_return['prepay_id']
            self.create_symbol_object(_order_return)

            # 微信统一下单返回成功
            order_unified = None
            if(_order_return['return_msg'] == 'OK'):
                order_unified = {'_id':order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_SUCCESS}
            else:
                order_unified = {'_id':order_id,'prepay_id': _order_return['prepay_id'], 'pay_status': ORDER_STATUS_WECHAT_UNIFIED_FAILED}
            # 微信统一下单返回成功
            # TODO: 更新订单索引中，订单状态pay_status,prepay_id
            self.update_order_unified(order_unified)

            self.render('items/re-order-confirm.html',
                    access_token = access_token,
                    api_domain = API_DOMAIN,
                    shipping_addr=shipping_addr,
                    billing_addr=billing_addr,
                    club_id=club_id,
                    return_msg=response.body, order_return=_order_return,
                    order=order, items=items)


# 默认个人订单列表
class WxItemsMyordersDefaultHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self):
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("GET %r", self.request.uri)

        last_visit_club_id = self.get_cookie("last_visit_club_id")
        logging.info("got last_visit_club_id=[%r]", last_visit_club_id)
        if last_visit_club_id == None:
            last_visit_club_id = CLUB_ID
            self.set_cookie("last_visit_club_id", last_visit_club_id)
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/items/myorders")
        else:
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/items/myorders")


# 订单中心-所有订单
class WxItemsMyordersHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        self.set_cookie("last_visit_club_id", club_id)

        self.render('items/myorders.html',
                club_id=club_id,
                API_DOMAIN=API_DOMAIN,
                access_token=access_token)


# 订单中心-已支付订单
class WxItemsPayMyordersHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        self.render('items/pay-myorders.html',
                club_id=club_id,
                API_DOMAIN=API_DOMAIN,
                access_token=access_token)


# 订单中心-未支付订单
class WxItemsNopayMyordersHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        self.render('items/nopay-myorders.html',
                club_id=club_id,
                API_DOMAIN=API_DOMAIN,
                access_token=access_token)


# 默认预估分类列表
class WxItemsRecommendListDefaultHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self):
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^^^^^")
        logging.info("GET %r", self.request.uri)

        last_visit_club_id = self.get_cookie("last_visit_club_id")
        logging.info("got last_visit_club_id=[%r]", last_visit_club_id)
        if last_visit_club_id == None:
            last_visit_club_id = CLUB_ID
            self.set_cookie("last_visit_club_id", last_visit_club_id)
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/recommend")
        else:
            self.redirect("/bf/wx/vendors/"+ last_visit_club_id +"/recommend")


# 预估分类列表
class WxItemsRecommendListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id):
        logging.info("GET %r", self.request.uri)
        self.set_cookie("last_visit_club_id", club_id)

        # 查询分类
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)

        club = self.get_club_basic_info(club_id)
        league_id = club['league_id']

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        self.render('items/recommend-category.html',
                API_DOMAIN=API_DOMAIN,
                access_token=access_token,
                LEAGUE_ID=league_id,
                club=club,
                club_id=club_id,
                wx_app_id=wx_app_id,
                share_url=share_url,
                sign=_sign)


# 预估商品列表
class WxItemsRecommendProductsHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, club_id, recommend_category_id):
        logging.info("GET %r", self.request.uri)
        logging.info("GET club_id %r", club_id)
        access_token = self.get_access_token()
        logging.info("GET access_token %r", access_token)
        logging.info("got recommend_category_id %r", recommend_category_id)

        club = self.get_club_basic_info(club_id)

        my_account_id = self.get_secure_cookie("account_id")
        logging.info("GET my_account_id=[%r]", my_account_id)

        wx_app_info = vendor_wx_dao.vendor_wx_dao().query(club_id)
        wx_app_id = wx_app_info['wx_app_id']
        wx_app_secret = wx_app_info['wx_app_secret']
        wx_notify_domain = wx_app_info['wx_notify_domain']
        logging.info("got wx_app_info=[%r]", wx_app_info)

        wx_access_token = wx_wrap.getAccessTokenByClientCredential(wx_app_id, wx_app_secret)
        _jsapi_ticket = wx_wrap.getJsapiTicket(wx_access_token)
        _url = wx_notify_domain + self.request.uri
        share_url = wx_notify_domain + "/bf/wx/vendors/"+club_id+my_account_id+"/category/items"
        _sign = wx_wrap.Sign(_jsapi_ticket, _url).sign()
        logging.info("got sign=[%r]", _sign)

        self.render('items/recommend-products.html',
                     api_domain=API_DOMAIN,
                     club_id=club_id,
                     club=club,
                     access_token=access_token,
                     recommend_category_id=recommend_category_id,
                     wx_app_id=wx_app_id,
                     share_url=share_url,
                     sign=_sign)


# 我的历史积分列表页
class WxItemsUserPointsHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        account_id = self.get_secure_cookie("account_id")
        access_token = self.get_access_token()

        # 获取当前积分
        url = API_DOMAIN + "/api/clubs/"+vendor_id+"/users/" + account_id
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        _customer_profile = data['rs']
        bonus_num = _customer_profile['remaining_points']

        self.render('items/user-points.html',
                api_domain = API_DOMAIN,
                access_token = access_token,
                account_id = account_id,
                vendor_id=vendor_id,
                bonus_num=bonus_num)


# 我的上下线
class WxItemsUserlinesHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        account_id = self.get_secure_cookie("account_id")
        access_token = self.get_access_token()

        # 上级
        url = API_DOMAIN + "/api/clubs/"+vendor_id+"/acquaintance/"+account_id+"/higher"
        http_client = HTTPClient()
        headers = {"Authorization":"Bearer " + access_token}
        response = http_client.fetch(url, method="GET", headers=headers)
        logging.info("got response.body %r", response.body)
        data = json_decode(response.body)
        higher = data['rs']
        if higher:
            higher['ctime'] = timestamp_datetime(float(higher['ctime']))

        self.render('items/user-lines.html',
                vendor_id=vendor_id,
                account_id=account_id,
                higher=higher,
                api_domain=API_DOMAIN,
                access_token = access_token)

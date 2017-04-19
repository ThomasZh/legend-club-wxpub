#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import hashlib
import logging
import random
import string
import time

from tornado.escape import json_decode
from tornado.httpclient import HTTPClient

from xml_parser import parseWxOrderReturn, parseWxPayReturn


def getAccessTokenByClientCredential(appId, appSecret):
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid="+appId+"&secret="+appSecret
    http_client = HTTPClient()
    response = http_client.fetch(url, method="GET")
    logging.info("got response %r", response.body)
    accessToken = json_decode(response.body)
    return accessToken["access_token"]


def getJsapiTicket(accessToken):
    url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token="+accessToken+"&type=jsapi"
    http_client = HTTPClient()
    response = http_client.fetch(url, method="GET")
    logging.info("got response %r", response.body)
    jsapiTicket = json_decode(response.body)
    return jsapiTicket["ticket"]


def getNonceStr():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))


# wechat 统一下单
def getUnifiedOrder(remote_ip, wx_app_id, store_id, product_description, wx_notify_domain, wx_mch_id, wx_mch_key, openid, order_id, actual_payment, timestamp):
    key = wx_mch_key
    nonceA = getNonceStr();
    logging.info("got nonceA %r", nonceA)
    total_fee = str(actual_payment)
    logging.info("got total_fee %r", total_fee)
    notify_url = wx_notify_domain + '/bf/wx/orders/notify'
    logging.info("got notify_url %r", notify_url)
    signA = getOrderSign(remote_ip, notify_url, wx_app_id, wx_mch_id, nonceA, openid, key, store_id, order_id, product_description, total_fee)
    logging.info("got signA %r", signA)

    _xml = '<xml>' \
        + '<appid>' + wx_app_id + '</appid>' \
        + '<attach>' + store_id + '</attach>' \
        + '<body>' + product_description + '</body>' \
        + '<mch_id>' + wx_mch_id + '</mch_id>' \
        + '<nonce_str>' + nonceA + '</nonce_str>' \
        + '<notify_url>' + notify_url + '</notify_url>' \
        + '<openid>' + openid + '</openid>' \
        + '<out_trade_no>' + order_id + '</out_trade_no>' \
        + '<spbill_create_ip>' + remote_ip + '</spbill_create_ip>' \
        + '<total_fee>' + str(actual_payment) + '</total_fee>' \
        + '<trade_type>JSAPI</trade_type>' \
        + '<sign>' + signA + '</sign>' \
        + '</xml>'
    url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    http_client = HTTPClient()
    response = http_client.fetch(url, method="POST", body=_xml)
    logging.info("got response %r", response.body)
    order_return = parseWxOrderReturn(response.body)

    if not order_return.has_key('prepay_id'):
        order_return['prepay_id'] = ""
    logging.info("got prepayId %r", order_return['prepay_id'])
    if not order_return.has_key('nonce_str'):
        order_return['nonce_str'] = ''
    signB = getPaySign(timestamp, wx_app_id, order_return['nonce_str'], order_return['prepay_id'], key)
    logging.info("got signB %r", signB)
    order_return['pay_sign'] = signB
    order_return['timestamp'] = timestamp
    order_return['app_id'] = wx_app_id

    return order_return


def getOrderSign(remoteIp, notify_url, appId, mchId, nonceA, openId, key, storeId, orderId, productDescription, total_fee):
    # "http://" + domain + "/bf/wx/orders/notify"
    # 'http://'+ domain + '/bf/wx/voucher-orders/notify'
    stringA = "appid=" + appId + \
        "&attach=" + storeId + \
        "&body=" + productDescription + \
        "&mch_id=" + mchId + \
        "&nonce_str=" + nonceA + \
        "&notify_url=" + notify_url + \
        "&openid=" + openId + \
        "&out_trade_no=" + orderId + \
        "&spbill_create_ip=" + remoteIp + \
        "&total_fee=" + total_fee + \
        "&trade_type=JSAPI"
    stringSignTemp = stringA + "&key=" + key;
    signA = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest().upper();
    return signA


def getPaySign(timeStamp, appId, nonceA, prepayId, key):
    stringB = "appId=" + appId + \
        "&nonceStr=" + nonceA + \
        "&package=prepay_id=" + prepayId + \
        "&signType=MD5" + \
        "&timeStamp=" + str(timeStamp)
    stringSignTemp = stringB + "&key=" + key;
    signB = hashlib.md5(stringSignTemp).hexdigest().upper();
    return signB


# 注意 URL 一定要动态获取，不能 hardcode
# sign = Sign('jsapi_ticket', 'http://example.com')
# print sign.sign()
class Sign:
    def __init__(self, jsapi_ticket, url):
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': jsapi_ticket,
            'timestamp': self.__create_timestamp(),
            'url': url
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        stringA = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(stringA).hexdigest()
        return self.ret


def getAccessToken(appId, appSecret, code):
    url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid="+appId+"&secret="+appSecret+"&code="+code+"&grant_type=authorization_code"
    http_client = HTTPClient()
    response = http_client.fetch(url, method="GET")
    logging.info("got response %r", response.body)
    accessToken = json_decode(response.body)
    return accessToken


def getUserInfo(token, openid):
    url = "https://api.weixin.qq.com/sns/userinfo?access_token="+token+"&openid="+openid+"&lang=zh_CN"
    http_client = HTTPClient()
    response = http_client.fetch(url, method="GET")
    logging.info("got response %r", response.body)
    userInfo = json_decode(response.body)
    return userInfo

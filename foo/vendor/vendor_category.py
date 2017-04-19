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
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))
from comm import *
from dao import budge_num_dao
from dao import category_dao
from global_const import *
import uuid


# 这里vendorid是应该动态得到并赋值
class VendorIndexHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self):
        ops = self.get_ops_info()
        logging.info("got ops %r in uri", ops)

        self.redirect('/vendors/' + ops['club_id'] + '/categorys')


# /vendors/<string:vendor_id>/categorys/<string:category_id>/delete
class VendorCategoryDeleteHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id, category_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got category_id %r in uri", category_id)

        ops = self.get_ops_info()

        category_dao.category_dao().delete(category_id)

        self.redirect('/vendors/' + vendor_id + '/categorys')


# /vendors/<string:vendor_id>/categorys
class VendorCategoryListHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        ops = self.get_ops_info()

        categorys = category_dao.category_dao().query_by_vendor(vendor_id)
        counter = self.get_counter(vendor_id)
        self.render('vendor/category-list.html',
                vendor_id=vendor_id,
                ops=ops,
                counter=counter,
                categorys=categorys)


# /vendors/<string:vendor_id>/categorys/create
class VendorCategoryCreateHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        ops = self.get_ops_info()

        counter = self.get_counter(vendor_id)
        self.render('vendor/category-create.html',
                vendor_id=vendor_id,
                ops=ops,
                counter=counter)

    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        ops = self.get_ops_info()

        title = self.get_argument("title", "")
        desc = self.get_argument("desc", "")
        bk_img_url = self.get_argument("bk_img_url", "")
        logging.debug("got param title %r", title)
        logging.debug("got param desc %r", desc)
        logging.debug("got param bk_img_url %r", bk_img_url)

        _id = str(uuid.uuid1()).replace('-', '')
        logging.info("create categroy _id %r", _id)
        categroy = {"_id":_id, "vendor_id":vendor_id,
                "title":title, "desc":desc ,"bk_img_url":bk_img_url}
        category_dao.category_dao().create(categroy);

        self.redirect('/vendors/' + vendor_id + '/categorys')


# /vendors/<string:vendor_id>/categorys/<string:category_id>/edit
class VendorCategoryEditHandler(AuthorizationHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id, category_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got category_id %r in uri", category_id)

        ops = self.get_ops_info()

        category = category_dao.category_dao().query(category_id)
        counter = self.get_counter(vendor_id)
        self.render('vendor/category-edit.html',
                vendor_id=vendor_id,
                ops=ops,
                counter=counter,
                category=category)

    @tornado.web.authenticated  # if no session, redirect to login page
    def post(self, vendor_id, category_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got category_id %r in uri", category_id)

        ops = self.get_ops_info()

        title = self.get_argument("title", "")
        desc = self.get_argument("desc", "")
        bk_img_url = self.get_argument("bk_img_url", "")
        logging.debug("got param title %r", title)
        logging.debug("got param desc %r", desc)
        logging.debug("got param bk_img_url %r", bk_img_url)

        categroy = {"_id":category_id, "title":title, "desc":desc ,"bk_img_url":bk_img_url}
        category_dao.category_dao().update(categroy);

        self.redirect('/vendors/' + vendor_id + '/categorys')

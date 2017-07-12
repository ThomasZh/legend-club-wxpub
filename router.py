# _*_ coding: utf-8_*_
#
# genral application route config:
# simplify the router config by dinamic load class
# by lwz7512
# @2016/05/17

import tornado.web

from foo import comm
from foo.auth import auth_email
from foo.auth import auth_phone
from foo.auth import auth_wx
from wx import wx_activity
from wx import wx_items
from wx import wx_resale
from wx import wx_voucher
from wx import wx_triprouter
from wx import wx_personal_center
from wx import wx_vendor
from wx import wx_wrap
from wx import wx_order
from wx import xml_parser
from api import api_category
from api import api_activity
from api import api_items
from api import api_blog
from api import api_setup
from api import api_customer_profile
from api import api_order
from foo.portal import eshop


def map():

    config = [

        # authenticated
        (r'/bf/wxpub/auth/login', getattr(auth_wx, 'AuthWxLoginHandler')),
        (r'/bf/wxpub/auth/login/step2', getattr(auth_wx, 'AuthWxLoginStep2Handler')),


        # bike-forever ajax handler result
        (r"/bf/api/vendors/([a-z0-9]*)/categorys", getattr(api_category, 'ApiCategoryListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/popular", getattr(api_activity, 'ApiActivityPopularListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/completed", getattr(api_activity, 'ApiActivityCompletedListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)", getattr(api_activity, 'ApiActivityInfoXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)/members", getattr(api_activity, 'ApiActivityMemberListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)/share", getattr(api_activity, 'ApiActivityShareXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/articles/([a-z0-9]*)/paragraphs", getattr(api_blog, 'ApiBlogParagraphListXHR')),

        # 受欢迎的商品列表
        (r"/bf/api/vendors/([a-z0-9]*)/items/popular", getattr(api_items, 'ApiItemsPopularListXHR')),

        (r"/bf/api/vendors/([a-z0-9]*)/orders", getattr(api_order, 'ApiOrdersXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/orders/activitys/([a-z0-9]*)", getattr(api_order, 'ApiActivityOrdersXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/orders/([a-z0-9]*)", getattr(api_order, 'ApiOrderInfoXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/orders/([a-z0-9]*)/review", getattr(api_order, 'ApiOrderReviewXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/orders/([a-z0-9]*)/delete", getattr(api_order, 'ApiOrderDeleteXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/order/search", getattr(api_order, 'ApiOrderSearchXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/voucher-orders", getattr(api_order, 'ApiVoucherOrderListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/voucher-orders/([a-z0-9]*)/review", getattr(api_order, 'ApiVoucherOrderReviewXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/apply/search", getattr(api_order, 'ApiApplySearchXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/applys", getattr(api_order, 'ApiApplyListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/applys/([a-z0-9]*)/review", getattr(api_order, 'ApiApplyReviewXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)/applys/export", getattr(api_order, 'ApiActivityExportXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/insurance-templates", getattr(api_setup, 'ApiSetupInsuranceTemplateListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/customer-profile/vouchers", getattr(api_customer_profile, 'ApiCustomerProfileVoucherListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/customer-profile/my", getattr(api_customer_profile, 'ApiCustomerProfileMyInfoXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/customer-profile/contacts", getattr(api_customer_profile, 'ApiCustomerProfileMyContactListXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/customers/([a-z0-9]*)/orders", getattr(api_customer_profile, 'ApiCustomerOrdersXHR')),
        (r"/bf/api/vendors/([a-z0-9]*)/customer-profile/customers", getattr(api_customer_profile, 'ApiCustomerListXHR')),


        # 俱乐部首页
        (r"/bf/wx/vendors/([a-z0-9]*)/info", getattr(wx_vendor, 'WxVendorInfoHandler')),
        # 俱乐部管理员绑定微信
        (r"/bf/wx/vendors/([a-z0-9]*)/ops/([a-z0-9]*)/binding", getattr(wx_vendor, 'WxVendorBindingHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/ops/([a-z0-9]*)/binding/step1", getattr(wx_vendor, 'WxVendorBindingStep1Handler')),
        # 联盟管理员绑定微信
        (r"/bf/wx/leagues/([a-z0-9]*)/administrators/([a-z0-9]*)/binding", getattr(wx_vendor, 'WxLeagueBindingHandler')),
        (r"/bf/wx/leagues/([a-z0-9]*)/administrators/([a-z0-9]*)/binding/step1", getattr(wx_vendor, 'WxLeagueBindingStep1Handler')),
        # 分销商发起提现申请
        (r"/bf/wx/vendors/([a-z0-9]*)/ops/([a-z0-9]*)/apply-cash-out/suppliers/([a-z0-9]*)", getattr(wx_vendor, 'WxVendorResellerApplyCashoutHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/ops/([a-z0-9]*)/apply-cash-out/suppliers/([a-z0-9]*)/step1", getattr(wx_vendor, 'WxVendorResellerApplyCashoutStep1Handler')),
        # 查看提现申请详情
        (r"/bf/wx/vendors/([a-z0-9]*)/apply-cashout/([a-z0-9]*)", getattr(wx_vendor, 'WxVendorApplyCashoutInfoHandler')),
        # 查看积分变化详情
        (r"/bf/wx/vendors/([a-z0-9]*)/bonus-points/([a-z0-9]*)", getattr(wx_vendor, 'WxVendorBonusPointChangedHandler')),
        # 订单详细信息
        (r"/bf/wx/vendors/([a-z0-9]*)/orders/([a-z0-9]*)", getattr(wx_order, 'WxVendorOrderInfoHandler')),


        # 推荐活动列表
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/recommend", getattr(wx_resale, 'WxResaleActivityIndexHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)_([a-z0-9]*)", getattr(wx_resale, 'WxResaleActivityInfoHandler')),
        # 分销商5个页面
        (r"/bf/wx/vendors/([a-z0-9]*)/supplier-list", getattr(wx_resale, 'WxResaleSupplerListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/supplier", getattr(wx_resale, 'WxResaleSupplerHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/goods-detail/([a-z0-9]*)", getattr(wx_resale, 'WxResaleGoodsDetailHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/register-distributor", getattr(wx_resale, 'WxResaleRegisterDistributorHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/distributor-personal/([a-z0-9]*)", getattr(wx_resale, 'WxResaleDistributorPersonalHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/distributor/([a-z0-9]*)/goods-share/([a-z0-9]*)", getattr(wx_resale, 'WxResaleGoodsShareHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/distributor/([a-z0-9]*)/checkout/([a-z0-9]*)", getattr(wx_resale, 'WxResaleGoodsCheckoutHandler')),


        # bike-forever wexin activity
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys", getattr(wx_activity, 'WxActivityListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/history", getattr(wx_activity, 'WxActivityHistoryListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)", getattr(wx_activity, 'WxActivityInfoHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)/qrcode", getattr(wx_activity, 'WxActivityQrcodeHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)_([a-z0-9]*)/apply/step0", getattr(wx_activity, 'WxActivityApplyStep0Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)_([a-z0-9]*)/apply/step1", getattr(wx_activity, 'WxActivityApplyStep1Handler')),
        (r"/bf/wxpay", getattr(wx_activity, 'WxActivityApplyStep2Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/activitys/([a-z0-9]*)/apply/step3", getattr(wx_activity, 'WxActivityApplyStep3Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/hha", getattr(wx_activity, 'WxHhaHandler')),


        # items wexin
        (r"/bf/wx/vendors/([a-z0-9]*)/items", getattr(wx_items, 'WxItemsListHandler')),
        # cart
        (r"/bf/wx/vendors/([a-z0-9]*)/items/cart", getattr(wx_items, 'WxItemsCartHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/items/submit/order", getattr(wx_items, 'WxItemsSubmitOrderHandler')),

        (r"/bf/wx/vendors/([a-z0-9]*)/items/myorders", getattr(wx_items, 'WxItemsMyordersHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/items/([a-z0-9]*)", getattr(wx_items, 'WxItemsDetailHandler')),
        # 点击结算按钮
        (r"/bf/wxpay/items", getattr(wx_items, 'WxItemsOrderCheckoutHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/items/order/([a-z0-9]*)/result", getattr(wx_items, 'WxItemsOrderResultHandler')),

        # 开放线路市场
        (r"/bf/wx/vendors/([a-z0-9]*)/triprouters", getattr(wx_triprouter, 'WxTriprouterMarketHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/triprouters/([a-z0-9]*)", getattr(wx_triprouter, 'WxTriprouterInfoHandler')),


        # 由俱乐部分享出的有偿代金券
        (r"/bf/wx/vendors/([a-z0-9]*)/vouchers/([a-z0-9]*)", getattr(wx_voucher, 'WxVoucherShareHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/vouchers/([a-z0-9]*)/buy/step0", getattr(wx_voucher, 'WxVoucherBuyStep0Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/vouchers/([a-z0-9]*)/buy/step1", getattr(wx_voucher, 'WxVoucherBuyStep1Handler')),
        (r"/bf/voucher-pay", getattr(wx_voucher, 'WxVoucherBuyStep2Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/vouchers/([a-z0-9]*)/buy/step3", getattr(wx_voucher, 'WxVoucherBuyStep3Handler')),


        # bike-forever wexin order
        # 微信支付结果通用通知
        # 该链接是通过【统一下单API】中提交的参数notify_url设置，如果链接无法访问，商户将无法接收到微信通知。
        # 通知url必须为直接可访问的url，不能携带参数。示例：notify_url：“https://pay.weixin.qq.com/wxpay/pay.action”
        (r"/bf/wx/orders/notify", getattr(wx_activity, 'WxOrderNotifyHandler')),
        (r"/bf/wx/voucher-orders/notify", getattr(wx_voucher, 'WxVoucherOrderNotifyHandler')),
        (r"/bf/wx/orders/wait", getattr(wx_activity, 'WxOrderWaitHandler')),


        # bike-forever wexin personal-center
        (r"/bf/wx/vendors/([a-z0-9]*)/pc0", getattr(wx_personal_center, 'WxPersonalCenterStep0Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc1", getattr(wx_personal_center, 'WxPersonalCenter1Handler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc", getattr(wx_personal_center, 'WxPersonalCenterHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/orders", getattr(wx_personal_center, 'WxPcOrderListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/orders/([a-z0-9]*)", getattr(wx_personal_center, 'WxPcOrderInfoHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/orders/([a-z0-9]*)/applys", getattr(wx_personal_center, 'WxPcOrderApplyListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/orders/([a-z0-9]*)/evaluate", getattr(wx_personal_center, 'WxPcOrderEvaluateHandler')),
        (r"/bf/wxrepay", getattr(wx_personal_center, 'WxPcOrderRepayHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/vouchers", getattr(wx_personal_center, 'WxPcVoucherListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/bonus", getattr(wx_personal_center, 'WxPcBonusListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/certs", getattr(wx_personal_center, 'WxPcCertListHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/certs/([a-z0-9]*)", getattr(wx_personal_center, 'WxPcCertInfoHandler')),
        (r"/bf/wx/vendors/([a-z0-9]*)/pc/tasks", getattr(wx_personal_center, 'WxPcTaskListHandler')),


        (r'/webapp', getattr(eshop, 'EshopHomeHandler')),
        (r'/webapp/eshop', getattr(eshop, 'EshopHomeHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)', getattr(eshop, 'EshopIndexHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)/articles/([a-z0-9]*)', getattr(eshop, 'EshopArticleHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)/articles/([a-z0-9]*)/add-comment', getattr(eshop, 'EshopArticleAddCommentHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)/products/([a-z0-9]*)', getattr(eshop, 'EshopProductHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)/products/([a-z0-9]*)/place-order', getattr(eshop, 'EshopProductPlaceOrderHandler')),
        (r'/webapp/eshop/clubs/([a-z0-9]*)/products/([a-z0-9]*)/place-order-success', getattr(eshop, 'EshopProductPlaceOrderSuccessHandler')),


        (r"/MP_verify_rZAV6WH7J2WhqAIs.txt", getattr(comm, 'WxMpVerifyHandler')),
        (r"/MP_verify_UwBwsF7uHi57Xd6e.txt", getattr(comm, 'WxMpVerify2Handler')),
        (r'/MP_verify_qdkkOWgyqqLTrijx.txt', getattr(comm, 'WxMpVerify3Handler')),
        (r'/MP_verify_5ADJKiXMdg0ycJjx.txt', getattr(comm, 'WxMpVerify4Handler')),

        # comm
        ('.*', getattr(comm, 'PageNotFoundHandler'))

    ]

    return config

// @2017/07/05
$(function(){

      var api_domain = $("#api_domain").val();
      var access_token = $("#access_token").val();
      var club_id = $("#club_id").val();
      function getCartPro(pageNum) {
          var limit = 20;//初始化值
          $.ajax({
            type: "GET",
            url: api_domain+"/api/clubs/"+ club_id +"/cart/items?page="+pageNum+"&limit="+limit,
            headers: {"Authorization": "Bearer "+ access_token +""},
            contentType: 'application/json',
            success: function(data, status, xhr) {

                  data_obj = JSON.parse(data);
                  data = data_obj.rs;
              var pageData = data.data;
              var inner_html = "";
              // console.log(pageData);
              if(pageData.length == 0){
                  inner_html += '<div class="empty">';
                  inner_html += '<div class="empty-cart">';
                  inner_html += '<h4>购物车空空如也</h4>';
                  inner_html += '<a href="/bf/wx/vendors/'+ club_id +'/items" class="shop-btn">去抢购</a>';
                  inner_html += '</div></div>';
              }else{
                  for (var i in pageData) {
                      inner_html += '<li class="collection-item avatar list-item-info">';
                      inner_html += '<img src="'+pageData[i].img+'" alt="" class="circle">';
                      inner_html += '<span class="title">'+pageData[i].title+'</span>';
                      inner_html += '<p>'+pageData[i].fee_template_name+'</p>';
                      inner_html += '<div class="hilight flex-separate">';
                      inner_html += '<input type="hidden" value="'+ pageData[i].fee_template_id +'" class="fee_template">';
                      inner_html += '<span class="one-price">'+pageData[i].fee/100+'元/桶</span>';
                      inner_html += '<div class="qunatity">';
                      inner_html += '<a href="#!" class="counter del" data_dele_id="'+pageData[i]._id+'" data_pro_id="'+pageData[i].item_id+'"><i class="ion-minus-circled"></i></a>';
                      inner_html += '<span class="one-quantity">'+pageData[i].quantity+'</span>';
                      inner_html += '<a href="#!" class="counter add" data_dele_id="'+pageData[i]._id+'"><i class="ion-plus-circled"></i></a>';
                      inner_html += '</div></div>';
                      inner_html += '<a href="javascript:;" class="close cart-info-delete" data_dele_id="'+pageData[i]._id+'">';
                      inner_html += '<i class="iconfont icon-close ion-ios-close-empty"></i>';
                      inner_html += '</a>';
                      inner_html += '</li>';
                    };
                }
                $('#list-item').append(inner_html);
                // 减数量
                $(document).on("click",".del",function(){
                  var num = $(this).next().text();
                    if(num < 2){
                      num = 1;
                      $(this).next().text(num);
                    }else{
                      num--;
                      var _id = $(this).attr("data_dele_id");
                      // console.log(_id);
                      var data = {"quantity":num}
                      var  _json = JSON.stringify(data);
                      var _this = $(this);
                      $.ajax({
                        type: "POST",
                        url: api_domain+"/api/clubs/"+ club_id +"/cart/items/"+_id,
                        data:_json,
                        headers: {"Authorization": "Bearer "+ access_token +""},
                        contentType: 'application/json',
                        success: function(data, status, xhr) {
                          var data = JSON.parse(data);
                          var quantity = data.data.quantity;
                          _this.next().text(quantity);
                          getTotal();
                        }
                      });
                    }
                });
                // add product_num
                $(document).on("click",".add",function(){
                  var num = $(this).prev().text();
                      num++;
                  var _id = $(this).attr("data_dele_id");

                  var  data = {"quantity":num}
                  var  _json = JSON.stringify(data);
                    // console.log(_json);
                    var _this = $(this);
                    $.ajax({
                      type: "POST",
                      url: api_domain+"/api/clubs/"+ club_id +"/cart/items/"+_id,
                      data:_json,
                      headers: {
                        "Authorization": "Bearer "+ access_token +""
                      },
                      contentType: 'application/json',
                      success: function(data, status, xhr) {
                        // console.log(data);
                        var data = JSON.parse(data);
                        var quantity = data.data.quantity;
                        _this.prev().text(quantity);
                        getTotal();
                      }
                    });

                });
                // blur input save
                $(document).on("blur",".J_input",function(){
                    var _id = $(this).next().attr("data_dele_id");
                    var _this = $(this);
                    var num = $(this).val();
                    var data = {"quantity":num}
                    var _json = JSON.stringify(data);
                    $.ajax({
                      type: "POST",
                      url: api_domain+"/api/clubs/"+ club_id +"/cart/items/"+_id,
                      data:_json,
                      headers: {
                        "Authorization": "Bearer "+ access_token +""
                      },
                      contentType: 'application/json',
                      success: function(data, status, xhr) {
                        // console.log(data);
                        var data = JSON.parse(data);
                        var quantity = data.data.quantity;
                        _this.prev().val(quantity);
                        getTotal();
                      }
                    });
                });
                // watch input change
                $(document).on("input",".J_input",function(){
                    getTotal();
                });
                // 计算总金额
                function getTotal(){
                  var num = $(".list-item-info").length;
                  var total_price=0;
                  for(var i=0;i<num;i++){
                    var one_price = $(".list-item-info").eq(i).find(".one-price").text();
                    // console.log(one_price);
                    var quantity = $(".list-item-info").eq(i).find(".one-quantity").text();
                    // console.log(quantity);
                    var one_total = parseFloat(one_price)*quantity;
                        total_price += parseFloat(one_total);
                  }
                    // $(".footer-total-price").children().html(total_price.toFixed(2));
                    $("#footer-bar span").text(total_price.toFixed(2));
                    $("#total_amount").val(total_price.toFixed(2));
                };
                getTotal();

                // 组织json数据
                function get_json(){
                  var items = [];
                  $('.list-item-info').each(function(index) {
                    var item_id = $(".del",$(this)).attr("data_pro_id");
                    var fee_template_id =  $(".fee_template",$(this)).val();
                    var quantity = $(".one-quantity",$(this)).text();
                    obj =  {"item_id":item_id,"fee_template_id":fee_template_id,"quantity":quantity};
                    items.push(obj);
                   });
                   console.log(items);
                   var cart_arr = JSON.stringify(get_json(items));
                   console.log(cart_arr);
                   $("#item_input").val(cart_arr);
                };
                get_json();

                // 删除购物车一项
                $(document).on('click','.cart-info-delete',function(){
                  var _id = $(this).attr('data_dele_id');
                  var _this = $(this);
                  $.confirm("确定删除该商品吗?", function() {
                      $.ajax({
                        type: "DELETE",
                        url: api_domain+"/api/clubs/"+ club_id +"/cart/items/"+_id,
                        headers: {"Authorization": "Bearer "+ access_token +""},
                        contentType: 'application/json',
                        success: function(data, status, xhr) {
                          _this.parent().remove();
                          $.alert(get_json().length);
                          // if(get_json().length == 0){
                          //   location.href="/bf/wx/vendors/"+ club_id +"/items/checkout/cart";
                          // }
                          get_json();
                          getTotal();
                        }
                      });
                    }, function() {
                    //点击取消后的回调函数
                    });
                });

                // 下单操作
                $("#open-right").on('click',function(event){
                  $.alert(get_json().length);
                  if(get_json().length == 0){
                     event.preventDefault();
                  }else{
                    $(".order-form").submit();
                  }

                });

              }
            })
      };
      getCartPro('1');

});

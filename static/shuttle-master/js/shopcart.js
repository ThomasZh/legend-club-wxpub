// @2017/07/05
$(function(){
      getCartPro();
      var limit = 20;//初始化值
      var api_domain = $("#api_domain").val();
      var access_token = $("#access_token").val();
      var club_id = $("#club_id").val();
      function getCartPro(pageNum) {
          $.ajax({
            type: "GET",
            url: api_domain+"/api/clubs/"+ club_id +"/cart/items?page="+pageNum+"&limit="+limit,
            headers: {"Authorization": "Bearer "+ access_token +""},
            contentType: 'application/json',
            success: function(data, status, xhr) {
                  console.log(data);
                  data_obj = JSON.parse(data);
                  data = data_obj.rs;
              var pageData = data.data;
              for (var i in pageData) {
                  var inner_html = '<li class="collection-item avatar">';
                      inner_html += '<img src="'+pageData[i].img+'" alt="" class="circle">';
                      inner_html += '<span class="title">'+pageData[i].item_id+'</span>';
                      inner_html += '<p>'+pageData[i].title+'</p>';
                      inner_html += '<div class="hilight flex-separate">';
                      inner_html += '<span>'+pageData[i].item_id+'元/桶</span>';
                      inner_html += '<div class="qunatity">';
                      inner_html += '<a href="#!" class="counter" data_dele_id="'+pageData[i].item_id+'" data_pro_id="'+pageData[i].item_id+'"><i class="ion-minus-circled"></i></a>';
                      inner_html += '<span>'+pageData[i].item_id+'</span>';
                      inner_html += '<a href="#!" class="counter" data_dele_id="'+pageData[i].item_id+'"><i class="ion-plus-circled"></i></a>';
                      inner_html += '</div></div></li>';
                      $('#list-item').append(inner_html);
                };
              }
            })
      };

    // 减产品数量
    $(document).on("click",".J_Del",function(){
      var num = $(this).next().val();
        if(num < 2){
          num = 1;
          $(this).next().val(num);
        }else{
          num--;
          var _id = $(this).attr("data_dele_id");
          // console.log(_id);
          var data = {"quantity":num}
          var  _json = JSON.stringify(data);
          var _this = $(this);
          $.ajax({
            type: "POST",
            url: "{{api_domain}}/api/clubs/{{club_id}}/cart/items/"+_id,
            data:_json,
            headers: {
              "Authorization": "Bearer {{ access_token }}"
            },
            contentType: 'application/json',
            success: function(data, status, xhr) {
              var data = JSON.parse(data);
              var quantity = data.data.quantity;
              _this.next().val(quantity);
              getTotal();
            }
          });
        }
    });
    // add product_num
    $(document).on("click",".J_Add",function(){
      var num = $(this).prev().val();
          num++;
      var _id = $(this).attr("data_dele_id");

      var  data = {"quantity":num}
      var  _json = JSON.stringify(data);
        // console.log(_json);
        var _this = $(this);
        $.ajax({
          type: "POST",
          url: "{{api_domain}}/api/clubs/{{club_id}}/cart/items/"+_id,
          data:_json,
          headers: {
            "Authorization": "Bearer {{ access_token }}"
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
    // blur input save
    $(document).on("blur",".J_input",function(){
        var _id = $(this).next().attr("data_dele_id");
        var _this = $(this);
        var num = $(this).val();
        var data = {"quantity":num}
        var _json = JSON.stringify(data);
        $.ajax({
          type: "POST",
          url: "{{api_domain}}/api/clubs/{{club_id}}/cart/items/"+_id,
          data:_json,
          headers: {
            "Authorization": "Bearer {{ access_token }}"
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
        var one_price = $(".list-item-info").eq(i).find(".original-price").html();
        var quantity = $(".list-item-info").eq(i).find(".J_input").val();
        var one_total = one_price*quantity;
            total_price += parseFloat(one_total);
      }
        $(".footer-total-price").children().html(total_price.toFixed(2));
        $("#total_amount").val(total_price.toFixed(2));
    };
    getTotal();

    // 删除购物车一项
    $(document).on('click','.cart-info-delete',function(){
      var _id = $(this).attr('data_dele_id');
      $.confirm("确定删除该商品吗?", function() {
          $.ajax({
            type: "DELETE",
            url: "{{api_domain}}/api/clubs/{{club_id}}/cart/items/"+_id,
            headers: {
              "Authorization": "Bearer {{ access_token }}"
            },
            contentType: 'application/json',
            success: function(data, status, xhr) {
              location.reload();
            }
          });
        }, function() {
        //点击取消后的回调函数
        });
    });

    // 组织json数据
    var items = [];
    $('.list-item-info').each(function(index) {
      var item_id = $(".J_Del",$(this)).attr("data_pro_id");
      var fee_template_id =  $(".fee_template",$(this)).val();
      var quantity = $(".J_input",$(this)).val();
      obj =  {"item_id":item_id,"fee_template_id":fee_template_id,"quantity":quantity};
      items.push(obj);
     });
    //  console.log(items);
     $("#item_input").val(JSON.stringify(items));

     // 收货地址
     var address = {};
     var name = $("#name").val();
     var phone = $("#phone").val();
     var addr = $("#address").val();
         address = {"name":name,"phone":phone,"addr":addr};
    $("#addr_input").val(JSON.stringify(address));

    // 下单操作
    $("#en-order").on('click',function(event){
      if(items == ""){
         event.preventDefault();
      }else{
        $(".order-form").submit();
      }

    });

});

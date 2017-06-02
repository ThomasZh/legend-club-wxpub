// 分销商列表 @2017/05/23
$(function(){
  console.log('to fetch distributor list...');

  $('.todo-element').click(function(e){
    console.log('todo element clicked!');

    console.log($(this));
    console.log($(this).data('id'));
    location.href = '/bf/wx/vendors/([a-z0-9]*)/supplier?s=' + $(this).data('id');
  });


});

// 分销商列表 @2017/05/23
$(function(){
  console.log('to fetch distributor list...');

  $('.todo-element').click(function(e){
    console.log('todo element clicked!');

    console.log($(this));
    console.log($(this).data('id'));
    location.href = 'supplier.html?s=' + $(this).data('id');
  });


});

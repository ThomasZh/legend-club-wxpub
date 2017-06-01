// 商品页面
$(function(){

  // Sliders
  var swiper = new Swiper('.swiper-slider', { // Default
      pagination: '.swiper-pagination',
      paginationClickable: true,
      nextButton: '.swiper-button-next',
      prevButton: '.swiper-button-prev',
      autoplay: false,
      loop: true,
      paginationType: 'progress',
  });

  // Tabs
  $('ul.tabs').tabs();


});

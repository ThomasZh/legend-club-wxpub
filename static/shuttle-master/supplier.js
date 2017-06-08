$(function () {

  // Tabs
  $('ul.tabs').tabs();

  // Masonry
  // $('.grid').masonry({
  //     itemSelector: '.grid-item'
  // });

  // Reinitialize masonry inside each panel after the relative tab link is clicked -
  $('.tab a').on('click', function() {
    // do async to allow menu to open
    // setTimeout( function() {
    //    $('.grid').masonry({
    //   itemSelector: '.grid-item'
    // }, 1);
    // });
  });


});

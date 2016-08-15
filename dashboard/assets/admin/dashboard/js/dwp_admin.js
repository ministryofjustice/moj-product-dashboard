    $(document).ready(function () {
      // Get the URL
      var url = window.location.href.split('/').pop();

      if (url === '') {
        url = '/';
      }

      // Check the href of each link in the sidebar
      $('.admin-sidebar-content a').each(function () {
        if (url === $(this).attr('href')) {
          // If the href matches the current URL set it as active
          $(this).parents('li').addClass('active');
        }
      });
    });
    //
    // // Tab Panes
    // $('.admin-panes').each(function() {
    //   $(this).children('div').hide();
    //   $(this).children('.admin-pane:first').show();
    //   $(this).parent().find('li:first').addClass('active');
    //   $(this).parents('.admin-submenu-container').find('h1').text($('.active').find('a').text());
    // });
    //
    // $(document).on('click', '.admin-submenu a', function(e) {
    //   e.preventDefault();
    //
    //   var nth = $(this).parent().index() + 1;
    //   var target = $(this).parents('.admin-submenu-container').find('.admin-pane:nth-child(' + nth + ')');
    //
    //   $(this).parents('.admin-submenu-container').find('.active').removeClass('active');
    //   $(this).parent().addClass('active');
    //
    //   $(this).parents('.admin-submenu-container').find('.admin-panes').children().hide();
    //   $(this).parents('.admin-submenu-container').find('h1').text($(this).text());
    //   target.show();
    // });

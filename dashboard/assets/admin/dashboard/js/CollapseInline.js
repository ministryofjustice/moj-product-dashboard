(function($) {
  $(document).ready(function() {
    $('div.inline-group div.inline-related fieldset.module h2').on('click', function (e) {
      $(this).toggleClass('expand');
      $(this).next('table').toggleClass('hidden');
    });
  });
})(django.jQuery);

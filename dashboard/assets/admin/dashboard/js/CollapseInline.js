/**
 * CollapseInline will detect and auto collapse django Admin Inline forms if
 * there  are more than 3 forms per inline. It will add a clickable tr to
 * collapse/expand the forms
 *
 */

(function($) {
  var SHOW_REMAINING = 3;
  var EXPAND_TEXT = '+++ Expand +++';
  var COLLAPSE_TEXT = '--- Collapse ---';

  $(document).ready(function() {
    $('div.inline-group div.inline-related fieldset.module table tbody').each(function (index) {
      var $tbody = $(this);
      var $trs = $tbody.find('tr').not('.add-row').not('.empty-form');
      if ($trs.length > SHOW_REMAINING) {
        var colspan = $trs.first().children('td').length;
        var $expandTr = $('<tr class="toggle-collapsed-inlines collapsed" />');
        var $expandTd = $('<td colspan="' + colspan + '" />');
        $expandTr.append($expandTd);
        $tbody.prepend($expandTr);

        function toggleRows ($rows) {
          $rows.each(function (i) {
            if ($rows.length - i - SHOW_REMAINING > 0) {
              $(this).toggleClass('hidden');
            }
          });
          if ($expandTd.text() == EXPAND_TEXT) {
            $expandTd.text(COLLAPSE_TEXT);
          } else {
            $expandTd.text(EXPAND_TEXT);
          }
        }

        toggleRows($trs);

        $expandTd.on('click', function (e) {
          toggleRows($trs);
        });
      }
    });
  });
})(django.jQuery);

(function () {
  'use strict';

  var readonlyElements = document.getElementsByClassName('js-remove-readonly-onfocus');

  for (var i = 0; i < readonlyElements.length; i += 1) {
    readonlyElements[i].onfocus = function () {
      this.removeAttribute('readonly');
    };
  }
})();

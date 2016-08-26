'use strict';

window.dashboard = window.dashboard || {};

window.dashboard.fileUpload = {
  init: function() {
    var self = this;

    Dropzone.autoDiscover = false;

    if($('#dropzone-box').length) {
      self.setup($('#dropzone-box'));
    }
  },

  setup: function($el) {
    var self = this;

    $el.dropzone({
      url: '.',
      autoProcessQueue: false,
      uploadMultiple: true,
      maxFiles: 1,
      clickable: '.dz-clickable',
      acceptedFiles: '.xls',
      paramName: 'payroll_file',
      previewTemplate: document.getElementById('preview-template').innerHTML,
      headers: { 'X-CSRF-Token' : $('input[name="csrfmiddlewaretoken"]').val() },

      forceFallback: false
    });

    self.bindEvents($el);
  },

  bindEvents: function($el) {
    var self = this;

    $el.find('button').on('click', function(e) {
      e.preventDefault();
    });

    $(document).on('click', '.js-remove-button', function(e) {
      e.preventDefault();
      Dropzone.forElement('#dropzone-box').removeAllFiles();
      self.enableDropzone();
    });
    $el.on('dragenter', function(e) {
      $('#dropzone-box').addClass('over');
    });
    $el.on('dragend', function(e) {
      $('#dropzone-box').removeClass('over');
    });

    $('#dropzone-box').attrchange({
      trackValues: true,
      callback: function(e) {
        if(e.attributeName === 'class') {
          if(e.newValue.search(/dz-max-files-reached/i) == -1) {
            self.enableDropzone();
          } else {
            self.disableDropzone();
          }
        }
      }
    });

    $el.closest('form').on('submit', function(e) {
      e.preventDefault();
      var dz = Dropzone.forElement('#dropzone-box');
      dz.options.params = {
        csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
        date_month: $('#id_date_month option:selected').val(),
        date_year: $('#id_date_year option:selected').val()
      };
      dz.processQueue();
    });
  },

  enableDropzone: function() {
    $('#dropzone-box').removeClass('over').removeClass('dropped');
    $('.dropzone-message').show();
  },

  disableDropzone: function() {
    $('#dropzone-box').removeClass('over').addClass('dropped');
    $('.dropzone-message').hide();
  }
};


$(function() {
  window.dashboard.fileUpload.init();
});

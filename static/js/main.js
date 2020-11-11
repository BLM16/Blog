// When document is loaded
$(document).ready(function() {

    // Expand textarea with text
    $('#about').on('keyup keypress', function() {
      $(this).height(0);
      $(this).height(this.scrollHeight);
    });
    $('#about').trigger('keypress')

});
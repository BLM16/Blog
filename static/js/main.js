// When document is loaded
$(document).ready(function() {

    // Expand textarea with text
    $('.textarea-expand').on('keyup keypress', function() {
        rows = $(this).attr('rows');

        if (rows) {

        } else {
            $(this).height(0);
            $(this).height(this.scrollHeight);
        }
    });
    $('.textarea-expand').trigger('keypress')

});
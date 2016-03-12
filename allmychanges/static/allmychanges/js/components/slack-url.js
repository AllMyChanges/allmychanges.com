var create_url_checker = require('./check-url.js');


var check_callback = (url, set_state) => {
        $.ajax({
            url: '/account/settings/test-slack/?url=' + url,
            method: 'POST',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: () => {
                set_state({sending: false,
                           error: null});
            },
            error: (xhr, status, err) => {
                set_state({sending: false,
                           error: 'Unable to send message'});
                console.error('Unable test url', status, err.toString());
            }
        });
}

module.exports = create_url_checker('slack_url', check_callback);

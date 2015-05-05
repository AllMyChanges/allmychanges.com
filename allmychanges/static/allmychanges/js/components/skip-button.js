var metrika = require('./metrika.js')

module.exports = React.createClass({
    perform_action: function(action) {
        // performing action [action] @buttons.skip
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                metrika.reach_goal(action.toUpperCase());

                if (this.props.on_skip !== undefined) {
                    this.props.on_skip();
                }
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to perform action ' + action + ' on changelog', status, err.toString());
            }.bind(this)
        });
    },
    skip: function (e) {
        e.preventDefault();
        this.perform_action('skip', true);
    },
    handle_popup_click: function (e) {
        // popup click @buttons.report
        e.nativeEvent.stopImmediatePropagation();
    },
    render: function() {
        return (<div className="skip-button">
                    <button className="button"
                            onClick={this.skip}
                            title="Click me to show next package.">Show next</button>
                </div>);
    }
});

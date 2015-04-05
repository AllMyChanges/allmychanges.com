var metrika = require('./metrika.js')

module.exports = React.createClass({
    getInitialState: function () {
        return {tracked: (this.props.tracked == 'true')};
    },
    perform_action: function(action, state_after) {
        // performing action [action] @buttons.track
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                this.setState({tracked: state_after});
                metrika.reach_goal(action.toUpperCase());
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to perform action ' + action + ' on changelog', status, err.toString());
            }.bind(this)
        });
    },
    track: function (e) {
        e.preventDefault();
        this.perform_action('track', true);
    },
    untrack: function (e) {
        e.preventDefault();
        this.perform_action('untrack', false);
    },
    render: function() {
        var num_trackers = this.props.num_trackers;

        var msg;
        if (num_trackers && num_trackers != '0') {
            msg = num_trackers + ' users already track it!'
            if (num_trackers == '1') {
                msg = 'one user already tracks it!';
            }
        } else {
            msg = 'nobody tracks it, be the first!';
        }
        var trackers_msg = <div className="track-button__message">{msg}</div>;

        if (this.state.tracked) {
            return (<div className="track-button">
                      <button className="button _bad"
                              onClick={this.untrack}
                              title="Click to unsubscribe from this package.">Untrack</button>
                    </div>);
        } else {
            return (<div className="track-button">
                      <button className="button _good"
                              onClick={this.track}
                              title="Click to receive notifications about new versions.">Track it!</button>
                      {trackers_msg}
                    </div>);
        }
    }
});

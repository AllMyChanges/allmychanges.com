module.exports = React.createClass({
    getInitialState: function () {
        console.log('this.props=', this.props);
        return {tracked: (this.props.tracked == 'true')};
    },
    perform_action: function(action, state_after) {
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                console.log('Setting state to ', state_after);
                this.setState({tracked: state_after});
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
        if (this.state.tracked) {
            return (<button className="button _bad"
                            onClick={this.untrack}
                            title="Click to unsubscribe from this package.">Untrack</button>);
        } else {
            return (<button className="button _good"
                            onClick={this.track}
                            title="Click to receive notifications about new versions.">Track it!</button>);
        }
    }
});

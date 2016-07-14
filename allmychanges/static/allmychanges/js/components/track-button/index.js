var React = require('react');
var metrika = require('../metrika.js');
var css = require('./index.styl');

module.exports = React.createClass({
    getInitialState: function () {
        // init track button for [this.props.username] @buttons.track
        return {tracked: (this.props.tracked == 'true'),
                show_popup: false};
    },
    perform_action: function(action, state_after) {
        // performing action [action] @buttons.track
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/' + action + '/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                metrika.reach_goal(action.toUpperCase());

                if (this.props.on_track !== undefined) {
                    this.props.on_track();
                }

                this.setState({tracked: state_after});

                if (this.props.username == '') {
                    // if user is anonymous, then show him a fullscreen popup @buttons.track
                    this.setState({show_popup: true});
                }
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
    handle_popup_click: function (e) {
        // popup click @buttons.report
        e.nativeEvent.stopImmediatePropagation();
    },
    render: function() {
        var popup;

        if (this.state.show_popup) {
            popup = (
                <div className="modal-popup" onClick={this.handle_popup_click}>
                    <div className="modal-popup__content modal-popup__please-login">
                      <p>Good job! You have made the first step, tracking this package.</p>
                      <p>Now, to receive notifications about it\'s future releases, you need to create account by signing in using:</p>
                      <p><a className="button _good _large" href="/login/twitter/"><i className="fa fa-twitter fa-lg"></i> Twitter</a> or <a className="button _good _large" href="/login/github/"><i className="fa fa-github fa-lg"></i> GitHub</a></p>
                    </div>
                </div>);
        }


        if (this.state.tracked) {
            return (<div className="track-button">
                      <button className="button"
                              onClick={this.untrack}
                              title="Click to unsubscribe from this package.">Unfollow</button>
                      {popup}
                    </div>);
        } else {
            return (<div className="track-button">
                      <button className="button _good"
                              onClick={this.track}
                              title="Click to receive notifications about new versions.">Follow</button>
                    </div>);
        }
    }
});

var React = require('react');
var metrika = require('../metrika.js');
var css = require('./index.styl');

module.exports = React.createClass({
    getInitialState: function () {
        // init moderate button for [this.props.username] @buttons.moderate
        return {
            moderated: (this.props.moderated == 'true'),
            show_popup: false
        }
    },
    perform_action: function(action, state_after) {
        // performing action [action] @buttons.moderate
        $.ajax({
            url: '/v1/changelogs/' + this.props.project_id + '/' + action + '/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: (data) => {
                metrika.reach_goal(action.toUpperCase());

                if (this.props.on_moderate !== undefined) {
                    this.props.on_moderate();
                }

                this.setState({moderated: state_after});
            },
            error: (xhr, status, err) => {
                PubSub.publish('show-error', 'Something went wrong, please write to support@allmychanges.com');
                console.error('Unable to perform action ' + action + ' on changelog', status, err.toString());
            }
        });
    },
    moderate: function (e) {
        e.preventDefault();
        if (this.props.username == '') {
            // if user is anonymous, then show him a fullscreen popup @buttons.moderate
            this.setState({show_popup: true});
        } else {
            this.perform_action('add_to_moderators', true);
            var message = 'Good job! Now you can tune this package and will receive notifications about any problems.'
            PubSub.publish('show-info', message);
            this.setState({'moderated': true});
        }
    },
    unmoderate: function (e) {
        e.preventDefault();
        this.perform_action('remove_from_moderators', false);
        var message = 'We hope, you\'ll find another package you would like to to maintain.'
        PubSub.publish('show-info', message);
        this.setState({'moderated': false});
    },
    render: function() {
        if (this.state.show_popup) {
            return (
                <div className="modal-popup">
                    <div className="modal-popup__content modal-popup__please-login">
                        <p>To be able to tune this project, you need to login with:

                            <a className="button _good _large" href="/login/twitter/"><i className="fa fa-twitter fa-lg"></i> Twitter</a>
                            or
                            <a className="button _good _large" href="/login/github/"><i className="fa fa-github fa-lg"></i> GitHub</a>
                        </p>
                    </div>
                </div>);

        } else {
            if (this.state.moderated) {
                return (<div className="moderate-button">
                            <button className="button"
                                    onClick={this.unmoderate}
                                    title="Click to stop moderating this project.">Unmoderate</button>
                        </div>);
            } else {
                return (<div className="moderate-button">
                            <button className="button _good"
                                    onClick={this.moderate}
                                    title="Click to start moderating this project.">Moderate</button>
                        </div>);
            }
        }
    }
});

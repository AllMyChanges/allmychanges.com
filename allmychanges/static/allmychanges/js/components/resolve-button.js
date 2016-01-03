var React = require('react');

module.exports = React.createClass({
    getInitialState: function () {
        return {resolved: false};
    },
    handle_click: function (e) {
        e.preventDefault();
        $.ajax({
            url: '/v1/issues/' + this.props.issue_id + '/resolve/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                this.setState({resolved: true});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to resolve issue', status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        if (this.state.resolved) {
            return (<button className="button" disabled="disabled">Resolved</button>);
        } else {
            return (<button className="button" onClick={this.handle_click}>Resolve</button>);
        }
    }
});

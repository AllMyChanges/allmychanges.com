module.exports = React.createClass({
    getInitialState: function () {
        return {deleted: false};
    },
    handle_click: function (e) {
        e.preventDefault();
        $.ajax({
            url: '/v1/versions/' + this.props.version_id + '/',
            method: 'DELETE',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                this.setState({deleted: true});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to delete version', status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        if (this.state.deleted) {
            return (<button className="button" disabled="disabled">Deleted</button>);
        } else {
            return (<button className="button" onClick={this.handle_click}>Delete</button>);
        }
    }
});

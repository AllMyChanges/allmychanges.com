module.exports = React.createClass({
    getInitialState: function () {
        return {tracked: false};
    },
    handle_click: function (e) {
        e.preventDefault();
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/track/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                this.setState({tracked: true});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to track changelog', status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        if (this.state.tracked) {
            return (<button className="package-select__track-button package-select__track-button_tracked" title="Now you are tracking this package.">Tracked</button>);
        } else {
            return (<button className="package-select__track-button" onClick={this.handle_click} title="Press to receive notifications about new versions.">Track</button>);
        }
    }
});

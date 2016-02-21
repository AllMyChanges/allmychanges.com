var React = require('react');
var metrika = require('./metrika.js');

module.exports = React.createClass({
    getInitialState: function () {
        return {opened: (this.props.opened == 'true')};
    },
    open: function () {
        this.setState({opened: true});
    },
    close: function () {
        this.setState({opened: false});
    },
    render: function() {
        if (this.state.opened) {
            return (<div className="login-menu">
                      <a className="login-menu__button"
                              onClick={this.close}
                              title="Click to close a menu.">{this.props.username}</a>
                      <ul className="login-menu__items">
                        <li><a href="/account/settings/">Settings</a></li>
                        <li><a href="/logout/?next=/">Logout</a></li>
                      </ul>
                    </div>);
        } else {
            return (<div className="login-menu">
                      <a className="login-menu__button"
                              onClick={this.open}
                              title="Click to open a menu.">{this.props.username}</a>
                    </div>);
        }
    }
});

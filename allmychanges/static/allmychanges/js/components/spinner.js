var React = require('react');

var Spinner = React.createClass({
    getInitialState: function() {
        return {
        };
    },
    render: function() {
        console.log('test');
        return (<div className="mdl-spinner mdl-js-spinner is-active"></div>);
    },
    componentDidUpdate: function() {
        componentHandler.upgradeDom();
    }
});

module.exports = Spinner;

/*
  This module renders bottom panel with downloader and parser settings.
*/
var React = require('react');

var Panel = React.createClass({
    getInitialState: function() {
        return {
            collapsed: false,
            class: "changelog-settings__tune"
        }
    },
    componentDidMount: function() {
        var margin = 20;
        
        if (this.state.collapsed) {
            this.height = margin;
        } else {
            // Попробовать React.findDOMNode(this)
            this.height = $('.changelog-settings__tune-content').height() + margin;
            console.log('=========> new height calculated: ' + this.height);
        }
        
        this.timer = setInterval(() => {
            var new_height;
            if (this.state.collapsed) {
                new_height = margin;
            } else {
                new_height = $('.changelog-settings__tune-content').height() + margin;
            }
            if (this.height != new_height) {
                console.log('Forcing update from component');
                this.height = new_height;
                this.forceUpdate();
            }
        }, 50);

    },
    componentWillUnmount: function() {
        clearInterval(this.timer);
    },
    render: function() {
        var style = {};
        var content = this.props.children;
        
        if (content === undefined) {
            console.log('Setting height to 0 during rendering');
            style['height'] = 0;
            style['padding-top'] = 0;
            style['padding-bottom'] = 0;
        } else {
            console.log('Setting height to ' + this.height + ' during rendering');
            style['height'] = this.height;
        }

        var on_click = (ev) => {
            console.log('Clicked');
            
            if (this.state.collapsed) {
                this.setState({
                    collapsed: false,
                    class: "changelog-settings__tune"
                });
            } else {
                this.setState({
                    collapsed: true,
                    class: "changelog-settings__tune changelog-settings__tune_collapsed"
                });
            }
        };
        
        var collapse_button;
        if (this.state.collapsed) {
            collapse_button = (
<button className="changelog-settings__collapse-button"
        onClick={on_click}>︽</button>);
        } else {
            collapse_button = (
<button className="changelog-settings__collapse-button"
        onClick={on_click}>︾</button>);
        }

        // ⬆︎
        
        return (
<div key="tune" className={this.state.class} style={style}>
  { collapse_button }
  <div className="changelog-settings__tune-content">
    {content}
  </div>
</div>
        );
    }
});
                              
module.exports = Panel;

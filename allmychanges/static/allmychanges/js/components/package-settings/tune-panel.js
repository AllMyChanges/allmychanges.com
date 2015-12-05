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
    render: function() {
        var style = {};
        var content = this.props.children;
        
        if (content === undefined) {
            console.log('Setting height to 0 during rendering');
            style['height'] = 0;
            style['padding-top'] = 0;
            style['padding-bottom'] = 0;
        } else {
            var new_height;
            if (this.state.collapsed) {
                new_height = 20;
            } else {
                new_height = $('.changelog-settings__tune-content').height() + 20;
            }
            console.log('Setting height to ' + new_height + ' during rendering');
            style['height'] = new_height;
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
        onClick={on_click}>⬆︎ ⬆︎ ⬆︎︎</button>);
        } else {
            collapse_button = (
<button className="changelog-settings__collapse-button"
        onClick={on_click}>⬇︎ ⬇︎ ⬇︎</button>);
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

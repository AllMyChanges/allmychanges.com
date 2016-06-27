var css = require('./index.styl');
var React = require('react');
var ReactMDL = require('react-mdl');
var Button = ReactMDL.Button;

module.exports = React.createClass({
    getInitialState: function () {
        return {
            show: true
        };
    },
    handle_close: function (e) {
        this.setState({'show': false});
    },
    check_if_esc_was_pressed: function (e) {
        if (e.key === 'ESC') {
            this.add_new_tag(e);
        }
    },
    render: function() {
        if (this.state.show) {
            return (
                 <div className="modal-popup"
                      onKeyPress={this.check_if_esc_was_pressed}
                      onClick={this.handle_close}>
                  
                   <div className="modal-popup__content tagging-help">
                    <h1>What</h1>
                    <p>Tags allow to mark dependencies or soft you are using.</p>
                    <p>Tag could have any meaning: a hostname, a name of a project or some environment, where library used.</p>

                    <h1>Why</h1>
                    <p>Tags mark a project's version and displayed on pages of the service and in notifications. They remind you which version are you use and if there any updates.</p>

                    <h1>How</h1>
                    <p>To tag some version, click "Tag" button beside version number on this page.</p>
                    <p>You can also use <a href="https://github.com/svetlyak40wt/allmychanges">amch</a> with <a href="https://github.com/allmychanges/pip2amch">pip2amch</a> (or similar tool), to automate version tagging.</p>
                      
                    <p className="close-button-row"><Button onClick={this.on_done}>Close</Button></p>
                   </div>
                </div>
            );
        } else {
            return (<div></div>);
        }
    }
});

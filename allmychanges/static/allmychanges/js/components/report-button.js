var React = require('react');
var metrika = require('./metrika.js');

module.exports = React.createClass({
    getInitialState: function () {
        return {show_popup: false,
                body_callback_installed: false};
    },
    handle_switcher_click: function (e) {
        // user clicked report button @buttons.report
        metrika.reach_goal('CLICK-REPORT-BUTTON');

        e.nativeEvent.stopImmediatePropagation();
        e.preventDefault();

        if (this.state.body_callback_installed == false) {
            $(document).click(function() {
                this.setState({show_popup: false});
                // hiding from body click @buttons.report
            }.bind(this));
            this.setState({body_callback_installed: true});
        }

        if (this.state.show_popup) {
            this.setState({show_popup: false});
        } else {
            this.setState({show_popup: true});
        }
    },
    handle_form_keypress: function (e) {
        if (e.key == 'Enter' && (e.metaKey || e.ctrlKey)) {
            this.handle_post(e);
        }
    },
    handle_popup_click: function (e) {
        // popup click @buttons.report
        e.nativeEvent.stopImmediatePropagation();
    },
    handle_post: function (e) {
        // sending feedback to the server @report.button
        metrika.reach_goal('REPORT');
        e.preventDefault();
        var type = this.refs.type.getDOMNode().value.trim();
        var comment = this.refs.comment.getDOMNode().value.trim();

        $.ajax({
            url: '/v1/issues/',
            dataType: 'json',
            type: 'POST',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            data: {changelog: this.props.changelog_id,
                   type: type,
                   comment: comment},
            success: function(data) {
                this.setState({show_popup: false});
                PubSub.publish('show-info', 'Thank you for reporing about the issue. We\'ll fix it as soon as possible.');
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        var popup;
        if (this.state.show_popup) {
            popup = <div className="report-button__popup" onClick={this.handle_popup_click}>
                <form className="form" onSubmit={this.handle_post}>
                  <label htmlFor="type">Problem type:</label>
                  <select className="select-box" ref="type" placeholder="Some issue type">
                    <option value="other">---</option>
                    <option value="version-missing">Some version is missing</option>
                    <option value="wrong-version">I found version which is wrong</option>
                    <option value="wrong-dates">There is some problem with dates</option>
                    <option value="wrong-version-content">A problem with content parsing</option>
                    <option value="other">Other issue</option>
                  </select><br/>
                  <textarea className="textarea"
                            ref="comment"
                            onKeyPress={this.handle_form_keypress}
                            placeholder="Please, describe issue here">
                  </textarea><br/>
                  <table className="form-buttons">
                    <tr>
                      <td className="form-buttons__back"></td>
                      <td className="form-buttons__next">
                        <button className="button _good">Report</button>
                      </td>
                    </tr>
                   </table>
                </form>
            </div>;
        }
        return  (<div className="report-button__dropdown"><button className="button" onClick={this.handle_switcher_click} title="If you found some issues with this changelog, please file this issue."><i className="fa fa-exclamation-circle fa-lg" style={{color: '#D9534F', marginRight: '5px'}}></i>Report</button>{popup}</div>);
    }
});

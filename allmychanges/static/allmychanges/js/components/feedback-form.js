var React = require('react');
var metrika = require('./metrika.js')

module.exports = React.createClass({
    getInitialState: function () {
        return {enable_submit: false};
    },
    handle_form_keypress: function (e) {
        if (e.key == 'Enter' && (e.metaKey || e.ctrlKey)) {
            this.handle_post(e);
        }
    },
    handle_comment_change: function (e) {
        this.setState({
            enable_submit: (this.refs.comment.getDOMNode().value.trim().length > 0)});
    },
    handle_post: function (e) {
        // sending feedback to the server @report.button
        metrika.reach_goal('REPORT');
        e.preventDefault();
        var comment = this.refs.comment.getDOMNode().value.trim();
        var email = this.refs.email.getDOMNode().value.trim();

        $.ajax({
            url: '/v1/issues/',
            dataType: 'json',
            type: 'POST',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            data: {type: 'feedback',
                   email: email,
                   page: this.props.page,
                   comment: comment},
            success: function(data) {
                this.setState({show_popup: false});
                this.refs.comment.getDOMNode().value = '';
                PubSub.publish('show-info', 'Thank you for sharing your ideas!');
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        var form = <form className="form" onSubmit={this.handle_post}>
            <input ref="email" className="text-input" placeholder="Your email will let us answer you, but it is optional." type="text" maxLength="100"/>
            <textarea className="textarea"
                      ref="comment"
                      onKeyPress={this.handle_form_keypress}
                      onChange={this.handle_comment_change}
                      placeholder="Please, describe your ideas here.">
            </textarea><br/>
            <table className="form-buttons">
               <tr>
                  <td className="form-buttons__back"></td>
                  <td className="form-buttons__next">
                     <button className="button _good"
                             disabled={this.state.enable_submit ? false: "disabled"}>Send</button>
                  </td>
               </tr>
            </table>
        </form>;
        return  form;
    }
});

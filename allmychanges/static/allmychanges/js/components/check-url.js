var React = require('react');
// var ReactMDL = require('react-mdl');
// var TextField = ReactMDL.Spinner;
// var Button = ReactMDL.Spinner;

module.exports = (field_name, check_callback) => React.createClass({
    getInitialState: function () {
        return {sending: false,
                url: this.props.url,
                error: this.props.error};
    },
    handle_click: function (e) {
        e.preventDefault();
        this.setState({'sending': true});
        check_callback(this.state.url, this.setState.bind(this));
    },
    handle_url_change: function (event) {
        this.setState({url: event.target.value});
    },
    render: function() {
        var disabled = false;
        var error_message;

        if (this.state.error) {
            error_message = <span class="mdl-textfield__error">{this.state.error}</span>;
        }
        
        if (this.state.sending) {
            disabled = true;
        }
        
        return (
                <table className={field_name} width="100%">
                <tr>
                <td width="100%">
                <input disabled={disabled} className="mdl-textfield__input" maxLength="2000" name={field_name} type="url" value={this.state.url} onChange={this.handle_url_change} />
                {error_message}
                </td>
                <td>
                <button disabled={disabled} className="mdl-button mdl-button--raised" onClick={this.handle_click} style={{marginLeft: '10px'}}>Test</button>
                </td>
                </tr>
  </table>);
    }
});

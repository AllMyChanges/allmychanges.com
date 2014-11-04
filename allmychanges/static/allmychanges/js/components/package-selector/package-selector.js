var Package = require('./package.js')

module.exports = React.createClass({
    getInitialState: function () {
        return {packages: []};
    },
    componentDidMount: function() {
        $.ajax({
            url: this.props.url,
            dataType: 'json',
            success: function(data) {
                this.setState({packages: data.results});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        var packages_list = this.state.packages.map(function (package) {
            return (
                <Package key={package.id}
                         changelog_id={package.id}
                         namespace={package.namespace}
                         name={package.name}
                         versions={package.versions}/>
            );
        });
        return (
            <ul className="package-selector">
                {packages_list}
            </ul>
        );
    }
});

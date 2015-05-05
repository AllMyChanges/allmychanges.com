var PackageSelector = require('./package-selector/package-selector.js')

module.exports = React.createClass({
    getInitialState: function () {
        // init landing page @landing-page
        return {num_tracked: 0};
    },
    componentDidMount: function() {
    },
    render: function() {
        return (<div className="landing-page">
                  <PackageSelector url='/v1/landing-package-suggest/?limit=1&amp;versions_limit=5'/>
                </div>);
    }
});

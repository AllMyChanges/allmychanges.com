var PackageSelector = require('../components/package-selector/package-selector.js')

module.exports = {
    render: function () {
        React.render(
                <PackageSelector url='/v1/landing-package-suggest/?limit=20&amp;versions_limit=5'/>,
            document.getElementById('login-index')
        );
    }
}

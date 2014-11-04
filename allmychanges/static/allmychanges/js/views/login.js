var PackageSelector = require('../components/package-selector/package-selector.js')

module.exports = {
    render: function () {
        var element = document.getElementById('login-index');

        if (element !== null) {
            React.render(
                <PackageSelector url='/v1/landing-package-suggest/?limit=20&amp;versions_limit=5'/>,
                element);
        }
    }
}

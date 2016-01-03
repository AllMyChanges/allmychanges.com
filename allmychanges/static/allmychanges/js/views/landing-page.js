var React = require('react');
var Landing = require('../components/landing-page.js')

module.exports = {
    render: function () {
        $('.landing-page-container').each(function (idx, element) {
            React.render(<Landing/>, element);
        });
    }
}

var React = require('react');
var Promo = require('../components/ios-promo.js')

module.exports = {
    render: function () {
        $('.ios-promo-container').each(function (idx, element) {
            React.render(<Promo/>, element);
        });
    }
}

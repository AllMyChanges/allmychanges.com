var React = require('react');
var Share = require('../components/share.js')

module.exports = {
    render: function () {
        $('.share-badge-container').each(function (idx, element) {
            React.render(
                <Share namespace={element.dataset['namespace']}
                       name={element.dataset['name']}/>,
                element);
        });
    }
}

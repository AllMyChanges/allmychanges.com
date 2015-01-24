var ReportButton = require('../components/report-button.js')
var ResolveButton = require('../components/resolve-button.js')
var DeleteButton = require('../components/delete-button.js')
var Typeahead = require('../components/typeahead.js')

module.exports = {
    render: function () {
        $('.report-button').each(function (idx, element) {
            React.render(
                <ReportButton changelog_id={element.dataset['changelogId']}/>,
                element);
        });

        $('.resolve-button-container').each(function (idx, element) {
            React.render(
                <ResolveButton issue_id={element.dataset['issueId']}/>,
                element);
        });
        $('.delete-button-container').each(function (idx, element) {
            React.render(
                <DeleteButton version_id={element.dataset['versionId']}/>,
                element);
        });
        $('.typeahead').each(function (idx, element) {
            React.render(
                <Typeahead />,
                element);
        });
    }
}

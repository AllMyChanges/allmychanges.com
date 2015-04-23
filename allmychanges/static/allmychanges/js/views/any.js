var LoginMenu = require('../components/login-menu.js')
var ReportButton = require('../components/report-button.js')
var ResolveButton = require('../components/resolve-button.js')
var DeleteButton = require('../components/delete-button.js')
var TrackButton = require('../components/track-button.js')
var MagicPrompt = require('../components/magic-prompt.js')
var Share = require('../components/share.js')
var Notifications = require('../components/notifications.js')
var FeedbackForm = require('../components/feedback-form.js')


module.exports = {
    render: function () {
        $('.report-button').each(function (idx, element) {
            React.render(
                <ReportButton changelog_id={element.dataset['changelogId']}/>,
                element);
        });

        $('.track-button-container').each(function (idx, element) {
            React.render(
                <TrackButton changelog_id={element.dataset['changelogId']}
                             tracked={element.dataset['tracked']}
                             username={username}
                             num_trackers={element.dataset['numTrackers']}/>,
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
        $('.magic-prompt-container').each(function (idx, element) {
            React.render(
                <MagicPrompt />,
                element);
        });
        $('.login-menu-container').each(function (idx, element) {
            React.render(
                <LoginMenu opened={element.dataset['opened']}
                           username={element.dataset['username']}/>,
                element);
        });
        $('.notifications-container').each(function (idx, element) {
            React.render(
                <Notifications/>,
                element);
        });
        $('.feedback-form-container').each(function (idx, element) {
            React.render(
                <FeedbackForm page={element.dataset['page']}/>,
                element);
        });
    }
}

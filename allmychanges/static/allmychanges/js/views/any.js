var React = require('react');
var ReactDOM = require('react-dom');

var LoginMenu = require('../components/login-menu.js')
var ReportButton = require('../components/report-button.js')
var ResolveButton = require('../components/resolve-button.js')
var DeleteButton = require('../components/delete-button.js')
var TagButton = require('../components/tag-button')
var TagHelp = require('../components/tag-help')
var TrackButton = require('../components/track-button.js')
var SlackURL = require('../components/slack-url.js')
var WebhookURL = require('../components/webhook-url.js')
var MagicPrompt = require('../components/magic-prompt.js')
var Share = require('../components/share.js')
var Notifications = require('../components/notifications.js')
var FeedbackForm = require('../components/feedback-form.js')
var PackageSettings = require('../components/package-settings')
var init_sticky_versions = require('../components/sticky-versions');

/* make introjs globally available */
window.intro = require('../components/intro.js')


$(document).ready(function() {
    init_sticky_versions();
    
    window.intro.push({'element': $(".magic-prompt")[0],
                       'intro': 'Using this search bar, you could search for packages and add a source URLs.'
                      }, 500);

    var intro_was_shown = false;
    var show_intro = function () {
        // may be showing intro if [intro_was_shown] @intro.show
        if (!intro_was_shown) {
            window.intro.start()
            intro_was_shown = true;
        }
    };

    // setting idle timer @intro.idle
    // window.intro_idle = new Idle({
    //     onAway : show_intro,
    //     awayTimeout : 15000
    // });
    // window.intro_idle.start();
});

module.exports = {
    render: function () {
        $('.report-button').each(function (idx, element) {
            ReactDOM.render(
                <ReportButton changelog_id={element.dataset['changelogId']}/>,
                element);
        });

        $('.track-button-container').each(function (idx, element) {
            ReactDOM.render(
                <TrackButton changelog_id={element.dataset['changelogId']}
                             tracked={element.dataset['tracked']}
                             username={username}
                             num_trackers={element.dataset['numTrackers']}/>,
                element);
        });

        $('.resolve-button-container').each(function (idx, element) {
            ReactDOM.render(
                <ResolveButton issue_id={element.dataset['issueId']}/>,
                element);
        });
        $('.delete-button-container').each(function (idx, element) {
            ReactDOM.render(
                <DeleteButton version_id={element.dataset['versionId']}/>,
                element);
        });

        var tag_help_shown = false;
        
        $('.tag-help-container').each(function (idx, element) {
            ReactDOM.render(<TagHelp key="help" />, element);
        });
        $('.tag-button-container').each(function (idx, element) {
            ReactDOM.render(
                <TagButton key="button"
                           version_id={element.dataset['versionId']}
                           version_number={element.dataset['versionNumber']}
                           project_id={element.dataset['projectId']}/>,
                element);
        });
        $('.slack-url-container').each(function (idx, element) {
            ReactDOM.render(
                    <SlackURL url={element.dataset['url']}
                              error={element.dataset['error']}/>,
                element);
        });
        $('.webhook-url-container').each(function (idx, element) {
            ReactDOM.render(
                    <WebhookURL url={element.dataset['url']}
                                error={element.dataset['error']}/>,
                element);
        });
        $('.magic-prompt-container').each(function (idx, element) {
            ReactDOM.render(
                <MagicPrompt />,
                element);
        });
        $('.login-menu-container').each(function (idx, element) {
            ReactDOM.render(
                <LoginMenu opened={element.dataset['opened']}
                           username={element.dataset['username']}/>,
                element);
        });
        $('.notifications-container').each(function (idx, element) {
            ReactDOM.render(
                <Notifications/>,
                element);
        });
        $('.feedback-form-container').each(function (idx, element) {
            ReactDOM.render(
                <FeedbackForm page={element.dataset['page']}/>,
                element);
        });
        $('.add-new-container').each(function (idx, element) {
            var downloader_settings = element.dataset['downloaderSettings'];
            downloader_settings = JSON.parse(downloader_settings);
            
            var guessed_sources = element.dataset['guessedSources'];
            guessed_sources = JSON.parse(guessed_sources);
            
            ReactDOM.render(
                <PackageSettings
                     preview_id={element.dataset['previewId']}
                     changelog_id={element.dataset['changelogId']}
                     source={element.dataset['source']}
                     downloader={element.dataset['downloader']}
                     downloader_settings={downloader_settings}
                     name={element.dataset['name']}
                     namespace={element.dataset['namespace']}
                     description={element.dataset['description']}
                     search_list={element.dataset['searchList']}
                     ignore_list={element.dataset['ignoreList']}
                     xslt={element.dataset['xslt']}
                     guessed_sources={guessed_sources}
                     mode={element.dataset['mode']}/>,
                element);
        });
    }
}

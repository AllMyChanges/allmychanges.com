var R = require('ramda');
var React = require('react');
var DOWNLOADERS_SETTINGS_RENDERERS = require('./downloaders-settings');
var default_option_value = '---';

var panel = function (opts) {
    var available_downloaders = {'feed': 'Rss/Atom Feed',
                                 'http': 'Single HTML Page',
                                 'rechttp': 'Multiple HTML Pages',
                                 'google_play': 'Google Play',
                                 'itunes': 'Apple AppStore', // TODO убрать это после полной миграции настроек даунлоадеров
                                 'appstore': 'Apple AppStore',
                                 'vcs.git': 'Git Repository',
                                 'vcs.git_commits': 'Git Commits',
                                 'hg': 'Mercurial Repository',
                                 'github_releases': 'GitHub Releases'};
    var render_option = function (item) {
        var name = item.name;
        return <option value={name} key={name}>{available_downloaders[name]}</option>;
    };
    
    var options = [<option value={null} key="undefined">{default_option_value}</option>].concat(
        R.map(render_option, opts.downloaders));

    var button_style = {transition: 'all 0.2s ease-in', opacity: 0};
    var button_disabled = true;
    
    if (opts.need_apply) {
        button_style.opacity = 1;
        button_disabled = false;
    } else {
        button_style.cursor = 'default';
    }

    // var downloader_name;
    // if (opts.downloader) {
    //     downloader_name = opts.downloader;
    // } else {
    //     if (opts.downloaders.length > 0) {
    //         downloader_name = opts.downloaders[0].name;
    //     }
    // }

    function on_change_downloader_settings(new_settings) {
        console.log('New downloader settings:');
        console.log(new_settings);
    }

    // if (opts.downloader !== undefined) {
    //     debugger
    // }
    var downloader_settings_renderer = DOWNLOADERS_SETTINGS_RENDERERS[opts.downloader];
    var downloader_settings;
    
    if (downloader_settings_renderer !== undefined) {
        downloader_settings = downloader_settings_renderer(
            opts.downloader_settings,
            opts.update_settings);
    }

    var on_downloader_change = (event) => {
        console.log('on_downloader_change');
        var value = event.target.value;
        if (value == default_option_value) {
            value = null;
        }
        opts.update_downloader(value);
        opts.update_settings({});
    }
        
    var change_downloader_panel = (
        <div key="downloader-panel">
            <div className="changelog-settings__tune-panel">
              <p>Please, select which downloader to use:</p>
              <select className="downloader-selector"
                      name="downloader"
                      value={opts.downloader}
                      onChange={on_downloader_change}>
                {options}
              </select>

              {downloader_settings}
              
              <p className="buttons-row">
                <input type="submit"
                       className="button _good _large"
                       value="Apply"
                       onClick={opts.on_submit}
                       style={button_style}
                       disabled={button_disabled}/>
              </p>
            </div>
        </div>);

    return change_downloader_panel;
}

module.exports = panel

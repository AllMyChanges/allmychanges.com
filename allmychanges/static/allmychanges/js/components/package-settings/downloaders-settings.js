var React = require('react');
var R = require('ramda');

// each downloader should get two parameters:
// settings is a dictionary with downloader's settings
// update_settings is a function of parent component
// to be called to change 'downloader_settings' attribute
// of the preview

function http (settings, update_settings) {
    var on_recursive_change = (event) => {
        if (event.target.checked) {
            settings = R.assoc('recursive', true, settings);
        } else {
            settings = R.dissoc('recursive', settings);
        }
        update_settings(settings);
    };
    
    var on_search_list_change = (event) => {
        settings = R.assoc('search_list', event.target.value, settings);
        update_settings(settings);
    };
    
    var on_ignore_list_change = (event) => {
        settings = R.assoc('ignore_list', event.target.value, settings);
        update_settings(settings);
    };
    
    var recursive_settings;

    if (settings.recursive) {
        recursive_settings = (
<div>
  <label htmlFor="ignore_list">Download urls like these:</label>
  <textarea placeholder="Enter here a directories where parser should search for changelogs. By default parser searches through all sources and sometimes it consider a changelog file which are not changelogs. Using this field you could narrow the search."
            className="new-package__search-input"
            name="search_list"
            onChange={on_search_list_change}
            value={settings.search_list}></textarea>
  
  <label htmlFor="ignore_list">Ignore these url patterns:</label>
  <textarea placeholder="Here you could enter a list of directories to ignore during the changelog search. This is another way how to prevent robot from taking changelog-like data from wierd places."
            className="new-package__ignore-input"
            name="ignore_list"
            onChange={on_ignore_list_change}
            value={settings.ignore_list}></textarea>
</div>);
    }

    return (
            <div>
              <label htmlFor="recursive">Recursive:</label>
              <input type="checkbox" name="recusive" checked={settings.recursive} onChange={on_recursive_change}/>
              { recursive_settings }
            </div>);
};


function git (settings, update_settings) {
    return <p>GIT DOWNLOADER SETTINGS</p>;
};


function unknown (settings, update_settings) {
    return <p>Our algorithms were unable to determine right downloader settings.</p>;
};

module.exports = {
    'http': http,
    'git': git,
    null: unknown
}

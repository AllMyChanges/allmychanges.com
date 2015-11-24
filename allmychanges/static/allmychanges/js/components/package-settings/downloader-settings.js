var React = require('react');

function http () {
    var settings = this.state.downloader_settings;
    
    var update_settings = event => {
        var name = event.target.name;
        var new_value = event.target.value;
        if (event.target.type == 'checkbox') {
            new_value = event.target.checked
        }
        console.log('Updating downloader setting ' + name + '=' + new_value);
        
        settings[name] = new_value;
        this.setState({'downloader_settings': settings});
    };

    return <p><input type="checkbox" name="recusive" checked={settings.recursive} onChange={update_settings}/></p>;
};

function git (settings) {
    return <p>GIT DOWNLOADER SETTINGS</p>;
};

module.exports = {
    'http': http,
    'git': git
}

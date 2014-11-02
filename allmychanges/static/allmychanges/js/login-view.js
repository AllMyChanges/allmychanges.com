console.log('LOGIN_VEW');

var TrackButton = React.createClass({
    getInitialState: function () {
        return {tracked: false};
    },
    handle_click: function (e) {
        e.preventDefault();
        $.ajax({
            url: '/v1/changelogs/' + this.props.changelog_id + '/track/',
            method: 'POST',
            dataType: 'json',
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function(data) {
                this.setState({tracked: true});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error('Unable to track changelog', status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        if (this.state.tracked) {
            return (<button className="package-select__track-button package-select__track-button_tracked">Tracked</button>);
        } else {
            return (<button className="package-select__track-button" onClick={this.handle_click}>Track</button>);
        }
    }
});

var Package = React.createClass({
  render: function() {
      var versions = this.props.versions.map(function(version) {
          return  (
                  <li className="package-selector__version">
                    <span className="package-selector__number">{version.number}</span>
                    <span className="package-selector__date">Released at {version.date}</span>
                  </li>
          );
      });

    var url = '/p/' + this.props.namespace + '/' + this.props.name + '/';
    return (
    <li className="package-selector__item">
    <div className="package-selector__package">
      <h1 className="package-selector__title"><a href={url}>{this.props.namespace}/{this.props.name}</a></h1>
      <ul className="package-selector__versions">
            {versions}
      </ul>
      <TrackButton changelog_id={this.props.changelog_id}/>
    </div>
    </li>
    );
  }
});

var PackageList = React.createClass({
    getInitialState: function () {
        return {packages: []};
    },
    componentDidMount: function() {
        $.ajax({
            url: this.props.url,
            dataType: 'json',
            success: function(data) {
                this.setState({packages: data.results});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        var packages_list = this.state.packages.map(function (package) {
            return (
                <Package changelog_id={package.id}
                         namespace={package.namespace}
                         name={package.name}
                         versions={package.versions}/>
            );
        });
        return (
            <ul className="package-selector">
                {packages_list}
            </ul>
        );
    }
});


React.render(
  <PackageList url='/v1/landing-package-suggest/?limit=20&amp;versions_limit=5'/>,
  document.getElementById('login-index')
);

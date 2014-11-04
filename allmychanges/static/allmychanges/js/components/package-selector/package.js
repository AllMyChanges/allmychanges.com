TrackButton = require('../track-button.js')

module.exports = React.createClass({
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

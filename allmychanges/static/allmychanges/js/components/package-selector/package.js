TrackButton = require('../track-button.js')
SkipButton = require('../skip-button.js')

module.exports = React.createClass({
  render: function() {
    var changelog_id = this.props.changelog_id;

    var on_track = function () {
        this.props.track_handler({id: this.props.changelog_id,
                                  namespace: this.props.namespace,
                                  name: this.props.name});
    }.bind(this);

    var url = '/p/' + this.props.namespace + '/' + this.props.name + '/';
    return (
    <div className="package-selector__package">
      <h1 className="package-selector__title"><a href={url}>{this.props.namespace}/{this.props.name}</a></h1>
      <h2 className="package-selector__description">{this.props.description}</h2>
      <iframe className="package-selector__versions" src={"/package-selector-versions/?changelog=" + this.props.changelog_id}/>
      <div className="package-selector__buttons">
        <TrackButton changelog_id={this.props.changelog_id} num_trackers={false} on_track={on_track}/>
        <SkipButton changelog_id={this.props.changelog_id} on_skip={this.props.skip_handler}/>
      </div>
    </div>
    );
  }
});

module.exports = React.createClass({
    getInitialState: function () {
        return {active_tab: 'markdown'};
    },
    show: function (tab) {
        return function () {
            this.setState({active_tab: tab});
        }.bind(this);
    },
    render: function() {
        var base_url = window.location.origin + '/p/' + this.props.namespace + '/' + this.props.name + '/';
        var package_url = base_url + '?utm_source=badge';
        var image_url = base_url + 'badge/';
        var tab_classes = {}
        tab_classes[this.state.active_tab] = 'tab_active';

        var get_content = function (tab) {
            var snippets = {
                markdown: '[![changelog](' + image_url + ')](' + package_url + ')',
                rst: '.. image:: ' + image_url + '\n   :target: ' + package_url,
                html: '<a href="' + package_url + '"><img title="changelog" src="' + image_url + '"/></a>'};
            var num_rows = {markdown: 1, rst: 2, html: 1};
            return (<textarea readOnly="1"
                              wrap="off"
                              rows={num_rows[tab]}
                              className="text-input share-badge__text"
                              value={snippets[tab]}></textarea>);
        }

        return (
<table className="share-badge">
  <tbody>
    <tr>
      <td></td>
      <td>
        <ul className="share-badge__tabs">
          <li className={"tab " + tab_classes.markdown} onClick={this.show('markdown')}>markdown</li>
          <li className={"tab " + tab_classes.rst} onClick={this.show('rst')}>reST</li>
          <li className={"tab " + tab_classes.html} onClick={this.show('html')}>html</li>
        </ul>
      </td>
    </tr>

    <tr>
      <td>
        <img className="share-badge__example" src={image_url}/>
      </td>
      <td>
        {get_content(this.state.active_tab)}
      </td>
    </tr>
  </tbody>
</table>);
    }
});

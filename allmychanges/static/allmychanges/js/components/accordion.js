/** @jsx React.DOM **/

var React = require('react');

var Section = React.createClass({
  handleClick: function(){
    if(this.state.open) {
      this.setState({
        open: false,
        class: "accordion__section"
      });
    }else{
      this.setState({
        open: true,
        class: "accordion__section accordion__section_open"
      });
    }
  },
  getInitialState: function(){
     return {
       open: false,
       class: "accordion__section"
     }
  },
  render: function() {
    return (
      <div className={this.state.class}>
        <button>toggle</button>
        <div className="accordion__section-head" onClick={this.handleClick}>{this.props.title}</div>
        <div className="accordion__content-wrap">
          <div className="accordion__content">
            {this.props.children}
          </div>
        </div>
      </div>
    );
  }
});

var Accordion = React.createClass({
    render: function() {
        var elements = this.props.elements.map(function(e, i) {
            return <Section key={i} title={e.title}>{e.content}</Section>
        });

        return <div className="accordion">{elements}</div>;
    }
});

module.exports = Accordion;


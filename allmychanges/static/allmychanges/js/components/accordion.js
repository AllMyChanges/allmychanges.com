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
    return (
      <div className="accordion">
        <Section title="Section Title One">   Lorem ipsum dolor sit amet, consectetur adipisicing elit. Amet nemo harum voluptas aliquid rem possimus nostrum excepturi!
        </Section>
        <Section title="Section Title Two">   Lorem ipsum dolor sit amet, consectetur adipisicing elit. Amet nemo harum voluptas aliquid rem possimus nostrum excepturi!
        </Section>
        <Section title="Section Title Three">   Lorem ipsum dolor sit amet, consectetur adipisicing elit. Amet nemo harum voluptas aliquid rem possimus nostrum excepturi!
        </Section>
      </div>
    );
  }
});

module.exports = Accordion;

// React.renderComponent(<Accordion title="Accordion Title Here" />, document.getElementById('accordian')); 

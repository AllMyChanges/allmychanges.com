(function() {
  var CommentList, CommentBox;
  CommentList = React.createClass({
    displayName: "CommentList",
    render: (function() {
      return React.DOM.div({
        className: "commentList"
      }, "Hello, world! I am a CommentList.");
    })
  });
  CommentBox = React.createClass({
    displayName: "CommentBox",
    render: (function() {
      return React.DOM.div({
        className: "commentBox"
      }, (function() {
        return React.DOM.div("Hello, world! I am a CommentBox.", undefined);
      }));
    })
  });
  return React.renderComponent(CommentBox(null), document.getElementById("react-content"));
})['call'](this);
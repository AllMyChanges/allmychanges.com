(function() {
  var CommentBox;

  function mknode(name) {
    function name(attrs, children) {
      return (function() {
        return React.DOM[name](attrs, children);
      });
    }
    return name;
  }
  mknode;
  mknode(span);
  CommentBox = React.createClass({
    displayName: "CommentBox",
    render: span({
      className: "commentBox"
    }, "Hello, world! I am a CommentBox.")
  });
  return React.renderComponent(CommentBox(null), document.getElementById("react-content"));
})['call'](this);
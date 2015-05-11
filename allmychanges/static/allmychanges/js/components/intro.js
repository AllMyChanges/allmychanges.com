var PriorityQueue = require('priorityqueuejs')
var _introjs_items = new PriorityQueue(function(a, b) {
    return a.priority - b.priority});

/*
Add items like:

push({
  element: document.querySelectorAll('#step2')[0],
  intro: "Ok, wasn't that fun?",
  position: 'right'
},  // element
100 // priority
);

*/

module.exports = {
    push: function(item, priority) {
        if (priority === undefined) {
            priority = 0
        }
        item['priority'] = priority;

        _introjs_items.enq(item);
    },
    start: function(item) {
        var intro = introJs();
        intro.setOptions({
            steps: _introjs_items._elements
        });

        intro.start();
    }
};

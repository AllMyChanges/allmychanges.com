var React = require('react');

// пример использования нотификаций:
// PubSub.publish('show-info', 'Привет мир!');

module.exports = React.createClass({
    componentDidMount: function() {
        PubSub.subscribe('show-info', this.newItem);
        PubSub.subscribe('show-warning', this.newItem);
    },
    newItem: function (msg, data) {
        this.counter += 1;
        var item = {'id': this.counter,
                    'text': data}
        
        if (msg == 'show-warning') {
            item['class'] = 'warning';
        } else {
            item['class'] = 'info';
        }

        var items = this.state.items;
        items[items.length] = item;
        this.setState({show: true, items: items});
    },
    getInitialState: function () {
        this.counter = 0;
        return {show: false, items: []};
    },
    render: function() {
        var notifications;
        var closeItem2 = (item_id) => {
            return () => {
                // closing item [item_id] @notifications
                var items = this.state.items;
                items = _.filter(items, function(item) {return item.id != item_id});
                this.setState({items: items});
            };
        };

        if (this.state.show) {
            var format_item = (item) => {
                return <li className={"notifications__item notifications__" + item.class} key={item.id}><div className="notifications__close-button" onClick={closeItem2(item.id)}>+</div><span dangerouslySetInnerHTML={{__html: item.text}}></span></li>
            }
            
            notifications = _.map(this.state.items, format_item);
        }
        return  (<ul className="notifications">{notifications}</ul>);
    }
});

module.exports = React.createClass({
    componentDidMount: function(){
        var element = this.getDOMNode();
        var fetch_suggestions = function(query, cb) {
            $.get('/v1/search-autocomplete/', {q: query}, function(data) {
                var results = data['results'];
                _.each(results, function(item) {
                    if (item.type == 'package') {
                        item.value = item.namespace + '/' + item.name;
                    }
                    if (item.type == 'namespace') {
                        item.value = item.namespace;
                    }
                    if (item.type == 'add-new') {
                        item.value = item.source;
                    }
                });

                cb(results);
            });
        };

        var show_by_type = {
            'package': _.template('<div class="magic-prompt2__suggest-item"><%- namespace %>/<%- name %></div>'),
            'namespace': _.template('<div class="magic-prompt2__suggest-item"><%- namespace %></div>'),
            'add-new': _.template('<div class="magic-prompt2__suggest-item"><%- source %> <span class="button _good">add new</span></div>')
        }

        var show_suggestion = function (obj) {
            return show_by_type[obj.type](obj);
        }

        $(element).find('.magic-prompt2__input').typeahead(
            {
                minLength: 1,
                highlight: true
            },
            {
                name: 'magic-prompt',
                displayKey: 'value',
                
                // Just a little object that implements the necessary 
                // signature to plug into typeahead.js
                source: fetch_suggestions,
                templates: {
                    empty: '<div class="magic-prompt2__no-matches">No matches found</div>',
                    suggestion: show_suggestion
                }
            });
        
        // Behind the scenes, this is just delegating to Backbone's router
        // to 'navigate' the main pane of the page to a different view
        $(element).on('typeahead:selected', function(jquery, option){
            window.location = option.url;
        });
    },
    
    componentWillUnmount: function(){
        var element = this.getDOMNode();
        $(element).find('.magic-prompt2__input').typeahead('destroy');
    },

    render: function(){
        return (
            <div className="magic-prompt2">
                <form action="/search/" method="GET">
                  <input type="search" name="q" ref="input" 
                         className="magic-prompt2__input" 
                         placeholder="Search packages and namespaces" />
                  <input type="submit" className="button _good _large magic-prompt2__submit" value="Search"/>
                </form>
            </div>
        );
    }
});

$(document).ready(function() {
    if (window.activity_heat_map !== undefined ) {

        var cal = new CalHeatMap();
        var year_ago = new Date();
        year_ago.setFullYear(year_ago.getFullYear() - 1);
        year_ago.setMonth(year_ago.getMonth() + 1);
        
        cal.init({domain: 'month',
                  subDomain: 'day',
                  tooltip: true,
                  start: year_ago,
                  data: window.activity_heat_map});
    }
});

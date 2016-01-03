var gulp = require('gulp'),
    stylus = require('gulp-stylus'),
    webpack = require('gulp-webpack'),
    user_story = require('gulp-user-story'),
    uglify = require('gulp-uglify'),
    concat = require('gulp-concat'),
    rename = require('gulp-rename');


var webpack_output = 'allmychanges/static/allmychanges/js-compiled/react-site.js';
var webpack_config = {
    output: {
        filename: webpack_output
    },
    module: {
        loaders: [
            {
                test: /\.js|\.jsx$/,
                exclude: [
                    /node_modules\/ramda/
                ],
                loader: "babel-loader"
            },
            {test: /\.styl$/, loader: "style!css!stylus"}
        ]
    }//, externals: {"react": "React"}
};

var combiner = require('stream-combiner2');

gulp.task('webpack', function() {
    // здесь мы используем combiner, как указано тут:
    // https://github.com/gulpjs/gulp/blob/master/docs/recipes/combining-streams-to-handle-errors.md#combining-streams-to-handle-errors
    // чтобы перехватить ошибки в цепочке обработчиков
    
    var combined = combiner.obj([
        gulp.src('allmychanges/static/allmychanges/js/react-site.js'),
        webpack(webpack_config),
        user_story(),
        gulp.dest('./'),
        uglify(),
        rename({extname: '.min.js'}),
        gulp.dest('./')]);

    combined.on('error', console.error.bind(console));
    return combined;
});

gulp.task('css', function() {
    return gulp.src('allmychanges/static/allmychanges/stylus/{allmychanges,email}.styl')
        .pipe(stylus())
        .pipe(gulp.dest("allmychanges/static/allmychanges/css/"));
});

var source_js_files = [
    'bower_components/lodash/lodash.js',
    'node_modules/gulp-user-story/node_modules/user-story/lib/UserStory.js',
    'node_modules/jquery/dist/jquery.js',
    'node_modules/jquery.cookie/jquery.cookie.js',
    'node_modules/jquery-sticky/jquery.sticky.js',
    'node_modules/waypoints/lib/jquery.waypoints.js',
    'allmychanges/static/spin.min.js', // TODO: это надо заменить на mdl.Spinner
    'allmychanges/static/jquery.tile.js',
    'bower_components/typeahead.js/dist/typeahead.jquery.js',
    'bower_components/PubSubJS/src/pubsub.js',
    // замена оригинала, потому что там мешает какой-то баг
    // подробнее, в README react-mdl
    'node_modules/react-mdl/extra/material.js',
    webpack_output
];

var js_dest = 'allmychanges/static/allmychanges/js-compiled/';

gulp.task('js', ['webpack'], function() {
    return gulp.src(source_js_files)
        .pipe(concat('all.js'))
        .pipe(gulp.dest(js_dest))
        .pipe(uglify())
        .pipe(rename({extname: '.min.js'}))
        .pipe(gulp.dest(js_dest));
});


gulp.task('default', ['css', 'js']);

var gulp = require('gulp'),
    uglify = require('gulp-uglify'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    webserver = require('gulp-webserver'),
    del = require('del')
;
var paths = {
        scripts: [
            'twinButton/app.js',
            'twinButton/*.js',
            // '!client/external/**/*.coffee'
        ],
      images: 'client/img/**/*'
    };

// Not all tasks need to use streams
// A gulpfile is just another node program and you can use any package available on npm
gulp.task('clean', function() {
  // You can use multiple globbing patterns as you would with `gulp.src`
  return del(['build']);
});

gulp.task('webserver', function() {
  gulp.src(__dirname)
    .pipe(webserver({
      livereload: true,
      directoryListing: true,
      open: true
    }));
});

gulp.task('scripts', ['clean'], function() {
  // Minify and copy all JavaScript (except vendor scripts)
  // with sourcemaps all the way down
  return gulp.src(paths.scripts)
    .pipe(sourcemaps.init())
      // .pipe(coffee())
      .pipe(uglify())
      .pipe(concat('components.min.js'))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('build/js'));
});
var gulp = require('gulp');
var webserver = require('gulp-webserver');
var floder = '.'; 
gulp.task('webserver', function() {
  gulp.src(floder)
    .pipe(webserver({
      livereload: true,
      directoryListing: true,
      open: true
    }));
});

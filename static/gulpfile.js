var gulp = require('gulp');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var babel = require('gulp-babel');

gulp.task('default', ['compress', 'watch'], function(){
  console.log('start...');
});
gulp.task('babel', function(){
  return gulp.src('src/*.js')
    .pipe(babel({
	    presets: ['react', 'es2015']
	}))
	.pipe(gulp.dest('build'));
});
gulp.task('compress', ['babel'], function(){
  return gulp.src(['build/*.js', '!build/*demo*'])
    .pipe(uglify())
    .pipe(concat('ng-bundle.min.js'))
    .pipe(gulp.dest('/home/python/nginx/static/js'));
});
gulp.task('watch', function() {
  gulp.watch('src/*.js', ['compress']);
});

var gulp = require('gulp');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var babel = require('gulp-babel');

gulp.task('default', ['watch'], function(){
  console.log('test');
});
gulp.task('babel', function(){
  return gulp.src('src/*.js')
    .pipe(babel({
	    presets: ['react', 'es2015']
	}))
	.pipe(gulp.dest('/home/python/nginx/static/js/'));
});
gulp.task('compress', ['babel'], function(){
  return gulp.src('bulid/*.js')
    .pipe(uglify())
    .pipe(concat('all.js'))
    .pipe(gulp.dest('dist'));
});
gulp.task('watch', function() {
  gulp.watch('src/*.js', ['babel']);
});
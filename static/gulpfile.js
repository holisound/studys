var gulp = require('gulp');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var babel = require('gulp-babel');

gulp.task('default', ['watch'], function(){
  console.log('start...');
});
gulp.task('babel', function(){
  var dirname = '/home/python/nginx/static/js';
  return gulp.src('src/*.js')
    .pipe(babel({
	    presets: ['react', 'es2015']
	}))
	.pipe(gulp.dest(dirname))
	.pipe(uglify())
	.pipe(concat('bundle.min.js'))
	.pipe(gulp.dest(dirname));
});
gulp.task('watch', function() {
  gulp.watch('src/*.js', ['babel']);
});

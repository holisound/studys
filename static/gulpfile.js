var gulp = require('gulp');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var babel = require('gulp-babel');
gulp.task('default', ['compress'], function(){
  console.log('test');
});
gulp.task('babel', function(){
  return gulp.src('src/*.js')
    .pipe(babel({
	    presets: ['react', 'es2015']
	}))
	.pipe(gulp.dest('bulid'));
});
gulp.task('compress', ['babel'], function(){
  return gulp.src('bulid/*.js')
    .pipe(uglify())
    .pipe(concat('all.js'))
    .pipe(gulp.dest('dist'));
});

#!/bin/bash
basedir=/home/edward/backup
PATH=/bin:/usr/bin:/sbin:/usr/sbin; export PATH
export LANG=C
bakname=$basedir/gallery.$(date +%Y-%m-%d).sql
[ ! -d "$basedir" ] && mkdir $basedir

/usr/bin/mysqldump -uroot -p123123 gallery > $bakname

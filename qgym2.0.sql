-- [gallery]
-- photos grouped and ordered by upload-date desc
-- user can toggle photos' privacy 
CREATE TABLE IF NOT EXISTS photo_table(
photo_id INT UNSIGNED KEY AUTO_INCREMENT,
photo_userid INT UNSIGNED NOT NULL,
photo_uuid VARCHAR(64) NOT NULL,
photo_uploadtime DATETIME NOT NULL DEFAULT NOW(),
photo_viewtimes INT UNSIGNED NOT NULL DEFAULT 0,
photo_stars TEXT,
photo_privacy INT UNSIGNED NOT NULL DEFAULT 0
-- deleteflag INT UNSIGNED NOT NULL DEFAULT 0
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;
-- [comment]
CREATE TABLE IF NOT EXISTS comment_table(
comment_id INT UNSIGNED KEY AUTO_INCREMENT,
comment_userid INT UNSIGNED NOT NULL,
-- comment_type 1: photo
comment_type INT UNSIGNED  NOT NULL,
comment_objectid INT UNSIGNED NOT NULL,
comment_content TEXT NOT NULL,
comment_postedtime DATETIME NOT NULL DEFAULT NOW(),
comment_parentid INT UNSIGNED
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;

DROP TABLE IF EXISTS relation_table;
CREATE TABLE IF NOT EXISTS relation_table(
relation_id INT UNSIGNED KEY AUTO_INCREMENT,
relation_main_userid INT UNSIGNED NOT NULL,
relation_sub_userid INT UNSIGNED NOT NULL,
relation_type INT UNSIGNED NOT NULL,
relation_createtime DATETIME NOT NULL DEFAULT NOW()
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;

DROP TABLE IF EXISTS coachauth_table;
CREATE TABLE IF NOT EXISTS coachauth_table(
coachauth_id    INT UNSIGNED KEY AUTO_INCREMENT,
coachauth_userid    INT UNSIGNED NOT NULL,
coachauth_status    INT UNSIGNED NOT NULL DEFAULT 0,
coachauth_name  VARCHAR(64) NOT NULL,
coachauth_idcardno  VARCHAR(64) NOT NULL,
coachauth_org   VARCHAR(64) NOT NULL,
coachauth_permitno    VARCHAR(64),
coachauth_snapshot  VARCHAR(64) NOT NULL,
coachauth_qualifications    VARCHAR(256) NOT NULL,
coachauth_posttime DATETIME DEFAULT NOW(),
coachauth_message VARCHAR(256)
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;

DROP TABLE IF EXISTS task_table;
CREATE TABLE IF NOT EXISTS task_table(
task_id INT UNSIGNED KEY AUTO_INCREMENT,
task_userid    INT UNSIGNED NOT NULL,
task_type   INT UNSIGNED NOT NULL,
task_finishtime DATETIME NOT NULL DEFAULT NOW()
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;

DROP TABLE IF EXISTS entry_table;
CREATE TABLE IF NOT EXISTS entry_table(
entry_id    INT UNSIGNED KEY AUTO_INCREMENT,
entry_parentid INT UNSIGNED,
entry_type  INT UNSIGNED NOT NULL,
entry_sortweight INT UNSIGNED NOT NULL DEFAULT 0,
entry_name_chs  VARCHAR(64) NOT NULL,
entry_name_eng  VARCHAR(64) NOT NULL,
entry_image VARCHAR(64) NOT NULL
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;
ALTER TABLE user_table ADD user_points INT UNSIGNED DEFAULT 0 AFTER user_huanchaouid;

DROP TABLE IF EXISTS schedule_table;
CREATE TABLE IF NOT EXISTS schedule_table(
schedule_id INT UNSIGNED KEY AUTO_INCREMENT,
schedule_name VARCHAR(64),
schedule_createtime DATETIME NOT NULL DEFAULT NOW(),
schedule_lessontime DATETIME,
schedule_coach_userid   INT UNSIGNED NOT NULL,
schedule_student_userid INT UNSIGNED,
schedule_status INT UNSIGNED NOT NULL DEFAULT 0,
schedule_deleteflag INT UNSIGNED NOT NULL DEFAULT 0
);

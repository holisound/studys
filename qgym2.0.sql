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

CREATE TABLE IF NOT EXISTS relation_table(
relation_id INT UNSIGNED KEY AUTO_INCREMENT,
relation_main_userid INT UNSIGNED NOT NULL,
relation_sub_userid INT UNSIGNED NOT NULL,
relation_type INT UNSIGNED NOT NULL
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;
-- [gallery]
-- photos grouped and ordered by upload-date desc

CREATE TABLE IF NOT EXISTS photo_table(
photo_id INT UNSIGNED KEY AUTO_INCREMENT,
photo_userid INT UNSIGNED NOT NULL,
photo_uuid CHAR(64) NOT NULL,
photo_uploadtime DATETIME DEFAULT NOW(),
photo_viewtimes INT UNSIGNED DEFAULT 0,
photo_stars INT UNSIGNED DEFAULT 0
)ENGINE=MyISAM DEFAULT CHARSET=UTF8;
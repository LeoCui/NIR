#! /usr/bin/env python
#################################################################################
#     File Name           :     test.py
#     Created By          :     Leo
#     Creation Date       :     [2017-11-03 20:10]
#     Last Modified       :     [2017-11-03 20:36]
#     Description         :      
#################################################################################
/*************************************************************************

	> File Name: test.py
	> Author: 
	> Mail: 
	> Created Time: Fri Nov  3 20:10:10 2017
 ************************************************************************/


CREATE TABLE news_info (
     id int(20) NOT NULL AUTO_INCREMENT,
     title varchar(255)  NOT NULL DEFAULT '',
     url varchar(255) NOT NULL DEFAULT '',
     pv int(20) NOT NULL DEFAULT 0,
     comment_number int(20) NOT NULL DEFAULT 0,
     publish_time timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
     create_time timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
     update_time timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
     PRIMARY KEY (id)
);

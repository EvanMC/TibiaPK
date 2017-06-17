CREATE DEFINER=`root`@`127.0.0.1` PROCEDURE `addDeath`(IN `p_name` VARCHAR(255), IN `p_date` DATETIME, IN `p_msg` VARCHAR(32766))
BEGIN
IF (select exists (select 1 from deaths where name = p_name and deathdate = p_date))
THEN
	select 'Death already added!';
ELSE
insert into deaths (
	name,
	deathdate,
    deathmessage
) values (
	p_name,
	p_date,
    p_msg
);
END IF;

END
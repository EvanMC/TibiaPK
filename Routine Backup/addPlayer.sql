CREATE DEFINER=`root`@`127.0.0.1` PROCEDURE `addPlayer`(IN `p_name` VARCHAR(255))
BEGIN
IF (select exists (select 1 from player where name = p_name))
THEN
	update player set lastlogin = NOW() where name = p_name;
ELSE
insert into player (
	name,
	lastlogin
) values (
	p_name,
	NOW()
);
END IF;

END
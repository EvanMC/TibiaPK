CREATE DEFINER=`root`@`127.0.0.1` PROCEDURE `removeOldPlayers`()
BEGIN
delete from player where lastlogin < (NOW() - interval 10 MINUTE);
END
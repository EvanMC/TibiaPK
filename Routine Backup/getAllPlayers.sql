CREATE DEFINER=`root`@`127.0.0.1` PROCEDURE `getAllPlayers`()
    READS SQL DATA
BEGIN
    select name from player; 
END
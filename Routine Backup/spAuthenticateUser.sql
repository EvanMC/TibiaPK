CREATE DEFINER=`root`@`127.0.0.1` PROCEDURE `sp_AuthenticateUser`(
IN p_username VARCHAR(20)
)
BEGIN

     select * from tblUser where UserName = p_username;

END
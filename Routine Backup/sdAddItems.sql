CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_AddItems`(
in p_userId int,
in p_item varchar(25)
)
BEGIN
    insert into tblItem(
        UserId,
        ItemName
    )
    values(
        p_userId,
        p_item
    );
END
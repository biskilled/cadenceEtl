truncate table dbo.Trans_Code_AUT_Full;

insert into dbo.Trans_Code_AUT_Full
(OriginalUnitID)
Select
distinct  OriginalUnitID
from BZ_ORG.dbo.Trans_Code;

-- , OriginalUnitName, UnitID, stID
-- , OriginalUnitName, UnitID, stID
Update dbo.Trans_Code_AUT_Full
Set OriginalUnitName = Trans.OriginalUnitName,
	UnitID = Trans.UnitID,
	stID = Trans.stID
From BZ_ORG.dbo.Trans_Code Trans
where Trans.OriginalUnitID = dbo.Trans_Code_AUT_Full.OriginalUnitID;


-- Delete trans_code rows that not in Expenses Model
Delete dbo.Trans_Code_AUT_Full
Where OriginalUnitID not in
(Select Distinct Y_Irgunit from V_Y_Irgunit_FACT_PAYMENTS3);

-- 663 - אוטומציה לא מקושר

Insert into dbo.Trans_Code_AUT_Full
(OriginalUnitID, OriginalUnitName,
 UnitID, stID)
Select distinct
convert (varchar (20) , Y_Irgunit),  'לא קיים תאור',
  663 , 1
FROM  dbo.DWH_FACT_PAYMENTS3
WHERE convert (varchar (20) , Y_Irgunit)
	not in
	(Select distinct OriginalUnitID from dbo.Trans_Code_AUT_Full)
    And DWH_FACT_PAYMENTS3.Mifal not in (670);

Insert into dbo.Trans_Code_AUT_Full
(OriginalUnitID, OriginalUnitName,
 UnitID, stID)
Select distinct
convert (varchar (20) , Department_No),  'לא קיים תאור',
  663 , 1
FROM  dbo.DWH_FACT_PAYMENTS3
WHERE convert (varchar (20) , Department_No)
	not in
	(Select distinct OriginalUnitID from dbo.Trans_Code_AUT_Full)
    And DWH_FACT_PAYMENTS3.Mifal  in (670);


update dbo.Trans_Code_AUT_Full
Set OriginalUnitName = isnull (Y_Irgunit_PIN,'לא קיים תאור')
From dbo.DWH_FACT_PAYMENTS3
Where convert (varchar (20) , DWH_FACT_PAYMENTS3.Y_Irgunit) = Trans_Code_AUT_Full.OriginalUnitID
And UnitID = 663
And DWH_FACT_PAYMENTS3.Mifal not in (670);

update dbo.Trans_Code_AUT_Full
Set OriginalUnitName = isnull (Department_Desc,'לא קיים תאור')
From dbo.DWH_FACT_PAYMENTS3
Where convert (varchar (20) , DWH_FACT_PAYMENTS3.Department_No) = Trans_Code_AUT_Full.OriginalUnitID
And UnitID = 663
And DWH_FACT_PAYMENTS3.Mifal in (670);




Truncate table OrgTree_NAMER_FULL;

Insert into OrgTree_NAMER_FULL
(ID, ItemName, ItemNameMed, ItemNameNurs, PID, iLevel, TASMC_Code,
 MABAR_Code, ItemTypeID, IndDistribute, IndAssignment, GateID,
 IsHidden, Shift, Gate, ItemNameMedMaz, ItemNameNursMaz, ItemNameNursMev)

Select
 ID, ItemName, ItemNameMed, ItemNameNurs, PID, iLevel, TASMC_Code,
 MABAR_Code, ItemTypeID, IndDistribute, IndAssignment, GateID,
 IsHidden, Shift, Gate, ItemNameMedMaz, ItemNameNursMaz, ItemNameNursMev
from dbo.v_Org_Tree;

/*
-- delete Members from organization tree that not connected to expenses model
delete OrgTree_NAMER_FULL
Where ID not in
(Select distinct UnitId from Trans_Code_NAMER_Full)
*/

Declare @Ounitid varchar (20), @Ounitname varchar (100) , @UnitID int
Declare @start int

-- 663 - אוטומציה לא מקושר
-- Update trance code which sdo not have 661 entries in ORG tree

Set @start = (select max(ID)+1 from OrgTree_NAMER_FULL)
declare LoadMissing cursor for
Select  OriginalUnitID, OriginalUnitName , UnitID
From dbo.Trans_Code_AUT_Full
Where UnitID = 663


Open LoadMissing
Fetch next from LoadMissing
Into @Ounitid,@Ounitname,@UnitID

While @@FETCH_STATUS = 0
BEGIN
	Update dbo.Trans_Code_AUT_Full
		Set UnitID = @start
	Where dbo.Trans_Code_AUT_Full.OriginalUnitID = @Ounitid
	And dbo.Trans_Code_AUT_Full.UnitID =662

	Insert into OrgTree_NAMER_FULL
	(ID, ItemName, ItemNameMed, ItemNameNurs, PID, iLevel, TASMC_Code,
	MABAR_Code, ItemTypeID, IndDistribute, IndAssignment, GateID,
	IsHidden, Shift, Gate, ItemNameMedMaz, ItemNameNursMaz, ItemNameNursMev)

	Select
	@start, @Ounitname,@Ounitname,@Ounitname,663,2,null,
	null,null,null,null,1,
	null,null,null,null,null,null
	Set @Start = @Start+1
	Fetch next from LoadMissing
	Into @Ounitid,@Ounitname,@UnitID
END

CLOSE LoadMissing
DEALLOCATE LoadMissing


-- 662 - הוצאות לא מקושר
-- 663 - אוטומציה לא מקושר


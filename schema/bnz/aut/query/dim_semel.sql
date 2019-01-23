truncate table dbo.STG_DIM_SEMEL;

Insert into STG_DIM_SEMEL ( mifal,  semel_code,  semel_mifal )
Select Distinct
mifal , semel_code , mifal*10000+semel_code As semel_mifal
from dbo.DWH_FACT_PAYMENTS3;

Update dbo.STG_DIM_SEMEL
Set
	mifal_name	= isnull (f.mifal_name,'לא ידוע' ),
	semel_desc	= isnull (f.semel_desc, 'לא ידוע' ),
	semel_seif	= isnull (f.semel_seif, -999 ),
	Semel_F_Name= convert (varchar (10), f.semel_code) + ' - ' +
					replace ( replace (f.semel_desc , '"' , '') , '''' , '' )
From DWH_FACT_PAYMENTS3 F
Where F.mifal = STG_DIM_SEMEL.mifal And F.semel_code = STG_DIM_SEMEL.semel_code
AND exists
(Select Max (period) As period,mifal, semel_code
 From DWH_FACT_PAYMENTS3 P
 Where	Isnull(P.semel_desc,'') <> '' AND
		P.semel_code	= f.semel_code AND
		P.mifal			= f.mifal AND
		P.period		= f.period
 Group by mifal, semel_code);


delete from DWH_DIM_SEMEL
Where exists
(Select 1 from STG_DIM_SEMEL D
 Where D.mifal = mifal And D.semel_code = semel_code);

Insert into DWH_DIM_SEMEL
Select * from STG_DIM_SEMEL;

/* Test By Tal Shany - 2013 - 08 -25
Select * from DWH_DIM_SEMEL
order by mifal, semel_Code

Select Distinct Mifal,semel_Code, Semel_desc,ID
From DWH_FACT_PAYMENTS3
Where Period = 201307 And semel_code = 4
order by Mifal, ID

Select Distinct Mifal,semel_Code, Semel_desc,ID
From DWH_FACT_PAYMENTS3
Where Period = 201307 And semel_code = 4  And ID = 1190782
order by Mifal, ID

Select Distinct Type,Period,MIfal,semel_code,semel_desc
From DWH_FACT_PAYMENTS3
Where  semel_code = 872  And ID = 1190782 --Period = 201307 And
--order by Mifal, ID


*/

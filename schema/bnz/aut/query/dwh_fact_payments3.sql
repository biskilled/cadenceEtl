-- Tal: 2016/05/23 - U[date seifim by this temp table
if object_id ('#seifim') is not null
	Drop table #seifim

Create table #seifim (
	seifNum int,
	seifHours float,
	seifDefault float
)

Insert into #seifim Select 211,null,1
Insert into #seifim Select 214,null,1
Insert into #seifim Select 234,null,1
Insert into #seifim Select 266,null,1
Insert into #seifim Select 267,null,1
Insert into #seifim Select 270,null,1
Insert into #seifim Select 286,null,1
Insert into #seifim Select 311,null,1
Insert into #seifim Select 318,null,1
Insert into #seifim Select 319,10.7,1
Insert into #seifim Select 320,10.7,1
Insert into #seifim Select 405,null,1

Update STG_FACT_PAYMENTS3
Set Y_Irgunit = V.Y_Irgunit,
	Y_Irgunit_PIN = V.Y_Irgunit_PIN
From V_Y_Irgunit V
Where	STG_FACT_PAYMENTS3.Period = V.Period And
		STG_FACT_PAYMENTS3.Mifal  = V.Mifal  And
		STG_FACT_PAYMENTS3.ID	   = V.ID And
		STG_FACT_PAYMENTS3.Y_Irgunit is null

update STG_FACT_PAYMENTS3
Set Y_Irgunit = -999,
	Y_Irgunit_PIN = 'לא ידוע'
Where Y_Irgunit is null

-- Tal, 2015-05-23: Update kamut by sefim listed above
Update STG_FACT_PAYMENTS3
Set kamut_Konenot =
	case when seif.seifHours is null then isnull (seif.seifDefault,1) else Kamut/seif.seifHours end
From #seifim seif
Where STG_FACT_PAYMENTS3.semel_code = seif.seifNum;

Delete from DWH_FACT_PAYMENTS3
Where exists
(Select * from STG_FACT_PAYMENTS3
where DWH_FACT_PAYMENTS3.PERIOD = STG_FACT_PAYMENTS3.PERIOD And
	DWH_FACT_PAYMENTS3.Mifal = STG_FACT_PAYMENTS3.Mifal And
	 DWH_FACT_PAYMENTS3.[ID]=STG_FACT_PAYMENTS3.[ID] And
	 DWH_FACT_PAYMENTS3.[SEMEL_CODE]= STG_FACT_PAYMENTS3.[SEMEL_CODE]);

Insert into DWH_FACT_PAYMENTS3
Select * from STG_FACT_PAYMENTS3;

Delete from dbo.DWH_FACT_PAYMENTS3
Where Period < 200300;
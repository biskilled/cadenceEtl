Truncate table STG_DIM_DEPARTMENTS;

Insert into STG_DIM_DEPARTMENTS
(RASHUT_CODE, MIFAL, MIFAL_NAME, [ID], ENAME,
 DEPARTMENT_NO, DEPARTMENT_DESC, R_MONE_3, MIFAL_ID_DEPARTMENT_DESC,
 DEPARTMENT_NO2 , DEPARTMENT_DESC2)

Select Distinct
	RASHUT_CODE,
	MIFAL,
	case when MIFAL = 404 then 'בי"ח בני ציון'
	     When MIFAL = 670 then 'קרן מחקרים בי"ח בני ציון'
	Else 'לא ידוע'
 	End As MIFAL_NAME,
	[ID],
	null,
	DEPARTMENT_NO,
	DEPARTMENT_DESC,
	Null,
	Convert (varchar (10) , Isnull(MIFAL,-999))+'-'+
	Convert (varchar (10) , Isnull (Department_no, -999))+'-'+
	Ltrim(Rtrim(Isnull (DEPARTMENT_DESC,'לא ידוע'))) +'-'+
	ltrim(rtrim(Convert (varchar (10) , Isnull([ID],-999)))),
	-999,'לא ידוע'
From dbo.STG_FACT_PAYMENTS3;


Update  STG_DIM_DEPARTMENTS
	set ENAME = isnull (ltrim(rtrim(STG_FACT_PAYMENTS.ENAME)),'לא ידוע')
From dbo.STG_FACT_PAYMENTS
Where dbo.STG_FACT_PAYMENTS.MIFAL = STG_DIM_DEPARTMENTS.MIFAL And
	dbo.STG_FACT_PAYMENTS.Department_no = STG_DIM_DEPARTMENTS.Department_no And
	dbo.STG_FACT_PAYMENTS.DEPARTMENT_DESC = STG_DIM_DEPARTMENTS.DEPARTMENT_DESC And
	dbo.STG_FACT_PAYMENTS.[ID] = STG_DIM_DEPARTMENTS.[ID];

-- update department2
Update STG_DIM_DEPARTMENTS
Set DEPARTMENT_NO2 = PAN_Y_IRGUNIT,
	DEPARTMENT_DESC2 = PAN_Y_IRGUNIT_TEUR
from dbo.AUT_M_OVED
Where STG_DIM_DEPARTMENTS.[ID] = dbo.AUT_M_OVED.OVED_TZ And
	STG_DIM_DEPARTMENTS.department_no = dbo.AUT_M_OVED.seif_takzivi_rashi_code;

Insert into DWH_DIM_DEPARTMENTS
Select * from STG_DIM_DEPARTMENTS
Where STG_DIM_DEPARTMENTS.MIFAL_ID_DEPARTMENT_DESC NOT IN
(Select Distinct MIFAL_ID_DEPARTMENT_DESC
 From DWH_DIM_DEPARTMENTS);

Insert into DWH_DIM_DEPARTMENTS
Select Distinct
	RASHUT_CODE,
	MIFAL,
	case when MIFAL = 404 then 'בי"ח בני ציון'
	     When MIFAL = 670 then 'קרן מחקרים בי"ח בני ציון'
	Else 'לא ידוע'
 	End As MIFAL_NAME,
	[ID],
	null,
	DEPARTMENT_NO,
	DEPARTMENT_DESC,
	Null,
	Convert (varchar (10) , Isnull(MIFAL,-999))+'-'+
	Convert (varchar (10) , Isnull (Department_no, -999))+'-'+
	Ltrim(Rtrim(Isnull (DEPARTMENT_DESC,'לא ידוע'))) +'-'+
	ltrim(rtrim(Convert (varchar (10) , Isnull([ID],-999)))),
	-999,'לא ידוע'
From DWH_Automation
Where MIFAL_ID_DEPARTMENT_DESC not in
(Select distinct MIFAL_ID_DEPARTMENT_DESC from DWH_DIM_DEPARTMENTS);
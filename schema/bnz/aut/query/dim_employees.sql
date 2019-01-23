Update dbo.STG_FACT_PAYMENTS3
Set M_Oved_Code =
	convert (varchar (20),[ID]) +'-'+convert (varchar (20),MIFAL);


truncate table STG_DIM_Employee;

Insert into STG_DIM_Employee
(M_Oved_Code,M_OVED, MIFAL, MIFAL_PIN, RASHUT_CODE, RASHUT_PIN,
 MAHLAKA, MAHLAKA_PIN, R_MISHPAHA, R_PRATI, R_ISHUV, R_KTOVET,
 MAZAV_MISHPAHTI, MAZAV_PIN, TAAR_LEDA,
 TAAR_TH_AVODA, SEMEL_ISUK, ISUK_PIN, Y_IRGUNIT,
 Y_IRGUNIT_PIN, SUM_AHUZ_MISRA, T_MASKORET, DERUG,
 DERUG_PIN, DARGA, DARGA_PIN,
 RAMA, RAMA_PIN, TZ_MALE)

Select convert (varchar (20),M_OVED) +'-'+convert (varchar (20),MIFAL),
 M_OVED, MIFAL, isnull (MIFAL_PIN,'לא ידוע'), RASHUT_CODE, isnull (RASHUT_PIN,'לא ידוע'),
 MAHLAKA, isnull (MAHLAKA_PIN,'לא ידוע'), ltrim(rtrim(R_MISHPAHA)), ltrim(rtrim(R_PRATI)), R_ISHUV, R_KTOVET,
 MAZAV_MISHPAHTI, isnull (MAZAV_PIN,'לא ידוע'), TAAR_LEDA,
 TAAR_TH_AVODA, SEMEL_ISUK, isnull (ISUK_PIN,'לא ידוע'), Y_IRGUNIT,
 isnull (Y_IRGUNIT_PIN,'לא ידוע'), SUM_AHUZ_MISRA, T_MASKORET, DERUG,
 isnull (DERUG_PIN,'לא ידוע'), DARGA, isnull (DARGA_PIN,'לא ידוע'),
 RAMA, RAMA_PIN, TZ_MALE
From AUT_SACHAR_OVED A
Where PERIOD_LAST=
(Select max (PERIOD_LAST) from AUT_SACHAR_OVED
 Where mifal = A.mifal And
	   M_OVED = A.M_OVED);

Update dbo.STG_DIM_Employee
Set R_PRATI = STG_DIM_Employee_HELP.R_PRATI,
	R_MISHPAHA = STG_DIM_Employee_HELP.R_MISHPAHA
	--ENAME = STG_DIM_Employee_HELP.EName
From STG_DIM_Employee_HELP
Where
	dbo.STG_DIM_Employee.M_Oved_Code = STG_DIM_Employee_HELP.M_Oved_Code;

Update STG_DIM_Employee
Set R_Mishpaha = v.R_Mishpaha,
	R_Prati  = v.R_Prati
From V_HELP_STG_DIM_Employee_UnicNames V
Where v.M_OVed = STG_DIM_Employee.M_OVed;


Delete DWH_DIM_Employee
From STG_DIM_Employee
Where DWH_DIM_Employee.mifal=STG_DIM_Employee.mifal And
	DWH_DIM_Employee.M_OVED = STG_DIM_Employee.M_OVED;

Insert into DWH_DIM_Employee
Select distinct * from STG_DIM_Employee;

Insert into DWH_DIM_Employee
(M_Oved_Code,
 M_OVED, MIFAL, MIFAL_PIN, RASHUT_CODE, RASHUT_PIN, MAHLAKA, MAHLAKA_PIN,
 R_MISHPAHA, R_PRATI, R_ISHUV, R_KTOVET,
 MAZAV_MISHPAHTI, MAZAV_PIN,
 TAAR_LEDA, TAAR_TH_AVODA, SEMEL_ISUK, ISUK_PIN,
 Y_IRGUNIT, Y_IRGUNIT_PIN, SUM_AHUZ_MISRA, T_MASKORET,
 DERUG, DERUG_PIN,
 DARGA, DARGA_PIN,
 RAMA, RAMA_PIN, TZ_MALE)

Select distinct
convert (varchar (20),[ID]) +'-'+convert (varchar (20),MIFAL),
[ID] , MIFAL,MIFAL_NAME, RASHUT_CODE, RASHUT_PIN,DEPARTMENT_NO, DEPARTMENT_DESC,
L_Name, F_Name, 'לא ידוע', 'לא ידוע',
-99 , 'לא ידוע',
'1900-01-01 00:00:00.000','1900-01-01 00:00:00.000',-99, 'לא ידוע',
Y_IRGUNIT,Y_IRGUNIT_PIN,0,Null,
-99, 'לא ידוע',
-99, 'לא ידוע',
0,NUll, [ID]
From dbo.DWH_FACT_PAYMENTS3
Where Not exists
(Select 1 from DWH_DIM_Employee
 Where DWH_DIM_Employee.M_Oved = DWH_FACT_PAYMENTS3.ID and
	   DWH_DIM_Employee.MIfal = DWH_FACT_PAYMENTS3.Mifal);


Delete from DWH_DIM_Employee
Where Not exists
(Select 1 from DWH_FACT_PAYMENTS3
 Where DWH_DIM_Employee.M_Oved = DWH_FACT_PAYMENTS3.ID and
	   DWH_DIM_Employee.MIfal = DWH_FACT_PAYMENTS3.Mifal);
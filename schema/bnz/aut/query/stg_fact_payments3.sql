Truncate table dbo.STG_FACT_PAYMENTS3;

Insert into dbo.STG_FACT_PAYMENTS3
(TYPE, PERIOD, MIFAL, [ID], TOTAL_PAYS, AUTO_DED, PER_DED,
 ALUT_MAAVID,
 SEMEL_CODE,
 SEMEL_CODE_VC, SEMEL_DESC,
 DEPARTMENT_NO, DEPARTMENT_DESC,
 F_Name, L_Name, ENAME,
 MIFAL_NAME, RASHUT_CODE,
 Achuz,Kamut,kamut_Konenot)

Select
'T',period,mifal,[M_oved],schum_66,0,0,
schum_alut_maavid,
case when isnull (semel,-99) = 0
	then -99
ELSE isnull (semel,-99)
End ,
convert (varchar (30) ,
	case when isnull (semel,-99)= 0
		then -99
	Else isnull (semel,-99)
	end) ,
isnull (semel_PIN,'עלויות נוספות'),
Convert (numeric (28,0) , Mahlaka_1), mahlaka_pin,
'לא ידוע', 'לא ידוע','לא ידוע',
null,rashut_code,
Achuz , Kamut, kamut
From dbo.AUT_SACHAR_TASHLUM_COLEL;

Update dbo.STG_FACT_PAYMENTS3
Set  F_Name = ltrim(rtrim(prati)),
	 L_Name = ltrim(rtrim(mishpaha)),
	 ENAME  = ltrim(rtrim(mishpaha)) + '-'+ltrim(rtrim(prati))
From dbo.AUT_SACHAR_66_TASHLUM
Where dbo.STG_FACT_PAYMENTS3.[ID] = dbo.AUT_SACHAR_66_TASHLUM.[M_oved];

/* --------------------------------------  */
Update dbo.STG_FACT_PAYMENTS3
Set  DEPARTMENT_NO = Convert (numeric (28,0) , Mahlaka),
	 DEPARTMENT_DESC = mahlaka_pin
From dbo.AUT_SACHAR_66_TASHLUM
Where dbo.STG_FACT_PAYMENTS3.[ID] = dbo.AUT_SACHAR_66_TASHLUM.[M_oved]
And DEPARTMENT_NO = 0 Or DEPARTMENT_NO is null;

-- Changed by Tal Shany, 021007
--dbo.AUT_SACHAR_66_TASHLUM


Insert into dbo.STG_FACT_PAYMENTS3
(TYPE, PERIOD, MIFAL, [ID], TOTAL_PAYS, AUTO_DED, PER_DED,
 ALUT_MAAVID, SEMEL_CODE, SEMEL_CODE_VC, SEMEL_DESC,
 DEPARTMENT_NO, DEPARTMENT_DESC,
 F_Name, L_Name, ENAME,
 PERIODD, MIFAL_NAME, RASHUT_CODE,
 Achuz,Kamut, Kamut_Konenot)
Select
'N',PERIOD, MIFAL, zehut, 0,0,Schum_nikui*-1,
0, Isnull (semel, -9999) , convert (varchar (30) , Isnull (semel, -9999)) ,Isnull (Semel_pin, 'עלויות נוספות' ),
mahlaka,mahlaka_pin,
ltrim(rtrim(R_prati)), ltrim(rtrim(R_mishpaha)) , ltrim(rtrim(R_mishpaha)) + '-'+ltrim(rtrim(R_prati)),
T_Maskoret,null,rashut_code,
Achuz,Kamut, Kamut
From dbo.AUT_SACHAR_NECUI;

Insert into dbo.STG_FACT_PAYMENTS3
(TYPE, PERIOD, MIFAL, [ID], TOTAL_PAYS, AUTO_DED, PER_DED,
 ALUT_MAAVID, SEMEL_CODE, SEMEL_CODE_VC, SEMEL_DESC,
 DEPARTMENT_NO, DEPARTMENT_DESC,
 F_Name, L_Name, ENAME,
 PERIODD, MIFAL_NAME, RASHUT_CODE)
Select
'N_MH',PERIOD, MIFAL, M_OVED, 0,Nikui_Mas*-1,0,
0, Isnull (semel_Mas, -9999) , convert (varchar (30) , Isnull (semel_MAS, -9999)) ,Isnull (Semel_pin, 'לא ידוע' )+' -מס הכנסה',
null,null,
ltrim(rtrim(R_prati)), ltrim(rtrim(R_mishpaha)) , ltrim(rtrim(R_mishpaha)) + '-'+ltrim(rtrim(R_prati)),
T_Maskoret,null,rashut_code
From dbo.AUT_SACHAR_M_HACNASA
Where T_Maskoret > dateadd (month , -12, getdate());

Insert into dbo.STG_FACT_PAYMENTS3
(TYPE, PERIOD, MIFAL, MIFAL_NAME, [ID], TOTAL_PAYS, AUTO_DED, PER_DED,
 ALUT_MAAVID, SEMEL_CODE, SEMEL_CODE_VC, SEMEL_DESC,
DEPARTMENT_NO, DEPARTMENT_DESC,
F_Name, L_Name, ENAME,
PERIODD, RASHUT_CODE, RASHUT_PIN,
--SEIF, SEIF_AMITI, SEIF_TEUR, SEMEL_KG, SEMEL_KG_PIN,
Y_IRGUNIT, Y_IRGUNIT_PIN)

Select
'T_N',av.period,av.mifal,av.MIFAL_PIN,av.[M_oved],0,av.nikuiim*-1 - isnull (nk.total_ded,0),0,
0,-999 ,'-999' , 'ניכויים נוספים' ,
Convert (numeric (28,0) , av.Mahlaka), av.mahlaka_pin,
ltrim(rtrim(av.R_prati)),  ltrim(rtrim(av.R_mishpaha)), ltrim(rtrim(av.R_mishpaha)) + '-'+ltrim(rtrim(av.R_prati)),
av.T_Maskoret,av.rashut_code,av.Rashut_PIN,
av.Y_IRGUNIT,av.Y_IRGUNIT_PIN
From dbo.AUT_SACHAR_AV As av,
	dbo.V_STG_NIKUY_NEW as nk
Where 	av.period  = nk.period  and av.M_OVED = nk.[ID]
	and av.mifal = nk.mifal
	and (av.nikuiim*-1 - isnull (nk.total_ded,0)) < 0.01;

Update dbo.STG_FACT_PAYMENTS3
Set
	SEIF = ma.SEIF,
	SEIF_AMITI = ma.SEIF_AMITI,
	SEIF_TEUR =  ma.SEIF_TEUR,
	SEMEL_KG = ma.SEMEL_KG,
	SEMEL_KG_PIN = ma.SEMEL_KG_PIN

From
dbo.AUT_SACHAR_66_ALUT_MAAVID As ma
Where ma.mifal = dbo.STG_FACT_PAYMENTS3.mifal and
	ma.m_oved = dbo.STG_FACT_PAYMENTS3.[ID] and
	ma.period = dbo.STG_FACT_PAYMENTS3.period AND
	ma.semel = dbo.STG_FACT_PAYMENTS3.semel_CODE;

Update dbo.STG_FACT_PAYMENTS3
Set
	MIFAL_NAME = ma.mifal_PIN,
	RASHUT_PIN = ma.Rashut_pin,
	Y_IRGUNIT =  ma.Y_IRGUNIT,
	Y_IRGUNIT_PIN = ma.Y_IRGUNIT_PIN

From
dbo.AUT_SACHAR_AV As ma
Where ma.mifal = dbo.STG_FACT_PAYMENTS3.mifal and
	ma.M_OVED = dbo.STG_FACT_PAYMENTS3.[ID] and
	ma.period = dbo.STG_FACT_PAYMENTS3.period;

-- update Y_Irgunit = 0
update dbo.STG_FACT_PAYMENTS3
Set Y_Irgunit_Pin = 'לא ידוע'
Where Y_irgunit = 0;

-- Update Mifal Names
Update dbo.STG_FACT_PAYMENTS3
Set mifal_name = 'מדינה'
Where mifal = 404;

Update dbo.STG_FACT_PAYMENTS3
Set mifal_name = 'קרן'
Where mifal = 670;

Update dbo.STG_FACT_PAYMENTS3
Set  DEPARTMENT_NO= DWH_F.DEPARTMENT_NO,
	 DEPARTMENT_DESC = DWH_F.DEPARTMENT_DESC
From
	(Select distinct
		period,mifal,id,department_no,department_desc
		from dbo.STG_FACT_PAYMENTS3
		Where department_no is not null and
			  department_desc is not null) as DWH_F
Where
(dbo.STG_FACT_PAYMENTS3.DEPARTMENT_NO is null OR
 dbo.STG_FACT_PAYMENTS3.DEPARTMENT_DESC is null OR
 dbo.STG_FACT_PAYMENTS3.DEPARTMENT_DESC='') And
	--dbo.STG_FACT_PAYMENTS3.PERIOD = DWH_F.PERIOD And
	dbo.STG_FACT_PAYMENTS3.MIFAL = DWH_F.MIFAL And
	dbo.STG_FACT_PAYMENTS3.ID = DWH_F.[ID];


Update dbo.STG_FACT_PAYMENTS3
Set  DEPARTMENT_NO= -99,
	 DEPARTMENT_DESC = 'לא מוגדר'
Where DEPARTMENT_NO is null;

-- New version, made by Tal Shany, 01-09-2009

truncate table [dbo].[STG_DIM_Employee_HELP];

Insert into [dbo].[STG_DIM_Employee_HELP]
(M_Oved_Code ,  M_OVED , PERIOD, MIFAL,MIFAL_PIN,
 R_MISHPAHA, R_PRATI,ENAME)
Select Distinct M_Oved_Code,  ID, max (Period),MIFAL,LTRIM(RTRIM(MIFAL_NAME)),
				'לא ידוע', 'לא ידוע', '-99 - לא ידוע'
FROM  dbo.STG_FACT_PAYMENTS3
Group by M_Oved_Code, ID,MIFAL,LTRIM(RTRIM(MIFAL_NAME));

Update [dbo].[STG_DIM_Employee_HELP]
Set R_MISHPAHA = fact.L_Name,
	R_PRATI = fact.F_Name,
	ENAME = fact.ENAME
From dbo.STG_FACT_PAYMENTS3 fact
WHERE
	(fact.ENAME IS NOT NULL) and fact.ENAME not like '%לא ידוע%' And
	fact.M_Oved_Code = STG_DIM_Employee_HELP.M_Oved_Code And
	fact.Period = STG_DIM_Employee_HELP.Period;

Update [dbo].[STG_DIM_Employee_HELP]
Set R_MISHPAHA = ltrim(rtrim(av.R_mishpaha)),
	R_PRATI = ltrim(rtrim(av.R_prati)),
	ENAME = ltrim(rtrim(av.R_mishpaha)) + '-'+ltrim(rtrim(av.R_prati))
FROM  dbo.AUT_SACHAR_AV av
WHERE
	av.R_mishpaha IS NOT NULL and
	STG_DIM_Employee_HELP.ENAME like '%לא ידוע%' And
	av.M_Oved  = STG_DIM_Employee_HELP.M_Oved And
	av.MIFAL  = STG_DIM_Employee_HELP.MIFAL And
	av.Period = STG_DIM_Employee_HELP.Period;

-- OlD version -----
/*
Update dbo.STG_FACT_PAYMENTS3
Set F_Name = V_STG_Employee.F_Name,
	L_Name = V_STG_Employee.L_Name,
	ENAME = V_STG_Employee.EName
From V_STG_Employee
Where
	dbo.STG_FACT_PAYMENTS3.ENAME = '' OR dbo.STG_FACT_PAYMENTS3.ENAME is null
	AND
	dbo.STG_FACT_PAYMENTS3.ID = V_STG_Employee.ID
*/

------------- NEW VERSION, made by Tal Shany, 01-09-2009


Update dbo.STG_FACT_PAYMENTS3
Set F_Name = STG_DIM_Employee_HELP.R_PRATI,
	L_Name = STG_DIM_Employee_HELP.R_MISHPAHA,
	ENAME = STG_DIM_Employee_HELP.EName
From STG_DIM_Employee_HELP
Where
	dbo.STG_FACT_PAYMENTS3.M_Oved_Code = STG_DIM_Employee_HELP.M_Oved_Code;

------------------------------------------------------------------
---       OLD version !!!

Update dbo.STG_FACT_PAYMENTS3
Set  F_NAME= dbo.V_STG_Employee_Dis_ID.F_NAME,
	 L_NAME = dbo.V_STG_Employee_Dis_ID.L_NAME,
	 ENAME = dbo.V_STG_Employee_Dis_ID.ENAME
From
	dbo.V_STG_Employee_Dis_ID
Where
	dbo.STG_FACT_PAYMENTS3.ID = dbo.V_STG_Employee_Dis_ID.ID;

-- Added by Tal Shany, 24-03-2008

Update dbo.STG_FACT_PAYMENTS3
Set Pail_Code = -1 ,
	Pail_Desc = 'לא ידוע';

Update dbo.STG_FACT_PAYMENTS3
Set Pail_code = Moved.pail_code,
    Pail_Desc = Moved.pail_teur
From dbo.AUT_M_OVED2 as Moved
Where Moved.oved_tz = dbo.STG_FACT_PAYMENTS3.ID;

Update dbo.STG_FACT_PAYMENTS3
Set MIFAL_ID_DEPARTMENT_DESC =
	Convert (varchar (10) , Isnull(MIFAL,-999))+'-'+
	Convert (varchar (10) , Isnull (Department_no, -999))+'-'+
	ltrim(rtrim(Convert (varchar (10) , Isnull([ID],-999))));

Update dbo.STG_FACT_PAYMENTS3
Set MIFAL_ID_Y_IRGUNIT=
	Convert (varchar (10) , Isnull(MIFAL,-999))+'-'+
	Convert (varchar (10) , Isnull (Y_IRGUNIT, -999))+'-'+
	ltrim(rtrim(Convert (varchar (10) , Isnull([ID],-999))));

Update STG_FACT_PAYMENTS3
Set Mifal_Name = replace (Mifal_Name , '"' , '');

Update STG_FACT_PAYMENTS3
Set Mifal_Name = replace (Mifal_Name , '''' , '');

/*
 Update dbo.DWH_FACT_PAYMENTS3_ALUT_MAAVID
Set Mifal_Name = replace (Mifal_Name , '"' , '')

Update dbo.DWH_FACT_PAYMENTS3_ALUT_MAAVID
Set Mifal_Name = replace (Mifal_Name , '''' , '')
*/

Update dbo.STG_FACT_PAYMENTS3
Set Semel_Seif = a.seif
From aut_sachar_66_tashlum a
Where a.seif <> 0 And
	STG_FACT_PAYMENTS3.mifal = a.mifal and
	STG_FACT_PAYMENTS3.semel_code = a.semel and
	a.period =
	(Select max (period) from
	 aut_sachar_66_tashlum B
	 Where B.mifal = a.mifal and B.semel = a.semel);
Truncate table STG_DIM_Employee_Full;

INSERT into STG_DIM_Employee_Full
(Employees_Code,
 Period, M_Oved_Code, M_OVED, MIFAL,
 MIFAL_PIN,
 RASHUT_CODE, RASHUT_PIN,
 /* MAHLAKA, MAHLAKA_PIN, */
 R_MISHPAHA, R_PRATI, R_ISHUV, R_KTOVET, MAZAV_MISHPAHTI,
 MAZAV_PIN, TAAR_LEDA, TAAR_TH_AVODA,
 SEMEL_ISUK, ISUK_PIN,
 Y_IRGUNIT, /*Y_IRGUNIT_PIN, */
 /*SUM_AHUZ_MISRA,*/ T_MASKORET, DERUG, DERUG_PIN,
 DARGA, DARGA_PIN, RAMA, RAMA_PIN, TZ_MALE,
 Y_IRGUNIT_VC, Y_IRGUNIT_BZ,
 Pail_Code, Pail_Desc,
 sector_num, sector_name)

SELECT distinct
'PER:'+convert (varchar (15),period) + '-'+
'ID:' +convert (varchar (15),ID) + '-'+
'MIF:'+convert (varchar (10),Mifal) + '-'+
--'DEP:'+convert (varchar (30),isnull (Department_no,-999)) + '-'+
'IRG:'+convert (varchar (30),isnull (Y_Irgunit, -999)),
period,Convert (varchar (20), [ID])+ '-'+ convert (varchar (10),Mifal)  As M_Oved_Code , [ID] , Mifal,
'לא ידוע',
'-999','לא ידוע',
/*isnull (Department_no,'-999') , isnull (Department_desc, 'לא ידוע'),*/
'לא ידוע' ,'לא ידוע','לא ידוע','לא ידוע',
-999,'לא ידוע',  Null , Null,
0, 'לא ידוע' ,
isnull (Y_Irgunit, -999) , /*Isnull (Y_Irgunit_PIN, 'לא ידוע'),*/
/*Achuz,*/ Null,-999,'לא ידוע',
'-999',-999,'-999',-999,Null,
Convert (varchar (30) , isnull (Y_Irgunit, -999)),'לא ידוע' ,
-1,'לא ידוע',
-999 , 'ללא סקטור'
FROM dbo.DWH_FACT_PAYMENTS3;

Update STG_DIM_Employee_Full
Set
	Mifal_Pin = dim.mifal_pin,
	Rashut_Code = dim.rashut_Code,
	Rashut_PIN = dim.rashut_PIN,
	MAHLAKA		= dim.Mahlaka,
	Mahlaka_PIN = dim.Mahlaka_PIN,
	R_Mishpaha = dim.R_Mishpaha,
	R_Prati = dim.R_Prati,
	R_IShuv = dim.R_Ishuv,
	R_Ktovet = dim.R_Ktovet,
	Mazav_Mishpahti = dim.Mazav_Mishpahti,
	Mazav_PIN = dim.Mazav_PIN,
	Taar_Leda = dim.Taar_Leda,
	Taar_Th_Avoda = dim.Taar_Th_Avoda,
	SEMEL_ISUK = dim.SEMEL_ISUK,
	ISUK_PIN = dim.ISUK_PIN,
	Y_IRGUNIT_PIN = dim.Y_IRGUNIT_PIN,
	Y_IRGUNIT_BZ  = dim.Y_IRGUNIT_PIN,
	SUM_AHUZ_MISRA = dim.SUM_AHUZ_MISRA,
	T_MASKORET = dim.T_MASKORET,
	DERUG = dim.DERUG,
	DERUG_PIN = dim.DERUG_PIN,
	DARGA = dim.DARGA,
	DARGA_PIN = dim.DARGA_PIN,
	RAMA = dim.RAMA,
	RAMA_PIN = dim.RAMA_PIN,
	TZ_MALE = dim.TZ_MALE,
	--Y_IRGUNIT_BZ = dim.Y_IRGUNIT_BZ,
	--Pail_Code = dim.Pail_Code,
	--Pail_Desc = dim.Pail_Desc,
	--sector_num = dim.sector_num,
	--sector_name = dim.sector_name,
	Achuz_Misra_Is_Empty = case when dim.SUM_AHUZ_MISRA is null then 'ללא אחוזי משרה'
								Else 'עם אחוזי משרה'
					       End
From dbo.DWH_DIM_Employee dim
Where
	dim.M_Oved_Code = STG_DIM_Employee_Full.M_Oved_Code;

Update STG_DIM_Employee_Full
Set
	--Y_IRGUNIT = isnull (Y_Irgunit, -999),
	Y_IRGUNIT_PIN = Pay.Y_IRGUNIT_PIN,
	Y_IRGUNIT_BZ = Pay.Y_IRGUNIT_PIN,
	--Mahlaka = isnull (Department_no,'-999'),
	Mahlaka_PIN = Pay.Department_Desc
From dbo.DWH_FACT_PAYMENTS3 Pay
Where
	STG_DIM_Employee_Full.Period = Pay.period And
	STG_DIM_Employee_Full.M_Oved = Pay.ID And
	STG_DIM_Employee_Full.Mifal = Pay.Mifal
	And Pay.Y_IRGUNIT_PIN is not null;

--Select top 10 * from 	dbo.DWH_FACT_PAYMENTS3

Update STG_DIM_Employee_Full
Set
	Pail_Code = 0,
	Pail_Desc = 'פעיל'
From  dbo.AUT_SACHAR_AV Av
Where
	STG_DIM_Employee_Full.Period = Av.period And
	STG_DIM_Employee_Full.M_Oved = Av.M_Oved And
	STG_DIM_Employee_Full.Mifal = Av.Mifal And
	(Av.Bruto is not null or Av.Bruto <> 0);

Update STG_DIM_Employee_Full
Set
	Pail_Code = 9,
	Pail_Desc = 'לא פעיל'
From  dbo.AUT_SACHAR_AV Av
Where
	STG_DIM_Employee_Full.Period = Av.period And
	STG_DIM_Employee_Full.M_Oved = Av.M_Oved And
	STG_DIM_Employee_Full.Mifal = Av.Mifal And
	(Av.Bruto is null or convert (float,Av.Bruto) = 0.0);


Update STG_DIM_Employee_Full
Set Y_IRGUNIT_BZ = dbo.BZ_PROD_hrotoorgdept.org_deptnamebz
FROM
	BZ_PROD_hrotoorgdept
Where
	Y_IRGUNIT = CONVERT(int, dbo.BZ_PROD_hrotoorgdept.org_deptnum) and
	(dbo.BZ_PROD_hrotoorgdept.org_deptnamebz is not null  or BZ_PROD_hrotoorgdept.org_deptnamebz <> '');

Update STG_DIM_Employee_Full
Set
	Sector_Num = Sec.Sector_Num,
	Sector_Name = Sec.Sector_Name
From dbo.BZion_Prod_Sectors Sec
Where
	Sec.id_num = M_Oved;
truncate table DWH_DIM_Y_IRGUNIT;

Insert into DWH_DIM_Y_IRGUNIT
(Y_IRGUNIT , Y_Irgunit_PIN)
Select distinct isnull (Y_Irgunit , -99) , 'מדינה - לא ידוע'
from dbo.DWH_FACT_PAYMENTS3
Where Mifal not in (670);

Update DWH_DIM_Y_IRGUNIT
Set Y_IRGUNIT_PIN = isnull (f.Y_Irgunit_PIN  ,'לא ידוע')
from DWH_FACT_PAYMENTS3 f
Where f.Y_Irgunit = DWH_DIM_Y_IRGUNIT.Y_Irgunit And f.Mifal not in (670)
And exists
(Select Max (period) As period,Y_Irgunit, Y_Irgunit_PIN
 From DWH_FACT_PAYMENTS3 P
 Where P.Y_Irgunit_PIN is not null and P.Mifal not in (670)
 And P.Y_Irgunit = f.Y_Irgunit And P.period = f.period
 Group by Y_Irgunit, Y_Irgunit_PIN);

Insert into DWH_DIM_Y_IRGUNIT
(Y_IRGUNIT , Y_Irgunit_PIN)
Select distinct isnull (Department_NO , -999) , 'קרן - לא ידוע'
from dbo.DWH_FACT_PAYMENTS3
Where Mifal in (670);

Update DWH_DIM_Y_IRGUNIT
Set Y_IRGUNIT_PIN = isnull (f.Department_Desc  ,'לא ידוע')
from DWH_FACT_PAYMENTS3 f
Where f.Department_NO = DWH_DIM_Y_IRGUNIT.Y_IRGUNIT And f.Mifal in (670)
	And DWH_DIM_Y_IRGUNIT.Y_Irgunit_PIN like 'קרן - לא ידוע'
And exists
(Select Max (period) As period,Department_NO
 From DWH_FACT_PAYMENTS3 P
 Where P.Department_Desc is not null and P.Mifal in (670)
 And P.Department_NO = f.Department_NO And P.period = f.period
 Group by Department_NO);
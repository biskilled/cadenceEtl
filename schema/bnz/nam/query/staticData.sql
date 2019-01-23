------------ dbo.DIM_AGE

Truncate table dbo.DIM_AGE
declare @i int

set @i=0

while @i<122
Begin
Insert into dbo.DIM_AGE
(AGE_NUM, AGE_TEXT, AGE_GROUP, age_shira, Age_group_order, Age_group_Pnimit)
Select @i,@i,
case
	when @i>=0 and @i<=1 then '0-1'
	when @i>=2 and @i<=4 then '2-4'
	when @i>=5 and @i<=14 then '5-14'
	when @i>=15 and @i<=24 then '15-24'
	when @i>=25 and @i<=34 then '25-34'
	when @i>=35 and @i<=44 then '35-44'
	when @i>=45 and @i<=54 then '45-54'
	when @i>=55 and @i<=64 then '55-64'
	when @i>=65 and @i<=74 then '65-74'
	when @i>=75 and @i<=123 then '75+'
End,
case
	when @i>=0 and @i<=14 then '0-14'
	when @i>=15 and @i<=29 then '15-29'
	when @i>=30 and @i<=44 then '30-44'
	when @i>=45 and @i<=64 then '45-64'
	when @i>=65 and @i<=74 then '65-74'
	when @i>=75 and @i<=84 then '75-84'
	when @i>=85 and @i<=123 then '85+'
End,
case
	when @i>=0 and @i<=1 then '0-1'
	when @i>=2 and @i<=4 then '2-4'
	when @i>=5 and @i<=14 then '5-14'
	when @i>=15 and @i<=24 then '15-24'
	when @i>=25 and @i<=34 then '25-34'
	when @i>=35 and @i<=44 then '35-44'
	when @i>=45 and @i<=54 then '45-54'
	when @i>=55 and @i<=64 then '55-64'
	when @i>=65 and @i<=74 then '65-74'
	when @i>=75 and @i<=123 then '75+'
End,
case
	when @i>=0 and @i<=74 then '0-74'
	when @i>=75 and @i<=84 then '75-84'
	when @i>=85 and @i<=123 then '85+'
End
--print @i
Set @i = @i+1
End


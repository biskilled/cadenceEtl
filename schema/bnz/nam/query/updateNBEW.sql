-- Update NBEW

Update stg
Set stg.MedOrgTree = trans.unitid
From STG_NBEW stg inner join BZ_ORG.dbo.trans_Code_Unicode trans ON trans.originalunitid = stg.orgmed;

Update STG_NBEW
Set MvEndDtTm= case when Year(MvEndDate)>=2049 then '12/31/2050 ' + MvEndTime else Convert (Smalldatetime, Convert (varchar(10), MvEndDate,103) + ' ' + MvEndTime, 103) end,
    MvBgDtTm = case when Year(MvBgDate)>=2049  then '12/31/2050 ' + MvBgTime else  Convert (Smalldatetime, Convert (varchar(10), MvBgDate,103) + ' ' + MvBgTime,103) end;

--Update STG_NBEW
--Set MvEndDtTm= case when convert (int,SUBSTRING(MvEndDate,7,4))>2050 then '12/31/2050 ' + MvEndTime else MvEndDate + ' ' + MvEndTime end,
--    MvBgDtTm = case when convert (int,SUBSTRING(MvBgDate,7,4))>2050 then '12/31/2050 ' + MvBgTime else  MvBgDate + ' ' + MvBgTime end;

UPDATE STG_NBEW 
SET mevtype=sub.mevtype
FROM STG_NBEW n inner join 
	(select m1.casenum,m1.mvsqnum,mevtype FROM STG_NBEW as m1 inner join 
		(select min(mvsqnum) mvsqnum,casenum FROM STG_NBEW	GROUP BY casenum) as sub2
			ON sub2.casenum=m1.casenum and sub2.mvsqnum=m1.mvsqnum) as sub
	ON sub.casenum=n.casenum --WHERE ETL_Date > '$start';

UPDATE STG_NBEW
SET mevtype=sub.mevtype
FROM STG_NBEW n inner join
	(select m1.casenum,m1.mvsqnum,mevtype FROM STG_NBEW as m1 inner join
		(select min(mvsqnum) mvsqnum,casenum FROM STG_NBEW	GROUP BY casenum) as sub2
			ON sub2.casenum=m1.casenum and sub2.mvsqnum=m1.mvsqnum) as sub
	ON sub.casenum=n.casenum; --WHERE ETL_Date > '$start'

update  STG_nbew
set  mah_em_med= coalesce(
    (select O1.ID from  BZ_ORG..OrgTree O1 inner join BZ_ORG..OrgTree O2 on O1.ID = O2.PID
     where O2.ID = t.medorgtree and O1.ItemTypeID = 3),

    (select O1.ID from  BZ_ORG..OrgTree O1 inner join BZ_ORG..OrgTree O2 on O1.ID = O2.PID
            inner join BZ_ORG..OrgTree O3 on O2.ID = O3.PID
        where O3.ID = t.medorgtree and O1.ItemTypeID = 3))
from STG_nbew as t
where mah_em_med  is null;

update  STG_nbew
set  mah_em_nurs= coalesce(
    (select O1.ID from  BZ_ORG..OrgTree O1  inner join BZ_ORG..OrgTree O2 on O1.ID = O2.PID
        where O2.ID = t.nursorgtree and O1.ItemTypeID = 3),
    (select O1.ID from  BZ_ORG..OrgTree O1
        inner join BZ_ORG..OrgTree O2 on O1.ID = O2.PID
        inner join BZ_ORG..OrgTree O3 on O2.ID = O3.PID
        where O3.ID = t.nursorgtree and O1.ItemTypeID = 3))
from STG_nbew as t
where mah_em_nurs  is null;

update  STG_NBEW
set NextOrgMed=In_nbew_1.OrgMed,
    NextOrgNurs=In_nbew_1.OrgNurs,
    NextMDeptNurstree=In_nbew_1.mah_em_nurs,NextMDeptMedtree=In_nbew_1.mah_em_nurs
FROM STG_NBEW inner JOIN
     STG_NBEW In_nbew_1 ON STG_NBEW.CaseNum = In_nbew_1.CaseNum AND
     STG_NBEW.MvCnsqNum = In_nbew_1.MvSqNum AND
	 STG_NBEW.MvCnsqNum <> STG_NBEW.MvSqNum
WHERE (STG_NBEW.nextOrgMed IS NULL or STG_NBEW.NextMDeptMedtree is null);

UPDATE STG_NBEW
SET PrevOrgMed = In_nbew_1.OrgMed, PrevOrgNurs = In_nbew_1.OrgNurs,
    PreviousMDeptNurstree=In_nbew_1.mah_em_nurs,PreviousMDeptMedtree=In_nbew_1.mah_em_MED
FROM STG_NBEW INNER JOIN STG_NBEW In_nbew_1 ON
    STG_NBEW.CaseNum = In_nbew_1.CaseNum AND In_nbew_1.MvCnsqNum = STG_NBEW.MvSqNum AND In_nbew_1.MvCnsqNum <> In_nbew_1.MvSqNum
WHERE (STG_NBEW.PrevOrgMed IS NULL or STG_NBEW.PreviousMDeptMedtree is null);


UPDATE STG_NBEW
set Gate_int=dbo.fn_get_gate(orgmed)
where gate_int is null;

UPDATE STG_NBEW
SET SugShihrurOrgMedFlg=
case
	when MvCat=4 then 9  		--אמבולטורי
	when MvCat=6 then 7		--יציאה לחופש
	when MvCat=7 then
		case
			when NextOrgMed<>OrgMed then 3
			else 0
		end	--כניסה מחופש
	when MvCat=1 then
		case
			when NextOrgMed<>OrgMed then 3
			else 0
		end
	when MvCat=2 then
		Case
			when MvType='40'  and gate_int=1 then 10  --נפטר
			when MvType<>'40' and gate_int=1 then 1
			when MvType='40'  and gate_int=3 then 5
			when MvType<>'40' and gate_int=3 then 4
			else  1 		-- הביתה
		end
	when NextOrgMed<>OrgMed then
		case
			when  Gate_int= 3 and dbo.fn_get_gate(NextOrgMed)=1 then 2   --מאושפז ממיון
			when    Gate_int= 3   and dbo.fn_get_gate(NextOrgMed)=3 then 6   -- העברה ממיון למיון
			else 3  -- העברה
		end
	when 	NextOrgMed=OrgMed and MvCat<>6 and MvCat<>4 then 0    --תנועת חדר או מיטה
else SugShihrurOrgMedFlg
end
where SugShihrurOrgMedFlg is null;

UPDATE STG_NBEW
SET SugShihrurOrgMedFlg=
case
	when NextOrgMed<>OrgMed then
		case 	when  Gate_int= 3 and dbo.fn_get_gate(NextOrgMed)=1 then 2   --מאושפז ממיון

			when    Gate_int= 3   and dbo.fn_get_gate(NextOrgMed)=3 then 6   -- העברה ממיון למיון
		else 3  -- העברה
		end
	when 	NextOrgMed=OrgMed and MvCat<>6 and MvCat<>4 then 0    --תנועת חדר או מיטה
else SugShihrurOrgMedFlg
end
where SugShihrurOrgMedFlg is null;

-- yoav 8.10.07 changed algorithm of mvcat=2
UPDATE STG_NBEW
SET SugShihrurOrgNursFlg=
case
	when MvCat=4 then 9  		--אמבולטורי
	when MvCat=6 then 7		--יציאה לחופש
	when MvCat=7 then
		case
			when NextOrgNurs<>OrgNurs then 3
			else 0
		end	--כניסה מחופש
	when MvCat=1 then
		case
			when NextOrgNurs<>OrgNurs then 3
			else 0
		end	 		--כניסה לבח
	when MvCat=2 then
		Case
			when MvType='40'  and gate_int=1 then 10  --נפטר
			when MvType<>'40' and gate_int=1 then 1
			when MvType='40'  and gate_int=3 then 5
			when MvType<>'40' and gate_int=3 then 4
			else  1 		-- הביתה
		end

	else SugShihrurOrgNursFlg
end
where SugShihrurOrgNursFlg is null;


UPDATE STG_NBEW
SET SugShihrurOrgNursFlg=
    case
        when NextOrgNurs<>OrgNurs then
                case 	when  Gate_int= 3 and dbo.fn_get_gate(NextOrgNurs)=1  then 2   --מאושפז ממיון
                when    Gate_int= 3   and dbo.fn_get_gate(NextOrgNurs)=3 then 6   -- העברה ממיון למיון
            else 3  -- העברה
            end
        when 	NextOrgMed=OrgMed and MvCat<>6 and MvCat<>4 then 0    --תנועת חדר או מיטה
    else SugShihrurOrgNursFlg
    end
where SugShihrurOrgNursFlg is null;

UPDATE STG_NBEW
SET SugKnisaOrgNursFlg=
case
	when MvCat=2 then
		case when PrevOrgNurs<>OrgNurs then  3
			else 0		--יציאה
		end
	when MvCat=4 then 9  		--אמבולטורי

	when MvCat=6  then
		case when PrevOrgNurs<>OrgNurs then  3
			else 0
		end
	when MvCat=7 then 7		--כניסה מחופש
	when MvCat=1 then
		case when	Gate_int=1 and EmergFlg <>'X' then 5  --אלקטיבי
			when Gate_int=1   and EmergFlg ='X'then 4 --דחוף לא ממיון
			when Gate_int=3  then 1   -- דחוף למיון
		end
else SugKnisaOrgNursFlg
end
where SugKnisaOrgNursFlg is null;


UPDATE STG_NBEW
SET SugKnisaOrgNursFlg=
case
	when MvCat=3 then
		case when PrevOrgNurs<>OrgNurs then
			case when  Gate_int= 1 and dbo.fn_get_gate(PrevOrgNurs)=3 then 2  --דחוף ממיון
				when  Gate_int= 3 and dbo.fn_get_gate(PrevOrgNurs)=3 then 6 --ממיון למיון
			else 3                    --העברה
			end

		else  0  --תנועת מיטה או חדר
		end
else SugKnisaOrgNursFlg
end
where SugKnisaOrgNursFlg is null;

UPDATE STG_NBEW
SET SugKnisaOrgMedFlg=
case
	when MvCat=2 then 			--יציאה
		case when PrevOrgMed<>OrgMed then 3
			else 0
		end
	when MvCat=4 then 9  		--אמבולטורי

	when MvCat=6 then 			--יציאה
		case when PrevOrgMed<>OrgMed then 3
			else 0
		end
	when MvCat=7 then 7		--כניסה מחופש
	when MvCat=1 then
		case when	Gate_int=1 and EmergFlg <>'X' then 5  --אלקטיבי
			when Gate_int=1   and EmergFlg ='X'then 4 --דחוף לא ממיון
			when Gate_int=3  then 1   -- דחוף ממיון
		end
else SugKnisaOrgMedFlg
end
where SugKnisaOrgMedFlg is null;


UPDATE STG_NBEW
SET SugKnisaOrgMedFlg=
case
	when MvCat=3 then
		case when PrevOrgMed<>OrgMed then
			case when  Gate_int= 1 and dbo.fn_get_gate(PrevOrgMed)=3 then 2  --דחוף ממיון
				when  Gate_int= 3 and dbo.fn_get_gate(PrevOrgMed)=3 then 6 --ממיון למיון
			else 3                    --העברה
			end

		else  0  --תנועת מיטה או חדר
		end
else SugKnisaOrgMedFlg
end
where SugKnisaOrgMedFlg is null;


UPDATE STG_NBEW
SET SugShihrurOrgMedFlg = 8, SugShihrurOrgNursFlg = 8 	--עדיין מאושפז
where (MvCnsqNum = '0')and (MvCat<>4)and (
 SugShihrurOrgMedFlg is null or SugShihrurOrgNursFlg is null);


UPDATE STG_NBEW
SET EnterMdeptNursFlg =
		Case
			When PreviousMDeptNurstree<>mah_em_nurs Then 3
		End,
	EnterMdeptMedFlg =
		Case
			When (PreviousMDeptMedtree<>mah_em_Med
					and EnterMdeptMedFlg is null) Then 3
		end,
	ExitMdeptNursFlg =
		Case
			When NextMDeptNurstree<>mah_em_nurs Then 3
		End,
	ExitMdeptMedFlg =
		Case
			When NextMDeptMedtree<>mah_em_Med Then 3
		End;

UPDATE STG_NBEW
SET ExitMdeptMedFlg =
	Case
		When SugShihrurOrgMedFlg<>3 Then SugShihrurOrgMedFlg
	End,
	ExitMdeptNursFlg =
	Case
		When SugShihrurOrgNursFlg<>3 Then SugShihrurOrgNursFlg
	End,
	EnterMdeptNursFlg =
	Case
		When SugKnisaOrgNursFlg<>3 Then SugKnisaOrgNursFlg
	End,
	EnterMdeptMedFlg =
	Case
		When SugKnisaOrgNursFlg<>3 Then SugKnisaOrgMedFlg
	End;

update STG_NBEW
set
   EnterDate = inn.enterDate,
   ExitDate = inn.ExitDate
FROM STG_NBEW ou,
    (
	SELECT CaseNum, MIN( convert (smalldatetime, MvBgDtTm)) enterDate, MAX( convert (smalldatetime, MvEndDtTm)) ExitDate
	FROM        STG_NBEW
	where  ( EnterDate is null or ExitDate is null)
	GROUP BY CaseNum,birthdate
    ) as inn
where ou.CaseNum = inn.CaseNum and ( ou.EnterDate is null or ou.ExitDate is null);

--Create Dimension Dim_MvType
drop table Dim_MvType
SELECT    case when STG_TN14U.MVCat='1' then 'קבלה'
when STG_TN14U.MVCat='2' then 'שחרור'
when STG_TN14U.MVCat='4'then 'ביקור אמבולטורי'
else 'אחר' end as MvCatType,

STG_TN14U.MVCat, STG_TN14U.MVType, STG_TN14U.UNMVTypeName into Dim_MvType
FROM         STG_TN14U INNER JOIN
                      STG_NBEW ON STG_TN14U.MVCat = STG_NBEW.MvCat AND STG_TN14U.MVType = STG_NBEW.MvType
GROUP BY STG_TN14U.MVCat, STG_TN14U.MVType, STG_TN14U.UNMVTypeName;

-- Add bt Tal shany on 2018-04-10, adding incremental loading
Delete from DWH_NBEW
Where exists (Select 1 from STG_NBEW Where DWH_NBEW.CaseNum = STG_NBEW.CaseNum AND DWH_NBEW.MvSqNum = STG_NBEW.MvSqNum);

Insert into DWH_NBEW
(CaseNum, MvSqNum, MvCat, MvType, MvBgDate, MvBgTime, MvEndDate, MvEndTime, MvCnsqNum, EmergFlg, AccidentType, AccidentNum, AccidentDate, OrgMed, OrgNurs, RoomCode, BedCode, Gate, DischType, AbsenceFlg, CreationDate, CreationUser, UpdateDate, UpdateUser, CancelFlg, CancelUser, DTCancelDate, MvReasFirstSec, MevType, GoremMafne, RefHosp, PLANB, BWPDT, KZTXT, DecisionTime, CancelDate, ETL_Date, MvBgDtTm, MvEndDtTm, NextOrgMed, NextOrgNurs, PrevOrgMed, PrevOrgNurs, SugKnisaOrgMedFlg, SugKnisaOrgNursFlg, SugShihrurOrgMedFlg, SugShihrurOrgNursFlg, EnterDate, ExitDate, Gate_int, MedOrgTree, NursOrgTree, mah_em_med, mah_em_nurs, BirthDate, PreviousMDeptMedtree, NextMDeptMedtree, PreviousMDeptNurstree, NextMDeptNurstree, EnterMdeptNursFlg, ExitMdeptNursFlg, EnterMdeptMedFlg, ExitMdeptMedFlg, ExitDate_Test)
Select
CaseNum, MvSqNum, MvCat, MvType, MvBgDate, MvBgTime, MvEndDate, MvEndTime, MvCnsqNum, EmergFlg, AccidentType, AccidentNum, AccidentDate, OrgMed, OrgNurs, RoomCode, BedCode, Gate, DischType, AbsenceFlg, CreationDate, CreationUser, UpdateDate, UpdateUser, CancelFlg, CancelUser, DTCancelDate, MvReasFirstSec, MevType, GoremMafne, RefHosp, PLANB, BWPDT, KZTXT, DecisionTime, CancelDate, ETL_Date, MvBgDtTm, MvEndDtTm, NextOrgMed, NextOrgNurs, PrevOrgMed, PrevOrgNurs, SugKnisaOrgMedFlg, SugKnisaOrgNursFlg, SugShihrurOrgMedFlg, SugShihrurOrgNursFlg, EnterDate, ExitDate, Gate_int, MedOrgTree, NursOrgTree, mah_em_med, mah_em_nurs, BirthDate, PreviousMDeptMedtree, NextMDeptMedtree, PreviousMDeptNurstree, NextMDeptNurstree, EnterMdeptNursFlg, ExitMdeptNursFlg, EnterMdeptMedFlg, ExitMdeptMedFlg, ExitDate_Test
From STG_NBEW;

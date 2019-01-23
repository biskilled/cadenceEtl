------------ Dim_Billing_Sign
Truncate table Dim_Billing_Sig
Insert into Dim_Billing_Sig
Select 'C', 'מבוטל' union
Select 'N',	'זיכוי' union
Select 'P',	'חיוב'

Truncate table Dim_Case_Type
Insert into Dim_Case_Type
Select 1,'מקרה אשפוז' union
Select 2,'מקרה אמבולטורי' union
Select 3,'מקרה מיון'

Truncate table DIM_KUPA_DEMOG
Insert into DIM_KUPA_DEMOG
Select '','קופה לא ידוע' union
Select 10,'כללית' union
Select 11,'מכבי' union
Select 12,'מאוחדת' union
Select 13,'לאומית' union
Select 80,'טל - קופה לא ידוע' union
Select 81,'טל - קופה לא ידוע' union
Select 82,'טל - קופה לא ידוע' union
Select 83,'טל - קופה לא ידוע' union
Select 98,'קופה לא ידוע' union
Select 99,'קופה לא ידוע'
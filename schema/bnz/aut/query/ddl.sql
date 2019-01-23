CREATE TABLE [dbo].[STG_FACT_PAYMENTS3](
	[TYPE] [varchar](10) NULL,
	[PERIOD] [numeric](28, 0) NULL,
	[MIFAL] [numeric](28, 0) NULL,
	[MIFAL_NAME] [varchar](40) NULL,
	[ID] [numeric](28, 0) NULL,
	[TOTAL_PAYS] [numeric](28, 2) NULL,
	[AUTO_DED] [numeric](28, 2) NULL,
	[PER_DED] [numeric](28, 2) NULL,
	[ALUT_MAAVID] [numeric](28, 2) NULL,
	[SEMEL_CODE] [decimal](28, 0) NULL,
	[SEMEL_CODE_VC] [varchar](70) NULL,
	[SEMEL_DESC] [varchar](60) NULL,
	[SEMEL_SEIF] [int] NULL,
	[DEPARTMENT_NO] [numeric](28, 0) NULL,
	[DEPARTMENT_DESC] [varchar](40) NULL,
	[F_Name] [varchar](30) NULL,
	[L_Name] [varchar](30) NULL,
	[ENAME] [varchar](30) NULL,
	[PERIODD] [datetime] NULL,
	[RASHUT_CODE] [numeric](28, 0) NULL,
	[RASHUT_PIN] [varchar](30) NULL,
	[SEIF] [numeric](28, 0) NULL,
	[SEIF_AMITI] [numeric](28, 0) NULL,
	[SEIF_TEUR] [varchar](20) NULL,
	[SEMEL_KG] [numeric](28, 0) NULL,
	[SEMEL_KG_PIN] [varchar](20) NULL,
	[Y_IRGUNIT] [numeric](28, 0) NULL,
	[Y_IRGUNIT_PIN] [varchar](20) NULL,
	[MIFAL_ID_DEPARTMENT_DESC] [varchar](70) NULL,
	[MIFAL_ID_Y_IRGUNIT] [varchar](70) NULL,
	[Pail_Code] [int] NULL,
	[Pail_Desc] [varchar](20) NULL,
	[M_Oved_Code] [varchar](40) NULL,
	[Achuz] [decimal](10, 2) NULL,
	[Kamut] [decimal](10, 1) NULL,
	[kamut_Konenot] [decimal](10, 1) NULL
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[STG_FACT_PAYMENTS3] ADD  CONSTRAINT [DF_STG_FACT_PAYMENTS3_SEMEL_SEIF]  DEFAULT ((-99)) FOR [SEMEL_SEIF]
GO

ALTER TABLE [dbo].[STG_FACT_PAYMENTS3] ADD  CONSTRAINT [DF_STG_FACT_PAYMENTS3_Pail_Code]  DEFAULT ((-1)) FOR [Pail_Code]
GO

ALTER TABLE [dbo].[STG_FACT_PAYMENTS3] ADD  CONSTRAINT [DF_STG_FACT_PAYMENTS3_Pail_Desc]  DEFAULT ('לא ידוע') FOR [Pail_Desc]
GO


if OBJECT_ID('DWH_FACT_PAYMENTS3') is null
Begin


	CREATE TABLE [dbo].[DWH_FACT_PAYMENTS3](
		[TYPE] [varchar](10) NULL,
		[PERIOD] [numeric](28, 0) NULL,
		[MIFAL] [numeric](28, 0) NULL,
		[MIFAL_NAME] [varchar](40) NULL,
		[ID] [numeric](28, 0) NULL,
		[TOTAL_PAYS] [numeric](28, 2) NULL,
		[AUTO_DED] [numeric](28, 2) NULL,
		[PER_DED] [numeric](28, 2) NULL,
		[ALUT_MAAVID] [numeric](28, 2) NULL,
		[SEMEL_CODE] [decimal](28, 0) NULL,
		[SEMEL_CODE_VC] [varchar](70) NULL,
		[SEMEL_DESC] [varchar](60) NULL,
		[SEMEL_SEIF] [int] NULL,
		[DEPARTMENT_NO] [numeric](28, 0) NULL,
		[DEPARTMENT_DESC] [varchar](40) NULL,
		[F_Name] [varchar](30) NULL,
		[L_Name] [varchar](30) NULL,
		[ENAME] [varchar](30) NULL,
		[PERIODD] [datetime] NULL,
		[RASHUT_CODE] [numeric](28, 0) NULL,
		[RASHUT_PIN] [varchar](30) NULL,
		[SEIF] [numeric](28, 0) NULL,
		[SEIF_AMITI] [numeric](28, 0) NULL,
		[SEIF_TEUR] [varchar](20) NULL,
		[SEMEL_KG] [numeric](28, 0) NULL,
		[SEMEL_KG_PIN] [varchar](20) NULL,
		[Y_IRGUNIT] [numeric](28, 0) NULL,
		[Y_IRGUNIT_PIN] [varchar](20) NULL,
		[MIFAL_ID_DEPARTMENT_DESC] [varchar](70) NULL,
		[MIFAL_ID_Y_IRGUNIT] [varchar](70) NULL,
		[Pail_Code] [int] NULL,
		[Pail_Desc] [varchar](30) NULL,
		[M_Oved_Code] [varchar](40) NULL,
		[Achuz] [decimal](10, 2) NULL,
		[Kamut] [decimal](10, 1) NULL,
		[kamut_Konenot] [decimal](10, 1) NULL
	) ON [PRIMARY]

END


if OBJECT_ID('[dbo].[STG_DIM_DEPARTMENTS]') is null
Begin

	CREATE TABLE [dbo].[STG_DIM_DEPARTMENTS](
		[RASHUT_CODE] [numeric](28, 0) NULL,
		[MIFAL] [numeric](28, 0) NULL,
		[MIFAL_NAME] [varchar](40) NULL,
		[ID] [numeric](28, 0) NULL,
		[ENAME] [varchar](50) NULL,
		[DEPARTMENT_NO] [numeric](28, 0) NULL,
		[DEPARTMENT_DESC] [varchar](40) NULL,
		[R_MONE_3] [numeric](28, 2) NULL,
		[MIFAL_ID_DEPARTMENT_DESC] [varchar](70) NOT NULL,
		[DEPARTMENT_NO2] [numeric](18, 0) NULL,
		[DEPARTMENT_DESC2] [varchar](50) NULL
	) ON [PRIMARY]
END

if OBJECT_ID('[dbo].[STG_DIM_SEMEL]') is null
Begin

	CREATE TABLE [dbo].[STG_DIM_SEMEL](
		[mifal] [numeric](28, 0) NULL,
		[mifal_name] [varchar](40) NULL,
		[semel_code] [decimal](28, 0) NULL,
		[semel_desc] [varchar](60) NULL,
		[semel_seif] [int] NULL,
		[Semel_F_Name] [varchar](8000) NULL,
		[semel_mifal] [numeric](35, 0) NULL
	) ON [PRIMARY]

END

if OBJECT_ID('[dbo].[Trans_Code_AUT_Full]') is null
Begin
	CREATE TABLE [dbo].[Trans_Code_AUT_Full](
		[OriginalUnitID] [varchar](20) NOT NULL,
		[OriginalUnitName] [varchar](max) NULL,
		[UnitID] [int] NULL,
		[stID] [int] NULL
	) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

END

if OBJECT_ID('[dbo].[DWH_DIM_Y_IRGUNIT]') is null
Begin

	CREATE TABLE [dbo].[DWH_DIM_Y_IRGUNIT](
		[Y_IRGUNIT] [numeric](28, 0) NOT NULL,
		[Y_IRGUNIT_PIN] [varchar](50) NULL
	) ON [PRIMARY]
END

if OBJECT_ID('[dbo].[STG_DIM_Employee_Full]') is null
Begin

	CREATE TABLE [dbo].[STG_DIM_Employee_Full](
		[Employees_Code] [varchar](60) NOT NULL,
		[Period] [varchar](30) NOT NULL,
		[M_Oved_Code] [varchar](40) NULL,
		[M_OVED] [numeric](28, 0) NULL,
		[MIFAL] [numeric](28, 0) NULL,
		[MIFAL_PIN] [varchar](20) NULL,
		[RASHUT_CODE] [numeric](28, 0) NULL,
		[RASHUT_PIN] [varchar](20) NULL,
		[MAHLAKA] [numeric](28, 0) NULL,
		[MAHLAKA_PIN] [varchar](60) NULL,
		[R_MISHPAHA] [varchar](15) NULL,
		[R_PRATI] [varchar](10) NULL,
		[R_ISHUV] [varchar](20) NULL,
		[R_KTOVET] [varchar](20) NULL,
		[MAZAV_MISHPAHTI] [numeric](28, 0) NULL,
		[MAZAV_PIN] [varchar](10) NULL,
		[TAAR_LEDA] [datetime] NULL,
		[TAAR_TH_AVODA] [datetime] NULL,
		[SEMEL_ISUK] [numeric](28, 0) NULL,
		[ISUK_PIN] [varchar](20) NULL,
		[Y_IRGUNIT] [numeric](28, 0) NULL,
		[Y_IRGUNIT_PIN] [varchar](20) NULL,
		[SUM_AHUZ_MISRA] [decimal](10, 2) NULL,
		[T_MASKORET] [datetime] NULL,
		[DERUG] [numeric](28, 0) NULL,
		[DERUG_PIN] [varchar](20) NULL,
		[DARGA] [numeric](28, 0) NULL,
		[DARGA_PIN] [varchar](20) NULL,
		[RAMA] [numeric](28, 0) NULL,
		[RAMA_PIN] [varchar](20) NULL,
		[TZ_MALE] [numeric](28, 0) NULL,
		[Y_IRGUNIT_VC] [nvarchar](40) NULL,
		[Y_IRGUNIT_BZ] [nvarchar](50) NULL,
		[Pail_Code] [int] NULL,
		[Pail_Desc] [varchar](30) NULL,
		[sector_num] [int] NULL,
		[sector_name] [nvarchar](50) NULL,
		[Achuz_Misra_Is_Empty] [varchar](30) NULL,
	 CONSTRAINT [PK_DWH_DIM_Employee_Full1] PRIMARY KEY CLUSTERED
	(
		[Employees_Code] ASC
	)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
	) ON [PRIMARY]

END
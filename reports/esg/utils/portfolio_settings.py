portfolioSettings = {
    "EUHYLUX": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "BI",
    },
    "EUHYDEN": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "DAIM": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "KIRCHE": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "EUHYCAT": {"Hedged": 1, "BM": None, "ShareClass": "CLC"},
    "PDANHY": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "KEVAHI": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined"},
    "CFEHI": {"Hedged": 1, "BM_Hedged": True, "BM_Composite": False, "ShareClass": "A"},
    "CFCOF": {"Hedged": 1, "BM": None, "ShareClass": "B"},
    "CFSTRAL": {"Hedged": 0, "BM": None, "ShareClass": "NotDefined"},
    "UBSHY": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "USD",
    },
    "DJHIC": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "DPBOND": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "A",
    },
    "DPLOAN": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "A",
    },
    "SJPHY": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": True,
        "BM_Composite_Parts": {"Index": ["HPC0", "H0A0"], "Weights": [0.50, 0.50]},
        "ShareClass": "NotDefined",
        "NAV": False,
    },
    "CFNEFO": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "A",
    },
    "SCII": {"Hedged": 1, "BM": None},
    "LVM": {
        "Hedged": "To Benchmark",
        "BM_Hedged": False,
        "BM_Composite": False,
        "ShareClass": "A",
    },
    "CFSMBC": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "TECTA": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
        "NAV": False,
    },
    "HPV": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
    },
    "CFTRC": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": True,
        "BM_Composite_Parts": {"Index": ["HPC0", "CSIWELLI"], "Weights": [0.5, 0.5]},
        "ShareClass": "B",
    },
    "UWV": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": True,
        "BM_Composite_Parts": {"Index": ["HPC0", "CSIWELLI"], "Weights": [0.65, 0.35]},
        "ShareClass": "NotDefined",
        "NAV": False,
    },
    "VELLIV": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "BI",
    },
    "NDEAFC": {"Hedged": 1, "BM": None, "ShareClass": "BI"},
    "CFSCO": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined"},
    "BSGLLF": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "NotDefined",
        "NAV": False,
    },
    "C4CLO1": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "C4CLO2": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "C4CLO3": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "C4CLO4": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "C4CLO5": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "C4USCLO1": {"Hedged": 1, "BM": None, "ShareClass": "NotDefined", "NAV": False},
    "MEDIO": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": True,
        "BM_Composite_Parts": {"Index": ["HPC0", "JUC0"], "Weights": [0.65, 0.35]},
        "ShareClass": "NotDefined",
    },
    "NEFO": {"Hedged": 1, "BM_Hedged": True, "BM_Composite": False, "ShareClass": "B"},
    "NDEAIBF": {
        "Hedged": 1,
        "BM_Hedged": True,
        "BM_Composite": False,
        "ShareClass": "BI",
        "NAV": True,
    },
    "TDPSD": {"Hedged": 0, "BM": None, "ShareClass": "NotDefined", "NAV": False},
}

BenchmarkEverestIndexCode = {"CSWELLI_Discontinued": "CSLLETOT"}

ratingDict_FromNum = {
    0: " ",
    1: "AAA",
    2: "AA+",
    3: "AA",
    4: "AA-",
    5: "A+",
    6: "A",
    7: "A-",
    8: "BBB+",
    9: "BBB",
    10: "BBB-",
    11: "BB+",
    12: "BB",
    13: "BB-",
    14: "B+",
    15: "B",
    16: "B-",
    17: "CCC+",
    18: "CCC",
    19: "CCC-",
    20: "CC",
    21: "C",
    22: "D",
    23: "NR",
}

capfourAssettype_dict = {
    "Bond_GovernmentBond": "Government Bond",
    "Bond_FixedRateBond": "Fixed Rate Bond",
    "Bond_StepFixedRateBond": "Step Fixed Rate Bond",
    "Bond_FloatingRateNote": "Floating Rate Note",
    "Bond_StepFloatingRateNote": "Step Floating Rate Note",
    "Bond_FixedToFloatingRateNote": "Fixed To Floating Rate Note",
    "Bond_FixedToVariableRateNote": "Fixed To Variable Rate Note",
    "Bond_PayInKindNoteFixed": "Pay In Kind Note Fixed",
    "Bond_PayInKindNoteFloat": "Pay In Kind Note Float",
    "Bond_PayInKindNoteFixedStep": "Pay In Kind Note Fixed Step",
    "Bond_PayInKindNoteFloatStep": "Pay In Kind Note Float Step",
    "Bond_ZeroCouponBond": "Zero Coupon Bond",
    "Loan_LeveragedLoan": "Leveraged Loan",
    "BondLike_FixedRateMortgageBond": "Fixed Rate Mortgage Bond",
    "Loan_DirectLoan": "Direct Loan",
    "EquityLike_PreferredShares": "Preferred Equity Shares",
    "EquityLike_UnlistedEquity": "Unlisted Equity Shares",
    "EquityLike_ListedEquity": "Listed Equity Shares",
    "BondLike_FloatingRateMortgageBond": "Floating Rate Mortgage Bond",
    "BondLike_AssetBackedSecurity": "Asset Backed Security",
    "BondLike_CollateralizedLoanObligation": "Collateralized Loan Obligation",
    "CreditDerivative_CreditDefaultSwapSovereign": "Credit Default Swap Sovereign",
    "CreditDerivative_CreditDefaultSwapSingleName": "Credit Default Swap Single Name",
    "CreditDerivative_CreditDefaultSwapIndex": "Credit Default Swap Index",
    "CreditDerivative_LoanCreditDefaultSwap": "Loan Credit Default Swap",
    "CreditDerivative_TotalReturnSwap": "Total Return Swap",
    "CreditDerivative_CdsIndexOption": "Credit Default Swap Index Option",
    "CreditDerivative_CreditDefaultTranche": "Credit Default Tranche",
    "Convertible_ConvertibleBond": "Convertible Bond",
    "CreditDerivative_CreditDefaultTranche": "Credit Default Tranche",
    "Convertible_ConvertibleBond": "Convertible Bond",
    "ForeignExchange_ForeignExchangeForward": "Foreign Exchange Forward",
    "ForeignExchange_ForeignExchangeOption": "Foreign Exchange Option",
    "Cash_Cash": "Cash",
    "Cash_Deposit": "Cash",
    "Cash_PayableReceivable": "Payable/Receivable",
    "Cash_Collateral": "Collateral",
    "Cash_MoneyMarketFund": "Money Market Fund",
    "Other_Claim": "Claim",
}

sorting_MaturityBuckets = [
    "< 1y",
    "1y - 3y",
    "3y - 5y",
    "5y - 7y",
    "7y - 10y",
    "10y - 20y",
    "> 20y",
    "Equity",
    "Closed-End Fund",
    "Index (iTraxx)",
    "Index (iBoxx)",
]
# sort_dur = ['< 0.3y', '0.3y - 1y', '1y - 3y', '3y - 5y', '5y - 7y', '7y - 10y', '10y - 20y', '> 20y']
sorting_PriceBuckets = [
    "< 40",
    "[40 - 50)",
    "[50 - 60)",
    "[60 - 70)",
    "[70 - 80)",
    "[80 - 90)",
    "[90 - 100)",
    "[100 - 110)",
    "> 110",
    "Cash",
    "Collateral",
    "FX",
    "Closed-End Fund",
    "Index (iTraxx)",
    "Index (iBoxx)",
]
# sort_rating_nosplit = ['CASH', '>= A', 'BBB', 'BB', 'B','CCC','CC', 'C', '(D)', 'NR']
sorting_Rating = [
    "AAA+",
    "AAA",
    "AAA-",
    "AA+",
    "AA",
    "AA-",
    "A+",
    "A",
    "A-",
    "BBB+",
    "BBB",
    "BBB-",
    "BB+",
    "BB",
    "BB-",
    "B+",
    "B",
    "B-",
    "CCC+",
    "CCC",
    "CCC-",
    "CC+",
    "CC",
    "CC-",
    "C+",
    "C",
    "C-",
    "D",
    "NR",
    "PR",
    "Equity",
    "Closed-End Fund",
    "Cash",
    "Collateral",
    "FX",
    "Index (iTraxx)",
    "Index (iBoxx)",
]
sorting_default = [
    "Equity",
    "Closed-End Fund",
    "Cash",
    "Collateral",
    "FX",
    "Index (iTraxx)",
    "Index (iBoxx)",
]
sorting_Rating_Bucket = [
    "AAA",
    "AA",
    "A",
    "BBB",
    "BB",
    "B",
    "CCC",
    "CC",
    "C",
    "D",
    "NR",
    "PR",
    "CLO",
    "Equity",
    "Closed-End Fund",
    "Cash",
    "Collateral",
    "FX",
    "Index (iTraxx)",
    "Index (iBoxx)",
]

renaming_RiskColumns = {
    "PositionDate": "Position Date",
    "AssetName": "Asset Name",
    "IssuerBondTicker": "Ticker",
    "AbbrevName": "Issuer Name",
    "AssetType": "Asset Type",
    "CapFourAssetType": "Asset Subtype",
    "AssetCurrencyISO": "Asset Currency",
    "IssueAmount": "Issue Amount",
    "IssueDate": "Issue Date",
    "CpnType": "Coupon Type",
    "CurrentCpnRate": "Current Coupon Rate",
    "C4Industry": "Industry",
    "BloombergIndustrySector": "Blomberg Industry Sector",
    "OperatingCountry": "Operating Country",
    "RiskCountry": "Risk Country",
    "RatingSimpleAverageChar": "Rating",
    "ParAmount": "Notional",
    "SelectedPrice": "Price",
    "DirtyValuePortfolioCur": "Market Value",
    "PfWeight": "Portfolio Weight",
    "BmWeight": "Benchmark Weight",
    "ActiveWeight": "Active Weight",
    "ToMaturityDate": "Maturity Date",
    "ToMaturityPrice": "MaturityPrice",
    "IspreadTW": "STW",
    "IspreadTC": "STC",
    "IspreadTM": "STM",
    "IspreadRegionalGovtTW": "RG_STW",
    "IspreadRegionalGovtTC": "RG_STC",
    "IspreadRegionalGovtTM": "RG_STM",
}

TectaRatingBucket = [
    ">=BBB-",
    "BB+",
    "BB",
    "BB-",
    "B+",
    "B",
    "B-",
    "<=CCC+",
    "NR",
    "PR",
    "Equity",
    "Cash",
    "FX",
]
TectaPriceBucket = [
    "<50",
    "[50-60)",
    "[60-70)",
    "[70-80)",
    "[80-90)",
    "[90-100)",
    ">=100",
    "Cash",
    "FX",
]
TectaMaturityBucket = [
    "< 1y",
    "1y - 3y",
    "3y - 5y",
    "5y - 7y",
    "7y - 10y",
    "> 10y",
    "Equity",
]
TectaAssetSubtypeBucket = [
    "Fixed Rate Bond - Unsecured",
    "Fixed Rate Bond - Secured",
    "Loan - First Lien",
    "Loan - Second Lien",
    "Floating Rate Note",
    "Pay In Kind Note",
    "Equity - Preferred",
    "Equity - Unlisted",
    "Cash",
    "FX",
]
Tecta_DefaultSorting = ["Other", "Cash", "FX"]

sorting_ESG = ["C4 ESG Score", "Environmental", "Social", "Governance"]

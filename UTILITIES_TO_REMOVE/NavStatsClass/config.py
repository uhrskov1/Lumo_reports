from capfourpy.c4api import CapFourAPI
from capfourpy.databases import Database


class NavStatsConfig:
    # Add objects
    validCompositeFormats = ["Composite", "composite", "Comp", "comp"]
    pattern_1 = r"(\d+)_([A-Z0-9]+)_(\d+)_([A-Z0-9]+)"  # Format = w1_idx1_w2_idx2: 50_HPC0_50_CSWELLIN
    pattern_2 = r"(\d+)_(\d+)_(.+)"  # Format = w1_w2_idx1_idx2: 50_50_HPC0_CSWELLIN
    pattern_3 = r"(\d+)_([A-Za-z0-9]+)-(\d+)_(.+)"  # Format = w1_idx1-w2_idx2: 50_HPC0-50_CSWELLIN
    pattern_4 = r"([A-Za-z0-9]+)_(\d+)-(.+)_(\d+)"  # Format = idx1_w1-idx2_w2: HPC0_50-CSWELLIN_50
    pattern_5 = r"^(LBP0|LBP3|LEC0|LEC3|LSF0|LSF3|LUS0|LUS3)_(\d+)([a-zA-Z]+)$"  # String used to split LEC3_7pct etc.
    pattern_6 = r"(\d+)([A-Za-z0-9]+)_(\d+)(.+)"  # Format = w1idx1_w2idx2: 50HPC0_50CSWELLIN
    combined_patterns = f"({'|'.join([pattern_1, pattern_2, pattern_3, pattern_4, pattern_6])})"
    validCurrencies = ["USD", "EUR"]
    bloombergIndices = ["GDDLE15", "GDDUE15"]
    currencySeriesMapping = {
        "EUR": "TRR_INDEX_VAL_EUR_H",
        "USD": "TRR_INDEX_VAL_USD_H",
        "LOC": "TRR_INDEX_VAL_LOC",
    }
    validNavSeries = ["GROSS", "NET"]
    navSeriesMapping = {
        "GROSS": "GrossIndex",
        "NET": "NavIndex"
    }

    # Add connections
    c4api = CapFourAPI()
    db_CfAnalytics = Database(database="CfAnalytics")
    db_CfRisk = Database(database="CfRisk")

    """
    SQL Queries
    """
    sql_validate_shareclass = """
    SELECT ShareClass
    FROM Performance.Portfolio
    WHERE PortfolioName = @fundCode
          AND PortfolioType = 'Portfolio';"""

    sql_validate_existence_nav_on_to_date = """
    SELECT DISTINCT bv.Date
    FROM Performance.vwBaseValue AS bv
    WHERE bv.ValueTypeName = 'NAV'
         AND bv.PortfolioName = @fundCode
         AND Date = @toDate;"""

    sql_validate_fund_code = """
    SELECT DISTINCT PortfolioName
    FROM Performance.Portfolio
    WHERE PortfolioType = 'Portfolio';"""

    sql_get_min_nav_date = """
    SELECT MIN(Date) as Date
    FROM Performance.vwBaseValue
    WHERE PortfolioName = @fundCode
    AND ShareClass = @shareClass"""

    sql_get_data_bloombergIndices = """
    SELECT BbgTicker AS SeriesIdentifier,
        'TRI' AS ValueType,
        ValueDate AS [Date],
        DataValue AS [Value],
        'CfAnalytics' AS [Source]
    FROM Calc.vwMktDataValue cc
    WHERE BbgTicker IN ( @idxCode )
        AND ValueDate
        BETWEEN @fromDate AND @toDate;"""

    sql_get_fund_class_currency = """
    SELECT PortfolioName AS Portfolio, 
          ShareClass, 
          Currency AS ClassCurrency
    FROM Performance.Portfolio
    WHERE PortfolioName = @fundCode
         AND ShareClass in ( @shareclass );"""

    sql_get_hedge_cost = """
    SELECT AsOfDate AS Date,
           HedgeCurrency,
           InstrumentCurrency,
           HedgeRateIndex,
           InstrumentRateIndex,
           HedgeRate,
           InstrumentRate,
           ForwardPoints3M,
           Spot,
           HedgeCost,
           Basis
    FROM CfRisk.Market.vwCrossCurrency cc
    WHERE InstrumentCurrency IN ( @fromCurrency )
          AND HedgeCurrency = @toCurrency
          AND AsOfDate >= @fromDate
    ORDER BY AsOfDate;"""

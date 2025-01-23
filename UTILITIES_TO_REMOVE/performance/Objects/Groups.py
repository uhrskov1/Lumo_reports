from UTILITIES_TO_REMOVE.performance.Utilities.EnumHelper import EnhancedEnum


class PerformanceData(EnhancedEnum):
    AssetId_String = "Everest AssetID."
    IssuerId_String = "Everest IssuerID."
    PositionSymbol = "FactSet PositionSymbol."
    AssetCurrency = "The raw Asset Currency. Use CleanAssetCurrency if Cash and FX should be grouped separately."
    PerformanceType = "The Factset Asset Performance Type"


class StaticData(EnhancedEnum):
    AssetName = "Asset Name."
    IssuerName = "Issuer Short Name."
    AssetType = "Asset Type."
    PrimaryIdentifier = "PrimaryIdentifier"
    CleanAssetCurrency = "The Asset Currency where Cash and FX are grouped separately. AssetCurrency can be used for the raw currency."
    CleanAssetCurrency_CLO = "The Asset Currency where Cash, FX and CLOs are grouped separately. AssetCurrency can be used for the raw currency."
    CleanAssetType_CLO = "The Asset Type where Cash, FX and CLOs are grouped separately."
    CapFourIndustry = "The Capital Four Industry."
    CapFourAssetType = "The Capital Four Main Asset Type."
    CapFourAssetSubType = "The Capital Four Sub Asset Type."
    MacAssetType = "Asset Type split used in MAC funds."
    MacAssetClass = "Asset Class Global split used in MAC funds."
    MacUniverse = "The SaaTaa EU/US Country Classifications."
    RiskCountry = "The Country of Risk."
    RiskCountryRegion = "The Region of Country of Risk."
    Seniority = "The Primary Seniority."
    SeniorSub = "Senior/Sub Split"
    IsPerpetual = "Perpetual Indicator"


class RatingData(EnhancedEnum):
    Rating = "Capital Four Simple Average Rating."
    CleanRating = "Capital Four Simple Average Rating - Rating Bucket."
    CleanRating_CLO = (
        "Capital Four Simple Average Rating - Rating Bucket. Where CLOs are grouped separately."
    )
    BucketRatings_CLO = "Capital Four Simple Average Rating - Rating Bucket. Where CLOs are grouped separately and below CCC bucketed."


class AnalystData(EnhancedEnum):
    Analyst = "Primary Capital Four Analyst."
    SecondaryAnalyst = "Secondary Capital Four Analyst."
    Location = "Primary Analyst Location."
    Team = "Primary Analyst Team"
    SubTeam = "Sub Team of Primary Analyst"


class SaaTaaData(EnhancedEnum):
    SaaTaaAssetClass = "The SaaTaa Asset Class Definitions, including rating breakdown."
    TeamTypes = "Types split on CLOs, Distressed and EU/US performing."


class RiskData(EnhancedEnum):
    DurationBuckets_CLO = "Simple Duration Buckets where CLOs are grouped separately."
    MaturityBuckets_CLO = "Simple Maturity Buckets where CLOs are grouped separately."
    IspreadBuckets_CLO = "Simple IspreadRegionalGovtTW Buckets where CLOs are grouped separately."


class EverestStaticData(EnhancedEnum):
    # TODO: This data connection should be refactored once we have the data in C4DW
    TectaRegion = "A region classification used for Tecta Reporting"

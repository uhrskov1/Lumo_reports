import numpy as np
import pandas as pd

from capfourpy.databases import Database

from UTILITIES_TO_REMOVE.Paths import getPathFromMainRoot


def getRMSData(Date: str = '2021-10-29', GrowthRateCap: float = 1, LeverageCap: float = 10):
    # Instantiate database connection
    database = Database(database='C4DW')

    # Define path to getRisk SQL
    RMSPath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'rms_data.sql')

    # Variables and values
    variables = ['@GrowthRatesCap_Py', '@LeverageCap_Py', '@Date_Py']
    values = [str(GrowthRateCap), str(LeverageCap), Date]

    # Request fund risk data
    tempRMSData = database.read_sql(path=RMSPath, variables=variables, values=values, statement_number=1)

    tempRMSData['AsOfDate'] = pd.to_datetime(tempRMSData['AsOfDate'])

    return tempRMSData


def getESGData(Date: str = '2021-10-29'):
    # Instantiate database connection
    database = Database(database='C4DW')

    # Define path to getRisk SQL
    ESGPath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'esg_data.sql')

    # Variables and values
    variables = ['@Date_Py']
    values = [Date]

    # Request ESG Data
    tempESGData = database.read_sql(path=ESGPath, variables=variables, values=values, statement_number=1)

    # Data Types
    tempESGData['AsOfDate'] = pd.to_datetime(tempESGData['AsOfDate'])
    tempESGData['Environmental'] = tempESGData['Environmental'].astype(float)
    tempESGData['Social'] = tempESGData['Social'].astype(float)
    tempESGData['Governance'] = tempESGData['Governance'].astype(float)
    tempESGData['C4 ESG Score'] = tempESGData['C4 ESG Score'].astype(float)

    return tempESGData


def getCIData(Date: str = '2021-10-29'):
    # Instantiate database connection
    database = Database(database='C4DW')

    # Define path to getRisk SQL
    CIPath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'ci_data.sql')

    # Variables and values
    variables = ['@PyDate']
    values = [Date]

    # Request ESG Data
    tempCIData = database.read_sql(path=CIPath, variables=variables, values=values, statement_number=1)

    outColumns = ['IssuerID', 'AsOfDate', 'CarbIntensityEur']

    if not tempCIData.empty:
        # Data Types
        tempCIData['AsOfDate'] = pd.to_datetime(tempCIData['AsOfDate'])
        tempCIData['CarbIntensityEur'] = tempCIData['CarbIntensityEur'].astype(float)

        return tempCIData[outColumns]
    else:
        tempCIData = pd.DataFrame(columns=outColumns)
        tempCIData['AsOfDate'] = tempCIData['AsOfDate'].astype(np.datetime64)
        return tempCIData


def getFundLevelCIData(FundCode: str,
                       Date: str,
                       ):
    # Instantiate database connection
    database = Database(database='C4DW')

    # Define path to getRisk SQL
    CIPath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'waci_fund_data.sql')

    # Variables and values
    variables = ['@Py_Fund', '@Py_ReportEndDate']
    values = [FundCode, Date]

    # Request ESG Data
    tempCIData = database.read_sql(path=CIPath, variables=variables, values=values, statement_number=8)

    outColumns = ['AsOfDate', 'PortfolioCode', 'BenchmarkCode', 'PF_WACI', 'BM_WACI']

    if not tempCIData.empty:
        # Data Types
        tempCIData['AsOfDate'] = pd.to_datetime(tempCIData['AsOfDate'])

        return tempCIData[outColumns]
    else:
        tempCIData = pd.DataFrame(columns=outColumns)
        tempCIData['AsOfDate'] = tempCIData['AsOfDate'].astype(np.datetime64)
        return tempCIData

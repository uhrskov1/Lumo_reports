"""
========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2023-01-31
-- Description:	Different Portfolio Related Datasources
========================================================================================================================================================================
"""
import pandas as pd

from capfourpy.databases import Database
from UTILITIES_TO_REMOVE.Paths import getPathFromMainRoot


def PortfolioStaticData(PortfolioCode:str = None, PortfolioID:int = None) -> pd.DataFrame:
    if not isinstance(PortfolioCode, (str, type(None))):
        raise TypeError('The PortfolioCode variable needs to be a str type.')

    if not isinstance(PortfolioID, (int, type(None))):
        raise TypeError('The PortfolioID variable needs to be a int type.')

    # SQL Path
    path = getPathFromMainRoot('C4Reporting', 'endpoints', 'utilities', 'RiskData', 'SQL', 'Portfolio_StaticData.sql')

    db = Database(database='C4DW')

    # Getting Data from Database
    args = {'@Py_PortfolioCode': PortfolioCode,
             '@Py_PortfolioID': PortfolioID}
    variables = []
    values = []
    replace_method = []

    for key, item in args.items():
        variables += [key]
        if item is None:
            values += ['NULL']
            replace_method += ['raw']
        else:
            values += [str(item)]
            replace_method += ['default']

    PortfolioData = db.read_sql(path=path, variables=variables, values=values, replace_method=replace_method)

    # Check that data exist.
    if PortfolioData.empty:
        if PortfolioID is not None:
            raise ValueError(f'The PortfolioID: {PortfolioID} does not exist! (or the C4DW.DailyOverview.Portfolio table could be empty!)')
        else:
            raise ValueError(f'The Portfolio: {PortfolioCode} does not exist! (or the C4DW.DailyOverview.Portfolio table could be empty!)')


    PortfolioData = PortfolioData.set_index('PortfolioCode')

    # Reformat types
    PortfolioData['SfdrArticleTypeEffectiveDate'] = pd.to_datetime(PortfolioData['SfdrArticleTypeEffectiveDate'])

    return PortfolioData

if __name__ == '__main__':
    Result = PortfolioStaticData()
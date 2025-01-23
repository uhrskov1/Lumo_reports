"""API Wrapper for Capital Four API.

========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2021-08-30
-- Description:	Wrapper class for Capital Four API. Syntax/Architecture is similar to the Bloomberg API.
========================================================================================================================================================================
"""  # noqa: E501

import json
import re
import ssl
import urllib.request
import urllib.response
from datetime import datetime, timedelta

import pandas as pd

from capfourpy.authentication import generate_token
from capfourpy.c4api.Additional_DataSources import (
    getCfRiskCrossCurrencyData,
    getCfRiskIndexData,
)
from capfourpy.c4api.C4API_Utilities import getReturnSeries
from capfourpy.c4api.CalculationEngine import GrossIndex

SCOPES = [
    "api://cfanalytics.ad.capital-four.com/Performance.ReadWrite",
    "api://cfanalytics.ad.capital-four.com/TimeSeries.ReadWrite",
]
# Define API controllers depending on the field the user is pulling
PERFORMANCE_CONTROLLER = [
    "NavSeries",
    "AumSeries",
    "SharesSeries",
    "NavIndex",
    "GrossIndex",
    "RelativeIndex",
]
TIMESERIES_CONTROLLER = [
    "PxLast",
    "SPREAD_TO_WORST",
    "SPREAD_DURATION",
    "MOD_DUR_TO_WORST",
    "YLD_TO_WORST",
]

CFANALYTCS_API_CLIENT_ID = "ad926898-da0e-41cf-be78-28db55dbfbfd"
AZURE_TENANT_ID = "62c5eb46-d129-44dd-91fd-47d9e6a17d69"


class CapFourAPI:
    """
    CapFourAPI provides an interface to interact with the Capital Four Analytics Performance API.

    This class facilitates data retrieval and management of performance and time series data, supporting
    multiple data sources and customizable query parameters. Its methods allow data fetching, caching updates,
    and data processing for various metrics and data fields, including performance indices, hedging costs,
    and currency-adjusted return series.

    Attributes
    ----------
        BASEURL (str): Base URL for the Capital Four API.
        context (ssl.SSLContext): SSL context for certificate management in API requests.

    Raises
    ------
        ValueError: For invalid fields, identifiers, or unsupported operations.

    Examples
    --------
        To connect to the Performance API and get data for a specific fund:
        C4API = CapFourAPI()
        data = C4API.cfdh(Identifier='EUHYDEN NotDefined Index',
             Field='NavIndex',
             Source='Everest',
             StartDate='2000-12-31',
             EndDate='2025-12-31',
             Trim='Both'
        )
    """

    def __init__(self):
        # self.BASEURL = 'https://cfanalytics.ad.capital-four.com/DataMgmt/api'  # Old API without authentication
        self.BASEURL = (
            "https://cfanalytics.ad.capital-four.com/api"  # New API with authentication enabled
        )

        # Context for not checking the Certificate. Should only be used for trusted URLs
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE

    def getURLData(self, url: str, field: str, neastedKey: str | None = None) -> pd.DataFrame:
        """Get the data from the URL and return it as a DataFrame.

        Args:
            url (str): The URL to get the data from
            field (str): The field of the data
            neastedKey (Optional[str]): The key to unneast the data, by default None

        Returns
        -------
            pd.DataFrame: The data from the URL as a DataFrame
        """
        idp_token = self.__get_token(field)
        try:
            request = urllib.request.Request(url, headers={"Authorization": f"Bearer {idp_token}"})
            response = urllib.request.urlopen(request, context=self.context)
            response = response.read().decode("utf-8")
            response_json = json.loads(response)
            tempDataFrame = pd.DataFrame(data=response_json)
        except urllib.error.HTTPError:
            return pd.DataFrame()

        if neastedKey is not None:
            tempNeastedDataFrame = tempDataFrame[neastedKey].apply(pd.Series)
            tempDataFrame = pd.merge(
                left=tempDataFrame.drop(columns=[neastedKey]),
                right=tempNeastedDataFrame,
                how="inner",
                left_index=True,
                right_index=True,
            )

        return tempDataFrame

    def __get_token(self, field: str = None):
        # Get the required scope for the controller we pull data from
        if field:
            if field in TIMESERIES_CONTROLLER or bool(re.match("TRR_INDEX_VAL_", field)):
                scope = next((s for s in SCOPES if "TimeSeries" in s), None)
            elif field in PERFORMANCE_CONTROLLER:
                scope = next((s for s in SCOPES if "Performance" in s), None)
            else:
                raise ValueError("This Field is not yet implemented!")

            token = generate_token(
                scopes=[scope], tenant_id=AZURE_TENANT_ID, client_id=CFANALYTCS_API_CLIENT_ID
            )
        else:
            token = None
        return token

    def postURLData(self, url: str, body: dict | None = None) -> bytes:
        """Post data to the URL and return the response.

        Args:
            url (str): The URL to post the data to
            body (Optional[dict]): The body to post, by default None

        Returns
        -------
            bytes: The response from the URL
        """
        if body is None:
            request = urllib.request.Request(url, method="POST")
            response = urllib.request.urlopen(request, context=self.context)
            response = response.read()

            return response

        request = urllib.request.Request(url, method="POST")
        request.add_header("Content-Type", "application/json")

        JSONdata = json.dumps(body)
        JSONdata_bytes = JSONdata.encode()

        response = urllib.request.urlopen(request, data=JSONdata_bytes, context=self.context)
        response = response.read()

        return response

    def cfdh(self, Identifier: str, Field: str, **kwargs) -> pd.DataFrame:
        """Get the data from the Capital Four API.

        Args:
            Identifier (str): The Identifier of the data
            Field (str): The Field of the data

        Returns
        -------
            pd.DataFrame

        Raises
        ------
            ValueError: If no StartDate is provided when Field is "GrossIndex_2"
            ValueError: If the Identifier is not a Currency when Field is "HedgeCost"
            ValueError: If the Field is not implemented yet
        """
        # Unpack Kwargs
        StartDateInput = kwargs.get("StartDate")
        EndDateInput = kwargs.get("EndDate")
        SourceInput = kwargs.get("Source")
        FrequencyInput = kwargs.get("Frequency")

        if Field in ["GrossIndex_2"]:
            if StartDateInput is None:
                raise ValueError(
                    "A StartDate is required for the calculation of the Gross Index, "
                    "as cost are compounded on a monthly basis."
                )

            AdjustedStartDate = datetime.strptime(  # noqa: DTZ007
                StartDateInput, "%Y-%m-%d"
            ).replace(day=1)
            AdjustedStartDate = AdjustedStartDate - timedelta(days=1)
            kwargs["StartDate"] = AdjustedStartDate.strftime("%Y-%m-%d")

            NetIndex = self.cfdh(Identifier=Identifier, Field="NavIndex", **kwargs)
            tempDataframe = GrossIndex(NetIndex=NetIndex).GenerateGrossIndex()
            tempDataframe = tempDataframe[tempDataframe["Date"] >= StartDateInput].copy(deep=True)

        elif Field in PERFORMANCE_CONTROLLER:
            if SourceInput is None:
                SourceInput = "Everest"

            TrimInput = kwargs.get("Trim")

            tempDataframe = self.__cfdh_Performance(
                Identifier=Identifier,
                Field=Field,
                StartDate=StartDateInput,
                EndDate=EndDateInput,
                Source=SourceInput,
                Frequency=FrequencyInput,
                Trim=TrimInput,
            )

        elif Field in TIMESERIES_CONTROLLER or bool(re.match("TRR_INDEX_VAL_", Field)):
            tempDataframe = self.__cfdh_TimeSeries(
                Identifier=Identifier,
                Field=Field,
                StartDate=StartDateInput,
                EndDate=EndDateInput,
                Source=SourceInput,
            )

        elif Field in ["NavIndex Return", "GrossIndex Return"]:
            if FrequencyInput is None:
                FrequencyInput = "Monthly"

            Field_Parts = Field.split(" ")

            tempNAVData = self.cfdh(Identifier=Identifier, Field=Field_Parts[0], **kwargs)

            tempDataframe = getReturnSeries(
                DataFrame=tempNAVData,
                NavColumn="IndexValue",
                DateColumn="Date",
                Frequency=FrequencyInput,
            )

        elif Field in ["HedgeCost"]:
            if Identifier.split(" ")[-1] != "Curncy":
                raise ValueError("The Identifier needs to be a Currency!")

            return getCfRiskCrossCurrencyData(
                Identifier=Identifier, StartDate=StartDateInput, EndDate=EndDateInput
            )

        else:
            raise ValueError("This Field is not yet implemented!")

        return tempDataframe

    def cfud(self, DataSeries: str) -> None:
        """Update the cache of the DataSeries.

        Args:
            DataSeries (str): The DataSeries to update the cache for (e.g. "TimeSeries")

        Raises
        ------
            ValueError: If the DataSeries is not a valid DataSeries. Only "TimeSeries" is valid.
        """
        if DataSeries == "TimeSeries":
            self.postURLData(url=f"{self.BASEURL}/TimeSeries/UpdateCache")
        else:
            raise ValueError(
                "This DataSeries is not a valid DataSeries! Please change the DataSeries"
            )

    def __cfdh_Performance(  # noqa: PLR0913
        self,
        Identifier: str,
        Field: str,
        StartDate: str | None,
        EndDate: str | None,
        Source: str,
        Frequency: str | None = None,
        Trim: str | None = None,
    ) -> pd.DataFrame:
        """Get the performance data from the Capital Four API.

        Args:
            Identifier (str): The Identifier of the data
            Field (str): The Field of the data
            StartDate (str): The StartDate of the data
            EndDate (str): The EndDate of the data
            Source (str): The Source of the data
            Frequency (Optional[str]): Frequency of the data, by default None
            Trim (Optional[dict]): The Trim of the data, by default None

        Returns
        -------
            pd.DataFrame
        """
        performanceURL = "/Performance"

        # Append Frequency
        if Frequency in ["Week", "Month", "Quarter", "Year"]:
            performanceURL += f"/{Frequency}"

        # Append seriesType and Source
        performanceURL += f"/{Field}/{Source}"

        # Append Identifier
        if Identifier is not None:
            IdentifierSplit = Identifier.split(" ")
            performanceURL += f"/{IdentifierSplit[0]}/{IdentifierSplit[1]}"

        # Append Days
        if StartDate is not None:
            performanceURL += f"?fromDate={StartDate}"

        if EndDate is not None:
            if StartDate is not None:
                performanceURL += f"&toDate={EndDate}"
            else:
                performanceURL += f"?toDate={EndDate}"

        if Trim is not None and Trim in ["Front", "Back", "Both"]:
            if StartDate is not None or EndDate is not None:
                performanceURL += f"&trim={Trim}"
            else:
                performanceURL += f"?trim={Trim}"

        outURL = self.BASEURL + performanceURL
        print(outURL)

        return self.getURLData(url=outURL, field=Field)

    def __cfdh_TimeSeries(
        self,
        Identifier: str | None,
        Field: str,
        StartDate: str | None,
        EndDate: str | None,
        Source: str | None,
    ) -> pd.DataFrame:
        """Get the time series data from the Capital Four API.

        Args:
            Identifier (str): The Identifier of the data
            Field (str): The Field of the data
            StartDate (str): The StartDate of the data
            EndDate (str): The EndDate of the data
            Source (str): The Source of the data

        Returns
        -------
            pd.DataFrame: Returns the time series data as a DataFrame
        """
        timeSericesURL = "/TimeSeries"

        # Append Identifier
        if Identifier is not None:
            IdentifierSplit = Identifier.split(" ")[0]
            timeSericesURL += f"/{IdentifierSplit}"
        else:
            IdentifierSplit = None

        # Append Field
        timeSericesURL += f"/{Field}"

        firstArg = "?"

        # Append Days
        if StartDate is not None:
            timeSericesURL += f"{firstArg}fromDate={StartDate}"
            firstArg = "&"

        if EndDate is not None:
            timeSericesURL += f"{firstArg}toDate={EndDate}"
            firstArg = "&"

        # Append Source
        if Source is not None:
            timeSericesURL += f"{firstArg}source={Source}"
            firstArg = "&"

        # Append Take/Skip
        timeSericesURL += (
            f"{firstArg}take=36500"  # Hardcode 100 years, not sure why the default value is 10 rows
        )

        outURL = self.BASEURL + timeSericesURL
        print(outURL)
        if Source == "CfRisk":
            tempDataFrame = getCfRiskIndexData(
                Identifier=IdentifierSplit, Field=Field, StartDate=StartDate, EndDate=EndDate
            )
            tempNeastedDataFrame = tempDataFrame["DataPoints"].apply(pd.Series)
            tempDataFrame = pd.merge(
                left=tempDataFrame.drop(columns=["DataPoints"]),
                right=tempNeastedDataFrame,
                how="inner",
                left_index=True,
                right_index=True,
            )
            tempDataFrame["Date"] = pd.to_datetime(tempDataFrame["Date"]).dt.tz_localize(None)
        else:
            tempDataFrame = self.getURLData(url=outURL, field=Field, neastedKey="DataPoints")
            if tempDataFrame.empty:
                return tempDataFrame

            tempDataFrame["Date"] = pd.to_datetime(tempDataFrame["Date"])

        return tempDataFrame

import json
import os
from datetime import datetime
from enum import Enum, auto

import pandas as pd

from UTILITIES_TO_REMOVE.database import Database

USER = os.path.expanduser("~")
USER = USER[USER.rfind("\\") + 1 :].upper()


class DataType(Enum):
    STATIC = auto()
    TIMESERIES = auto()


class BloombergFields:
    """
    Class for handling Bloomberg Fields data, including parsing, importing, and retrieving Bloomberg data fields
    within a database. The class includes methods for data validation, standardization, transformation, and
    database operations.

    Constants
    ----------
        DATABASE (str): Database name where Bloomberg data is stored.
        SCHEMA (str): Database schema for Bloomberg data.
        TABLE (str): Table name within the schema for storing Bloomberg fields data.
        COLUMNS (list[str]): List of required columns in the input data.
        TABLE_COLUMNS (list[str]): List of database table columns for data consistency.
        RESERVED_COLUMNS (list[str]): Reserved column names not allowed in input data.

    Methods
    -------
        PostField(Dataframe: pd.DataFrame) -> None
            Validates and posts Bloomberg data to the database, managing duplicates and new entries.

        GetField(Field: str, **kwargs) -> pd.DataFrame
            Retrieves Bloomberg data fields from the database, supporting optional filters such as date range and identifiers.

    Examples
    --------
        To retrieve Bloomberg data for a single field and for a single field for a single asset:
        bbg = BloombergFields()
        bbg_data = bbg.GetField(Field="HIST_CASH_FLOW")
        bbg_data_single = bbg.GetField(Field="HIST_CASH_FLOW", BloombergIDs="CMOH2319")
    """

    DATABASE = "CfRisk"
    SCHEMA = "Bloomberg"
    TABLE = "Fields"

    COLUMNS = ["IdentifierID", "IdentifierType", "BloombergID", "YellowKey", "Field", "TradeDate"]
    TABLE_COLUMNS = [
        "IdentifierID",
        "IdentifierTypeID",
        "BloombergID",
        "YellowKeyID",
        "FieldID",
        "TradeDate",
    ]

    RESERVED_COLUMNS = ["MetricDetails"]

    # region Private Functions

    @classmethod
    def __Validate(cls, Dataframe: pd.DataFrame) -> None:
        """
        Validates that the input DataFrame contains required columns and does not use reserved column names.

        Args:
            Dataframe (pd.DataFrame): Data to be validated.

        Raises
        ------
            ValueError: If required columns are missing.
            NameError: If reserved column names are used.
        """
        if not set(cls.COLUMNS).issubset(Dataframe.columns):
            raise ValueError(
                f'The Dataframe does not contain the required columns: {", ".join(cls.COLUMNS)}.'
            )
        if set(cls.RESERVED_COLUMNS).issubset(Dataframe.columns):
            raise NameError(
                f'The Dataframe contains the reserved column name: {", ".join(cls.RESERVED_COLUMNS)}. Please rename the column.'
            )

    @classmethod
    def __StandardizeColumns(cls, Dataframe: pd.DataFrame) -> None:
        """
        Standardizes columns in the input DataFrame, specifically adjusting date formats.

        Args:
            Dataframe (pd.DataFrame): DataFrame to standardize.

        Returns
        -------
            pd.DataFrame: A new DataFrame with standardized column formats.
        """
        # Adjust Date
        DataframeCopy = Dataframe.copy(deep=True)
        DataframeCopy["TradeDate"] = pd.to_datetime(DataframeCopy["TradeDate"].dt.date)

        return DataframeCopy

    @classmethod
    def __MapColumns(cls, Dataframe: pd.DataFrame, Column: str, ReferenceType: str) -> pd.DataFrame:
        """
        Maps input DataFrame columns to corresponding database reference IDs.

        Args:
            Dataframe (pd.DataFrame): DataFrame containing the column to map.
            Column (str): The column name to map.
            ReferenceType (str):The reference type for mapping.

        Returns
        -------
            pd.DataFrame: DataFrame with mapped columns.

        Raises
        ------
            LookupError: If any references are missing in the database.
        """
        DataframeCopy = Dataframe.copy(deep=True)

        MappingQuery = f"""  SELECT r.ID,
                                   r.Name,
                                   r.ReferenceType
                            FROM CfRisk.Bloomberg.Reference AS r
                            WHERE r.ReferenceType = '{ReferenceType}';
                         """

        db = Database(database=cls.DATABASE)

        Mapping = db.read_sql(query=MappingQuery)

        # Map
        ColumnID = f"{Column}ID"
        DataframeCopy[ColumnID] = pd.merge(
            left=DataframeCopy, right=Mapping, how="left", left_on=Column, right_on="Name"
        )["ID"]
        if DataframeCopy[ColumnID].isna().any():
            MissingMaps = ",".join(
                DataframeCopy.loc[DataframeCopy[ColumnID].isna(), Column].unique().tolist()
            )
            raise LookupError(
                f"This Column Reference: '{MissingMaps}' has yet to be created in: CfRisk.Bloomberg.Reference."
            )

        DataframeCopy.drop(columns=Column, inplace=True)

        return DataframeCopy

    @classmethod
    def __GetDataType(cls, Field: str) -> DataType:
        """
        Retrieves the data type (STATIC or TIMESERIES) for a given Bloomberg field.

        Args:
            Field (str): The Bloomberg field name.

        Returns
        -------
            DataType: Enum indicating whether the field is STATIC or TIMESERIES.

        Raises
        ------
            NotImplementedError: If the field is missing or data type is not specified in the database.
            ValueError: If an invalid data type is encountered.
        """
        DataQuery = """
                    SELECT r.ID,
                           r.Name,
                           r.ReferenceType,
                           r.Static
                    FROM Bloomberg.Reference AS r
                    WHERE r.ReferenceType = 'BloombergField';
                    """

        db = Database(database=cls.DATABASE)

        DataTypeData = db.read_sql(query=DataQuery)

        DataTypeDatabase = DataTypeData.query(f"Name == '{Field}'")["Static"]

        if DataTypeDatabase.empty:
            raise NotImplementedError(
                "The BloombergField is not created. Please insert the field in CfRisk.Bloomberg.Reference."
            )

        DataTypeDatabase = DataTypeDatabase.iloc[0]

        if DataTypeDatabase is None:
            raise NotImplementedError(
                "The DataType for this BloombergField is not given. Please update CfRisk.Bloomberg.Reference"
            )

        if DataTypeDatabase == 1:
            return DataType.STATIC
        elif DataTypeDatabase == 0:
            return DataType.TIMESERIES
        else:
            raise ValueError("This is not a valid DataType!")

    @classmethod
    def __ToJson(cls, Dataframe: pd.DataFrame):
        """
        Converts the DataFrame to a JSON string.

        Args:
            Dataframe (pd.DataFrame): DataFrame to convert.

        Returns
        -------
            str: JSON string representation of the DataFrame.
        """
        if Dataframe.shape[0] > 1:
            return json.dumps(Dataframe.reset_index(drop=True).to_dict("index"), default=str)
        else:
            return json.dumps(Dataframe.reset_index(drop=True).to_dict("records")[0], default=str)

    @classmethod
    def __PackData(cls, Dataframe: pd.DataFrame, DataType: DataType) -> pd.DataFrame:
        """
        Packages data for insertion, mapping identifiers and grouping as necessary.

        Args:
            Dataframe (pd.DataFrame): DataFrame to package.
            DataType (DataType): Type of data (STATIC or TIMESERIES) to guide processing.

        Returns
        -------
            pd.DataFrame: Packaged DataFrame ready for database insertion.
        """
        DataframeCopy = Dataframe.copy(deep=True)

        # TransformData
        Mapping = {
            "IdentifierType": "Identifier",
            "YellowKey": "BloombergYellowKey",
            "Field": "BloombergField",
        }

        for col, refType in Mapping.items():
            DataframeCopy = cls.__MapColumns(
                Dataframe=DataframeCopy, Column=col, ReferenceType=refType
            )

        if DataType == DataType.STATIC:
            DataframeCopy["TradeDate"] = datetime(1899, 1, 1)

        DataframeCopy = (
            DataframeCopy.groupby(by=cls.TABLE_COLUMNS)[
                DataframeCopy.drop(columns=cls.TABLE_COLUMNS).columns
            ]
            .apply(lambda row: cls.__ToJson(Dataframe=row))
            .reset_index()
        )
        DataframeCopy = DataframeCopy.rename(columns={0: "MetricDetails"})

        return DataframeCopy[cls.TABLE_COLUMNS + ["MetricDetails"]]

    @classmethod
    def __AugmentInsert(cls, Dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Adds metadata columns for tracking data insertions.

        Args:
            Dataframe (pd.DataFrame): DataFrame to augment with metadata.

        Returns
        -------
            pd.DataFrame: DataFrame with metadata columns.
        """
        DataframeCopy = Dataframe.copy(deep=True)

        DataframeCopy["AddUser"] = USER
        DataframeCopy["AddDate"] = datetime.now()
        DataframeCopy["Version"] = 1

        return DataframeCopy

    @classmethod
    def __GetField_Query(cls, Field: str, RawData: bool) -> str:
        """
        Generates SQL query for retrieving field data based on raw or processed data.

        Args:
            Field (str):The field name.
            RawData (bool):Flag to determine if raw or processed data is needed.

        Returns
        -------
            str: SQL query string.
        """
        if RawData:
            DataQuery = f"""
                            SELECT f.ID,
                                   f.IdentifierID,
                                   f.IdentifierTypeID,
                                   f.BloombergID,
                                   f.YellowKeyID,
                                   f.FieldID,
                                   f.TradeDate,
                                   f.MetricDetails,
                                   f.Version
                            FROM Bloomberg.Fields AS f
                            LEFT JOIN Bloomberg.Reference AS r ON r.ID = f.FieldID
                            WHERE r.Name = '{Field}'
                        """
        else:
            DataQuery = f"""SELECT vf.ID,
                                           vf.IdentifierID,
                                           vf.IdentifierType,
                                           vf.BloombergID,
                                           vf.YellowKey,
                                           vf.Field,
                                           vf.TradeDate,
                                           vf.MetricDetails,
                                           vf.Version
                                    FROM CfRisk.Bloomberg.vwFields AS vf
                                    WHERE vf.Field = '{Field}';
                                 """
        return DataQuery

    @classmethod
    def __TrimFieldData(cls, FieldData: pd.DataFrame, DataType: DataType, **kwargs) -> pd.DataFrame:
        """
        Trims field data by filtering based on date range, Bloomberg IDs, and identifiers.

        Args:
            FieldData (pd.DataFrame): DataFrame containing field data.
            DataType (DataType): The data type (STATIC or TIMESERIES).
            kwargs (dict): Additional filters like StartDate, EndDate, BloombergIDs, and IdentifierAndType.

        Returns
        -------
            pd.DataFrame: Filtered DataFrame.
        """
        LocalData = FieldData.copy(deep=True)

        # Unpack
        BloombergIDs = kwargs.get("BloombergIDs")
        IdentifierAndType = kwargs.get("IdentifierAndType")

        if DataType == DataType.TIMESERIES:
            # Unpack
            StartDate = kwargs.get("StartDate")
            EndDate = kwargs.get("EndDate")
            if StartDate is not None:
                LocalData = LocalData.query(f"TradeDate >= '{StartDate.strftime('%Y-%m-%d')}'")

            if EndDate is not None:
                LocalData = LocalData.query(f"TradeDate <= '{EndDate.strftime('%Y-%m-%d')}'")

        if BloombergIDs is not None:
            if isinstance(BloombergIDs, str):
                BloombergIDs = [BloombergIDs]
            if not isinstance(BloombergIDs, list):
                raise TypeError("The BloombergIDs argument needs to be a list.")
            BloombergIDs = "', '".join(BloombergIDs)
            LocalData = LocalData.query(f"BloombergID in ('{BloombergIDs}')")

        if IdentifierAndType is not None:
            if not isinstance(IdentifierAndType, dict):
                raise TypeError("The IdentifierAndType argument needs to be a dict.")
            for key, item in IdentifierAndType.items():
                if not isinstance(item, list):
                    raise TypeError("The IdentifierAndType argument items needs to be a list.")
                Identifiers = ", ".join([str(i) for i in item])
                LocalData = LocalData.query(f"IdentifierID in ({item}) & IdentifierType == '{key}'")

        return LocalData

    @classmethod
    def __GetField_Core(
        cls, Field: str, DataType: DataType, Unpact: bool, RawData: bool, **kwargs
    ) -> pd.DataFrame:
        """
        Core function for retrieving and processing field data from the database.

        Args:
            Field (str): Bloomberg field name.
            DataType (DataType): Type of data (STATIC or TIMESERIES).
            Unpact (bool): Whether to unpack JSON data in MetricDetails.
            RawData (bool): Flag to indicate raw data retrieval.
            **kwargs (Optional[any]): Additional filters for data retrieval.

        Returns
        -------
            pd.DataFrame: Processed field data.
        """
        DataQuery = cls.__GetField_Query(Field=Field, RawData=RawData)

        db = Database(database=cls.DATABASE)

        FieldData = db.read_sql(query=DataQuery)

        if FieldData.empty:
            return pd.DataFrame()

        FieldData["TradeDate"] = pd.to_datetime(FieldData["TradeDate"])

        FieldData = cls.__TrimFieldData(FieldData=FieldData, DataType=DataType, **kwargs)

        if FieldData.empty:
            return pd.DataFrame()

        if Unpact:
            # Unpack
            FieldData["MetricDetails"] = FieldData["MetricDetails"].apply(lambda x: json.loads(x))
            FieldData["MetricDetails_Length"] = FieldData["MetricDetails"].apply(lambda x: len(x))

            FieldData["MetricDetails"] = FieldData[["MetricDetails", "MetricDetails_Length"]].apply(
                lambda row: list(row["MetricDetails"].values())
                if row["MetricDetails_Length"] > 1
                else [row["MetricDetails"]],
                axis=1,
            )
            FieldData = FieldData.explode("MetricDetails").reset_index(drop=True)
            FieldData = FieldData.merge(
                pd.json_normalize(FieldData["MetricDetails"]), left_index=True, right_index=True
            ).drop(columns=["MetricDetails", "MetricDetails_Length"], axis=1)

        ColumnList = FieldData.columns.to_list()
        ColumnList.remove("Version")

        return FieldData[ColumnList + ["Version"]]

    @classmethod
    def __FindDuplicates(cls, Dataframe: pd.DataFrame, Field: str, DatatypeArg: DataType) -> dict:
        """
        Finds duplicate entries in the database for a specified field, returning data to update or insert.

        Args:
            Dataframe (pd.DataFrame): DataFrame with new data to check.
            Field (str): Bloomberg field name.
            DatatypeArg (DataType): Data type (STATIC or TIMESERIES) for processing.

        Returns
        -------
            dict: Dictionary with 'Update' and 'Insert' DataFrames.
        """
        NewData = BloombergFields.__PackData(Dataframe=Dataframe, DataType=DatatypeArg)

        DatabaseData = BloombergFields.__GetField_Core(
            Field=Field, DataType=DatatypeArg, Unpact=False, RawData=True
        )
        if DatabaseData.empty:
            return {"Update": pd.DataFrame(), "Insert": NewData}

        DatabaseData.rename(columns={"MetricDetails": "Old_MetricDetails"}, inplace=True)
        MergeData = pd.merge(left=NewData, right=DatabaseData, on=cls.TABLE_COLUMNS, how="left")

        # Update
        UpdateData = MergeData.query(
            "(MetricDetails != Old_MetricDetails) & (Old_MetricDetails.notna())", engine="python"
        )

        # Insert
        InsertData = MergeData.query("Old_MetricDetails.isna()", engine="python")
        InsertData = NewData.loc[InsertData.index]

        return {"Update": UpdateData, "Insert": InsertData}

    @classmethod
    def __Insert(cls, Dataframe: pd.DataFrame) -> None:
        """
        Inserts data into the database.

        Args:
            Dataframe (pd.DataFrame): DataFrame with data to insert.
        """
        if not isinstance(Dataframe, pd.DataFrame):
            raise ValueError("The Input is not a dataframe!")
        DataframeCopy = Dataframe.copy(deep=True)

        DataframeCopy = cls.__AugmentInsert(Dataframe=DataframeCopy)

        db = Database(database=cls.DATABASE)

        db.insert_sql(DataframeCopy, table=cls.TABLE, schema=cls.SCHEMA, if_exists="append")

        print(f"Inserted rows: {len(DataframeCopy)}.")

    @classmethod
    def __Update(cls, Dataframe: pd.DataFrame) -> None:
        """
        Updates existing data in the database.

        Args:
            Dataframe (pd.DataFrame): DataFrame with data to update.
        """
        db = Database(database=cls.DATABASE)
        for idx, row in Dataframe.iterrows():
            UpdateQuery = f""" UPDATE Bloomberg.Fields
                               SET MetricDetails = '{row['MetricDetails']}',
                                   Version = Version + 1,
                                   UpdateUser = '{USER}',
                                   UpdateDate = GETDATE()
                               WHERE ID = {row['ID']};
                          """
            db.execute_sql(statement=UpdateQuery)

        print(f"Updated rows: {len(Dataframe)}.")

    # endregion

    @classmethod
    def PostField(cls, Dataframe: pd.DataFrame) -> None:
        """
        Posts a validated data extract from Bloomberg to the database, handling duplicates.

        Args:
            Dataframe (pd.DataFrame): Cleaned DataFrame with Bloomberg data.
        """
        DataframeCopy = Dataframe.copy(deep=True)
        cls.__Validate(Dataframe=DataframeCopy)
        DataframeCopy = cls.__StandardizeColumns(Dataframe=DataframeCopy)

        Fields = DataframeCopy["Field"].unique().tolist()

        for flds in Fields:
            print(flds)
            dta = cls.__GetDataType(Field=flds)
            Output = cls.__FindDuplicates(
                Dataframe=DataframeCopy[DataframeCopy["Field"] == flds].reset_index(drop=True),
                Field=flds,
                DatatypeArg=dta,
            )

            UpdateData = Output.get("Update")
            InsertData = Output.get("Insert")

            if not UpdateData.empty:
                cls.__Update(Dataframe=UpdateData)
            else:
                print("Updated rows: 0.")

            if not InsertData.empty:
                cls.__Insert(Dataframe=InsertData)
            else:
                print("Inserted rows: 0.")

        return None

    @classmethod
    def GetField(cls, Field: str, **kwargs) -> pd.DataFrame:
        """
        Retrieves specified Bloomberg data fields from the database.

        Args:
            Field (str): Bloomberg field name to retrieve.
            **kwargs (Optional[any]):
                Optional parameters for filtering data, including:
                - StartDate (datetime): Start date for data.
                - EndDate (datetime): End date for data.
                - BloombergIDs (str or list): IDs to filter data.
                - IdentifierAndType (dict): Dictionary mapping identifier types to lists of IDs.

        Returns
        -------
            pd.DataFrame: DataFrame containing the Bloomberg data.
        """
        dta = cls.__GetDataType(Field=Field)
        return cls.__GetField_Core(Field=Field, DataType=dta, Unpact=True, RawData=False, **kwargs)

"""Databse connection class.

Database class: Python - Microsoft SQL Sever API connection.
It can be used for both reading and writing to the database. Note however that there isn't
implemented any writing restricting, these should be given through ones Microsoft credentials.

========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2019-12-11
-- Description:	API used to push and pull data frames from Python to a Microsoft SQL Sever
========================================================================================================================================================================

Database class: Python - Microsoft SQL Sever API connection.
It can be used for both reading and writing to the database. Note however that there isn't
implemented any writing restricting, these should be given through ones Microsoft credentials.

NOTE: This class is not thread-safe!
"""

import platform
import urllib

import pandas as pd
import sqlalchemy

from UTILITIES_TO_REMOVE import authentication

VALID_SERVER_STRINGS = [
    "DB-C4DW-PROD.ad.capital-four.com",
    "DB-C4DW-TEST.ad.capital-four.com",
    "mi-c4-share-register.public.c8c6f9050130.database.windows.net,3342",
]


class Database:
    """
    It can be used for both reading and writing to the database. Note however that there isn't
    implemented any writing restricting, these should be given through ones Microsoft credentials.

    It supports both traditional SQL Server and Azure SQL databases, allowing for seamless
    integration regardless of the hosting environment. Key features include the ability to execute
    raw SQL queries, read SQL queries from files, dynamically insert variables into queries, and
    perform bulk data insertions from pandas DataFrames. Additionally, the class provides mechanisms
    for handling multiple SQL statements and stored procedures, including support for fetching
    multiple result sets.

    NOTE: This class is not thread-safe!
    NOTE: This class assumes that the necessary credentials are managed externally.

    Examples
    --------
        To retrieve data from the SQL Server database:
        db = Database(database="C4DW")
        sql_query = "SELECT * FROM DailyOverview.AssetData"
        data_database = db.read_sql(sql_query)

        To retrieve data from the Azure database:
        db = Database(database="CfRms_prod", azure=True)
        sql_query = "SELECT TOP (1000) * FROM CfRms_prod.Scoring.Result"
        azure_database = db.read_sql(sql_query)
    """

    # The constructor of the Database_SQLAlchemy class.
    def __init__(
        self,
        server: str = None,
        database: str = None,
        azure: bool = False,
        use_service_account: bool = False,
        **kwargs,
    ):
        """Initialize the Database class with the given parameters.

        The `__init__` method initializes the Database class and establishes a connection to the
        specified database. The connection can be either to an Azure server or an SQL server,
        depending on the value of the `azure` parameter. Additional keyword arguments can be passed
        to customize the connection.

        Args:
            server (Optional[str]): The connection string to the server to connect to. If None, it defaults to production server.
            database (Optional[str]): The name of the database to connect to. If None, no specific database will be selected.
            azure (Optional[bool]): Specifies whether to connect to an Azure server or an SQL server. If True, an Azure server will be used. If False, an SQL server will be used.
            use_service_account (Optional[bool]): Use a service account for connection if True
            **kwargs (Optional[any]): Additional keyword arguments.

        Raises
        ------
            ValueError: If an invalid value is passed to the `azure` parameter.

        Examples
        --------
            To connect to an SQL server with a specific database:
            # >>> db = Database(database='my_database')

            To connect to an Azure server with a specific database and custom connection options:
            # >>> db = Database(database='my_database', azure=True, fast_executemany=True)
        """  # noqa: E501
        self.DATABASE = database
        self.SERVER = server
        connect_args_attrs = {}

        # Control server string
        if server and server not in VALID_SERVER_STRINGS:
            raise ValueError(
                f"The given server is not a valid server string, valid server strings are: "
                f"{VALID_SERVER_STRINGS}"
            )

        if not azure:
            if not self.SERVER:
                self.SERVER = "DB-C4DW-PROD.ad.capital-four.com"
            self.DRIVER = "ODBC Driver 17 for SQL Server"
            connection_str = f"Driver={self.DRIVER}; Server={self.SERVER}; Database={self.DATABASE}; Trusted_Connection=yes"  # noqa: E501
            if platform.system() == "Linux":
                authentication.setup_kerberos_environment(use_service_account)
        elif azure:
            # Set the Azure Server
            if not self.SERVER:
                self.SERVER = "mi-c4-share-register.public.c8c6f9050130.database.windows.net,3342"
            if platform.system() == "Linux":
                self.DRIVER = "ODBC Driver 18 for SQL Server"
                connection_str = (
                    f"Driver={self.DRIVER}; Server={self.SERVER}; Database={self.DATABASE};"
                )
                connect_args_attrs = authentication.get_azure_db_token()
            else:
                self.DRIVER = "ODBC Driver 17 for SQL Server"
                connection_str = f"Driver={self.DRIVER}; Server=tcp:{self.SERVER}; Database={self.DATABASE}; Encrypt=yes;TrustServerCertificate=no; Connection Timeout=30; Authentication=ActiveDirectoryIntegrated"  # noqa: E501
        else:
            raise ValueError(
                'Either connect to an SQL Server or an Azure Server. Only boolean values can be passed to parameter "Azure".'  # noqa: E501
            )

        # The connection requires a URL format
        parameters = urllib.parse.quote_plus(connection_str)

        # Instantiation of the SQL engine, which is used to connect Python with SQL
        self.engine = sqlalchemy.create_engine(
            f"mssql+pyodbc:///?odbc_connect={parameters}",
            fast_executemany=kwargs.get("fast_executemany", False),
            connect_args={"attrs_before": connect_args_attrs},
        )

    def read_sql(
        self,
        query: str = None,
        path: str = None,
        variables: list = None,
        values: list = None,
        stored_procedure: bool = False,
        statement_number: int = 0,
        debug: bool = False,
        **kwargs,
    ) -> pd.DataFrame:
        """Read data from the database using a SQL query or a file path.

        Args:
            query (Optional[str]): The SQL command which selects the desired data, by default None
            path (Optional[str]): The file path to a SQL file, which holds a SQL SELECT command that calls the desired data. Note that query overrides path, by default None
            variables (Optional[list]): Holds the names of any user-defined variables, which are defined in the SQL SELECT query, by default None
            values (Optional[list]): Holds the values of any user-defined variables, which are defined in the SQL SELECT query, by default None
            stored_procedure (Optional[bool]): Indicate whether to execute a stored procedure, by default False
            statement_number (Optional[int]): Used to indicate which SQL statement should be loaded, if the query contains more than one statement, by default 0
            debug (Optional[bool]): Enable debug print statements, by default False
            **kwargs (Optional[any]): Additional keyword arguments. The only two available parameters are:
                replace_method (Optional[list]): This indicates how the parameters in the SQL query should be replaced. Possible values are:
                    'default': This is used when only on parameter should be inserted.
                    'in': This is used when one wants to substitute one parameter in a SQL query
                    with a list of arguments.
                    'raw': This is a user defines method, where the users input is substituted
                    directly into the SQl query.
                Tables (Optional[int]): This indicates how many tables the user wants to fetch from the database.

        Returns
        -------
            pd.DataFrame or dict
                Returns a pandas data frame from the database. If the user wants to fetch multiple
                tables from the database then pass the number of tables as the parameter Tables, then a
                dictionary is returned.

        Raises
        ------
            ValueError: If neither a query nor a file path is provided.
            ValueError: If the length of the variables is not equal to the length of the values.
            ValueError: If the length of the replace methods is not equal to the length of the variables.
            ValueError: If the replace method is not defined.
            ValueError: If the number of tables is not a positive integer.
            TimeoutError: If the process reaches the maximum number of iterations.
        """  # noqa: E501
        # Note that query overrides path
        if query is None:
            if path is not None:
                # read file and close
                f = open(path)
                query = f.read()
                f.close()
            else:
                raise ValueError("Insert either a query or a file path")

        # Inserting user-defined variables in the SQL query if any
        if variables is not None:
            if len(variables) != len(values):
                raise ValueError(
                    "Then length of the values must be equal to the length of the variables."
                )

            if "replace_method" in kwargs:
                replace_method_list = kwargs.get("replace_method")
                if len(replace_method_list) != len(variables):
                    raise ValueError(
                        "The length of the replace methods (replace_method) must be equal to the the length of the variables."  # noqa: E501
                    )
                for i in range(0, len(variables)):
                    if replace_method_list[i] == "default":
                        query = query.replace(variables[i], "'" + values[i] + "'")
                    elif replace_method_list[i] == "in":
                        try:
                            query = query.replace(variables[i], "'" + "', '".join(values[i]) + "'")
                        except TypeError:
                            query = query.replace(
                                variables[i], "'" + "', '".join(str(num) for num in values[i]) + "'"
                            )
                    elif replace_method_list[i] == "raw":
                        query = query.replace(variables[i], values[i])
                    else:
                        raise ValueError(
                            f"The replace method: {replace_method_list[i]} is not defined."
                        )
            else:
                for i in range(0, len(variables)):
                    query = query.replace(variables[i], "'" + values[i] + "'")

        # Check if stored procedure
        if stored_procedure:
            # Add SQL-statement
            query = "SET NOCOUNT ON;\n\n" + query

        if debug:
            print(query)
        # Get a raw connection to the database via pyodbc
        connection = self.engine.raw_connection()
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query)

        # Find the table of interest
        if "Tables" in kwargs:
            NoOfTables = kwargs.get("Tables")
            if NoOfTables < 1:
                raise ValueError("The Number of tables needs to be a positive integer.")

            Result = {}
            TableCounter = 1
            BreakCounter = 0
            while TableCounter <= NoOfTables:
                if not BreakCounter < 100:
                    raise TimeoutError(
                        f"The current limit of {BreakCounter} was reached, thus the process is terminated!"  # noqa: E501
                    )
                BreakCounter += 1

                if debug:
                    print(cursor.description)
                    print(f"Table: {TableCounter}, Break: {BreakCounter}, NoOfTables: {NoOfTables}")

                # Fetch the all the column names and rows
                try:
                    column_names = [col[0] for col in cursor.description]
                    data_rows = cursor.fetchall()
                    DataLocated = True
                except TypeError:
                    DataLocated = False

                if DataLocated:
                    # Convert the data to a pandas data frame
                    temp_data = pd.DataFrame(data=(tuple(row) for row in data_rows))
                    temp_data.rename(
                        columns=dict(zip(temp_data.columns, column_names, strict=False)),
                        inplace=True,
                    )

                    Result.update({"Table_" + str(TableCounter): temp_data})

                    TableCounter += 1

                cursor.nextset()

            # Close the connection
            connection.close()
        else:
            if statement_number > 0:
                tableCounter = 1
                while tableCounter <= statement_number:
                    cursor.nextset()
                    if debug:
                        print(cursor.description)
                    tableCounter += 1

            # Fetch the all the column names and rows
            column_names = [col[0] for col in cursor.description]
            data_rows = cursor.fetchall()

            # Close the connection
            connection.close()

            # Convert the data to a pandas data frame
            Result = pd.DataFrame(data=(tuple(row) for row in data_rows))
            Result.rename(
                columns=dict(zip(Result.columns, column_names, strict=False)), inplace=True
            )

        return Result

    def insert_sql(
        self,
        dataframe=None,
        table: str = None,
        schema: str = None,
        if_exists: str = "fail",
        index: bool = False,
        index_label: str = None,
    ):
        """Insert a pandas DataFrame into a database table.

        Args:
            dataframe (Optional[pd.DataFrame]): The DataFrame to be pushed to the database, by default None.
            table (Optional[str]): The SQL table where data will be inserted, by default None.
            schema (Optional[str]): The schema where the SQL table is defined, by default None.
            if_exists (Optional[str]): Action if the table exists. Options: "fail", "replace", "append". By default "fail".
            index (Optional[bool]): Whether to use the index as a column. If True, specify index_label too, by default False.
            index_label (Optional[str]): Name of the index column if index=True, by default None.

        Raises:
            ValueError: If required arguments are missing or invalid.
            DatabaseError: If a database operation error occurs.
            Exception: For any other unexpected errors.
        """
        if dataframe is None:
            raise ValueError("Please specify a valid DataFrame.")
        if table is None:
            raise ValueError("Please specify a valid table name.")
        if schema is None:
            raise ValueError("Please specify a valid schema name.")

        try:
            dataframe.to_sql(
                name=table,
                con=self.engine,
                schema=schema,
                if_exists=if_exists,
                index=index,
                index_label=index_label,
                chunksize=10000,
            )
        except ValueError as ve:
            raise ValueError(f"DataFrame or column mismatch error: {ve}")
        except AttributeError as ae:
            raise AttributeError(f"Database connection or attribute error: {ae}")
        except pd.io.sql.DatabaseError as db_err:
            raise pd.io.sql.DatabaseError(f"Database error occurred: {db_err}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    def execute_sql(
        self,
        statement: str = None,
        read: bool = False,
        statement_number: int = 0,
        debug: bool = False,
    ):
        """Execute a SQL statement.

        This method executes a SQL statement using the provided statement string.
        It can also be used to execute multiple SQL statements in sequence.

        Args:
            statement (Optional[str]): The SQL statement to be executed. If None, no statement will be executed.
            read (Optional[bool]): Specifies whether the executed statement is a SELECT statement or not. If True, the method will return the result as a pandas DataFrame. If False, the method will not return any result.
            statement_number (Optional[int]):
                Specifies the number of result sets to fetch when executing multiple statements.
                This parameter is only used when `read` is True and `statement` is not None.
                If statement_number is 0, all result sets will be fetched.
                If statement_number is greater than 0, only the specified number of result sets will be
                fetched.
            debug (Optional[bool]): Specifies whether to print the description of each result set when executing multiple statements. This parameter is only used when `read` is True and `statement` is not None.

        Returns
        -------
            pandas.DataFrame or None
                If `read` is True and `statement` is not None, the method returns the result as a
                pandas DataFrame.
                If `read` is False or `statement` is None, the method does not return any result and
                returns None.

        Raises
        ------
            Any exceptions that may occur during the execution of the SQL statement.

        """  # noqa: E501
        # Connect to engine
        connection = self.engine.raw_connection()

        # Get cursor
        cursor = connection.cursor()

        # Execute statement
        cursor.execute(statement)
        if read:
            if statement_number > 0:
                tableCounter = 1
                while tableCounter <= statement_number:
                    cursor.nextset()
                    if debug:
                        print(cursor.description)
                    tableCounter += 1

            # Fetch the all the column names and rows
            column_names = [col[0] for col in cursor.description]
            data_rows = cursor.fetchall()

            # Convert the data to a pandas data frame
            result_data = pd.DataFrame(data=(tuple(row) for row in data_rows))
            result_data.rename(
                columns=dict(zip(result_data.columns, column_names, strict=False)), inplace=True
            )

        cursor.commit()

        # Close the connection
        connection.close()

        if read:
            return result_data

    def __del__(self):
        """Destructor for the Database class."""
        self.engine.dispose()
        del self.engine

# Silver validations

### Main implementation

We run a validation and sanity check on the silver tables, verifying things like uniqueness, some sanity checks for order of events and so on. We also gather information about each table like data types, number of null values per column and soo on.

All these, together with a few table-specific informations are stored in a silver_tablename_validations table in our database and will be used to do further sanity checks while building the gold tables.

### How it works

Using python, we connect to the database and download the table we want to work with into a pandas dataframe.
From there we run a bunch of checks and gather information that we write to a validation dataframe.

Once we are done we store the validations dataframe in the database with the same table name and the suffix "_validation"

### Tables validated
dbo.silver_disruption
dbo.silver_train_service_asd
dbo.silver_weather

### How to run
The silver validations can be run and rerun whenever using the validations_main_py script.

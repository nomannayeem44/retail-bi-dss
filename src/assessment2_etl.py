# Working copy: AI-written implementation under project-owner direction.
# Paths adapted for local review; analytical logic unchanged; not execution-tested.
# Import the tools needed for this ETL program
from pathlib import Path
from datetime import date, datetime
import pandas as pd


# Location of the original raw workbook
RAW_FILE = Path(
    Path(__file__).resolve().parents[1] / "data" / "raw" / "retail-source.xlsx"
)

# Folder where cleaned data will eventually be saved
OUTPUT_FOLDER = Path(__file__).resolve().parents[1] / "data" / "processed"

# The transaction worksheet has a space at the end of its name
SHEET_NAME = "RetailStore Dataset "


# EXTRACT: Read the transaction sheet from the Excel workbook
data = pd.read_excel(RAW_FILE, sheet_name=SHEET_NAME)


# Display basic validation information
print("DATA EXTRACTED SUCCESSFULLY")
print("Rows and columns:", data.shape)

print("\nColumn names:")
print(data.columns.tolist())

print("\nMissing values:")
print(data.isna().sum())

print("\nExact duplicate rows:")
print(data.duplicated().sum())

print("\nUnique Invoice IDs:")
print(data["Invoice ID"].nunique())

print("\nRepeated Invoice ID occurrences:")
print(data["Invoice ID"].duplicated().sum())
# ---------------------------------------------------------
# TRANSFORM: Standardise column names
# ---------------------------------------------------------

column_names = {
    "Invoice ID": "InvoiceID",
    "Customer type": "CustomerType",
    "Product line": "ProductLine",
    "Unit price": "UnitPrice",
    "Tax 5%": "Tax",
    "Date": "SourceDate",
    "Time": "SourceTime",
    "cogs": "COGS",
    "gross margin percentage": "GrossMarginPercentage",
    "gross income": "GrossIncome",
}

data = data.rename(columns=column_names)


# ---------------------------------------------------------
# Clean the text columns
# ---------------------------------------------------------

text_columns = [
    "InvoiceID",
    "Branch",
    "City",
    "CustomerType",
    "Gender",
    "ProductLine",
    "Payment",
]

for column in text_columns:
    data[column] = data[column].astype("string").str.strip()


# ---------------------------------------------------------
# Convert numerical columns
# ---------------------------------------------------------

numeric_columns = [
    "UnitPrice",
    "Quantity",
    "Tax",
    "Total",
    "COGS",
    "GrossMarginPercentage",
    "GrossIncome",
    "Rating",
]

for column in numeric_columns:
    data[column] = pd.to_numeric(data[column], errors="coerce")


# ---------------------------------------------------------
# Correct the mixed date formats
# ---------------------------------------------------------

def clean_mixed_date(value):
    """
    Correct Excel date objects where the month and day were reversed.
    Parse text dates using month/day/year format.
    """

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return pd.Timestamp(
            year=value.year,
            month=value.day,
            day=value.month,
        )

    return pd.to_datetime(
        str(value),
        format="%m/%d/%Y",
        errors="coerce",
    )


data["CleanDate"] = data["SourceDate"].apply(clean_mixed_date)


# ---------------------------------------------------------
# Convert transaction times
# ---------------------------------------------------------

parsed_time = pd.to_datetime(
    data["SourceTime"].astype(str),
    format="%H:%M:%S",
    errors="coerce",
)

data["CleanTime"] = parsed_time.dt.time


# Combine the cleaned date and time
date_text = data["CleanDate"].dt.strftime("%Y-%m-%d")
time_text = parsed_time.dt.strftime("%H:%M:%S")

data["TransactionTimestamp"] = pd.to_datetime(
    date_text + " " + time_text,
    errors="coerce",
)


# ---------------------------------------------------------
# Create unique and analytical fields
# ---------------------------------------------------------

# Create one unique number for every transaction row
data.insert(0, "TransactionKey", range(1, len(data) + 1))

# Create a date key in YYYYMMDD format
data["DateKey"] = (
    data["CleanDate"]
    .dt.strftime("%Y%m%d")
    .astype("Int64")
)

# Additional fields that will be useful in Power BI
data["Month"] = data["CleanDate"].dt.to_period("M").astype(str)
data["DayName"] = data["CleanDate"].dt.day_name()
data["Hour"] = data["TransactionTimestamp"].dt.hour.astype("Int64")


# ---------------------------------------------------------
# Validate the transformation
# ---------------------------------------------------------

print("\nTRANSFORMATION VALIDATION")

print("TransactionKey is unique:")
print(data["TransactionKey"].is_unique)

print("\nClean-date failures:")
print(data["CleanDate"].isna().sum())

print("\nClean-time failures:")
print(data["CleanTime"].isna().sum())

print("\nTimestamp failures:")
print(data["TransactionTimestamp"].isna().sum())

print("\nClean date range:")
print(data["CleanDate"].min(), "to", data["CleanDate"].max())

print("\nTransaction timestamp range:")
print(
    data["TransactionTimestamp"].min(),
    "to",
    data["TransactionTimestamp"].max(),
)

print("\nOriginal and cleaned date examples:")
print(
    data[
        [
            "InvoiceID",
            "SourceDate",
            "CleanDate",
            "SourceTime",
            "CleanTime",
            "TransactionKey",
        ]
    ].head(15)
)
# ---------------------------------------------------------
# CREATE KEYS FOR THE STAR SCHEMA
# ---------------------------------------------------------

# TimeKey represents the transaction time as HHMM.
# Example: 13:08 becomes 1308.
data["TimeKey"] = (
    data["TransactionTimestamp"]
    .dt.strftime("%H%M")
    .astype("Int64")
)


# ---------------------------------------------------------
# CREATE DimDate
# ---------------------------------------------------------

# Create one row for every date in the complete data period.
dim_date = pd.DataFrame(
    {
        "Date": pd.date_range(
            start=data["CleanDate"].min(),
            end=data["CleanDate"].max(),
            freq="D",
        )
    }
)

dim_date.insert(
    0,
    "DateKey",
    dim_date["Date"].dt.strftime("%Y%m%d").astype(int),
)

dim_date["Day"] = dim_date["Date"].dt.day
dim_date["DayName"] = dim_date["Date"].dt.day_name()
dim_date["MonthNumber"] = dim_date["Date"].dt.month
dim_date["MonthName"] = dim_date["Date"].dt.month_name()
dim_date["Quarter"] = (
    "Q" + dim_date["Date"].dt.quarter.astype(str)
)
dim_date["Year"] = dim_date["Date"].dt.year
dim_date["YearMonth"] = dim_date["Date"].dt.strftime("%Y-%m")


# ---------------------------------------------------------
# CREATE DimBranch
# ---------------------------------------------------------

dim_branch = (
    data[["Branch", "City"]]
    .drop_duplicates()
    .sort_values("Branch")
    .reset_index(drop=True)
)

dim_branch.insert(
    0,
    "BranchKey",
    range(1, len(dim_branch) + 1),
)


# ---------------------------------------------------------
# CREATE DimProduct
# ---------------------------------------------------------

dim_product = (
    data[["ProductLine"]]
    .drop_duplicates()
    .sort_values("ProductLine")
    .reset_index(drop=True)
)

dim_product.insert(
    0,
    "ProductKey",
    range(1, len(dim_product) + 1),
)


# ---------------------------------------------------------
# CREATE DimCustomer
# ---------------------------------------------------------

# This represents customer categories, not individual people,
# because the dataset does not contain a Customer ID.
dim_customer = (
    data[["CustomerType", "Gender"]]
    .drop_duplicates()
    .sort_values(["CustomerType", "Gender"])
    .reset_index(drop=True)
)

dim_customer.insert(
    0,
    "CustomerKey",
    range(1, len(dim_customer) + 1),
)


# ---------------------------------------------------------
# CREATE DimPayment
# ---------------------------------------------------------

dim_payment = (
    data[["Payment"]]
    .drop_duplicates()
    .sort_values("Payment")
    .reset_index(drop=True)
)

dim_payment.insert(
    0,
    "PaymentKey",
    range(1, len(dim_payment) + 1),
)


# ---------------------------------------------------------
# CREATE DimTime
# ---------------------------------------------------------

dim_time = (
    data[["TimeKey", "CleanTime", "Hour"]]
    .drop_duplicates()
    .sort_values("TimeKey")
    .reset_index(drop=True)
    .rename(columns={"CleanTime": "Time"})
)

# Create an easy-to-read hourly label.
dim_time["HourLabel"] = (
    dim_time["Hour"].astype(str).str.zfill(2) + ":00"
)

# Divide transaction times into business periods.
dim_time["DayPeriod"] = pd.cut(
    dim_time["Hour"],
    bins=[-1, 11, 16, 23],
    labels=["Morning", "Afternoon", "Evening"],
)


# ---------------------------------------------------------
# ADD DIMENSION KEYS TO EACH TRANSACTION
# ---------------------------------------------------------

warehouse_data = data.merge(
    dim_branch,
    on=["Branch", "City"],
    how="left",
    validate="many_to_one",
)

warehouse_data = warehouse_data.merge(
    dim_product,
    on="ProductLine",
    how="left",
    validate="many_to_one",
)

warehouse_data = warehouse_data.merge(
    dim_customer,
    on=["CustomerType", "Gender"],
    how="left",
    validate="many_to_one",
)

warehouse_data = warehouse_data.merge(
    dim_payment,
    on="Payment",
    how="left",
    validate="many_to_one",
)


# ---------------------------------------------------------
# CREATE FactSales
# ---------------------------------------------------------

fact_sales = warehouse_data[
    [
        "TransactionKey",
        "InvoiceID",
        "DateKey",
        "TimeKey",
        "BranchKey",
        "ProductKey",
        "CustomerKey",
        "PaymentKey",
        "UnitPrice",
        "Quantity",
        "Tax",
        "Total",
        "COGS",
        "GrossMarginPercentage",
        "GrossIncome",
        "Rating",
    ]
].copy()


# ---------------------------------------------------------
# VALIDATE THE STAR SCHEMA
# ---------------------------------------------------------

foreign_keys = [
    "DateKey",
    "TimeKey",
    "BranchKey",
    "ProductKey",
    "CustomerKey",
    "PaymentKey",
]

missing_foreign_keys = (
    fact_sales[foreign_keys].isna().sum().sum()
)

total_calculation_errors = (
    (
        fact_sales["Total"]
        - (fact_sales["COGS"] + fact_sales["Tax"])
    ).abs()
    > 0.001
).sum()

gross_income_errors = (
    (
        fact_sales["GrossIncome"]
        - fact_sales["Tax"]
    ).abs()
    > 0.001
).sum()

print("\nSTAR SCHEMA VALIDATION")

print("FactSales rows:")
print(len(fact_sales))

print("\nTransactionKey remains unique:")
print(fact_sales["TransactionKey"].is_unique)

print("\nMissing foreign keys:")
print(missing_foreign_keys)

print("\nTotal calculation errors:")
print(total_calculation_errors)

print("\nGross-income calculation errors:")
print(gross_income_errors)

print("\nTotal sales:")
print(round(fact_sales["Total"].sum(), 2))

print("\nDimension sizes:")
print("DimDate:", len(dim_date))
print("DimBranch:", len(dim_branch))
print("DimProduct:", len(dim_product))
print("DimCustomer:", len(dim_customer))
print("DimPayment:", len(dim_payment))
print("DimTime:", len(dim_time))

print("\nDimension key uniqueness:")
print("DimDate:", dim_date["DateKey"].is_unique)
print("DimBranch:", dim_branch["BranchKey"].is_unique)
print("DimProduct:", dim_product["ProductKey"].is_unique)
print("DimCustomer:", dim_customer["CustomerKey"].is_unique)
print("DimPayment:", dim_payment["PaymentKey"].is_unique)
print("DimTime:", dim_time["TimeKey"].is_unique)


# ---------------------------------------------------------
# LOAD: EXPORT THE CLEANED DATA AND WAREHOUSE TABLES
# ---------------------------------------------------------

star_schema_folder = OUTPUT_FOLDER / "Star Schema"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
star_schema_folder.mkdir(parents=True, exist_ok=True)

# Save a complete cleaned flat dataset for auditing.
data.to_csv(
    OUTPUT_FOLDER / "Cleaned_Retail_Transactions.csv",
    index=False,
)

# Save the central fact table.
fact_sales.to_csv(
    star_schema_folder / "FactSales.csv",
    index=False,
)

# Save each dimension table.
dim_date.to_csv(
    star_schema_folder / "DimDate.csv",
    index=False,
)

dim_branch.to_csv(
    star_schema_folder / "DimBranch.csv",
    index=False,
)

dim_product.to_csv(
    star_schema_folder / "DimProduct.csv",
    index=False,
)

dim_customer.to_csv(
    star_schema_folder / "DimCustomer.csv",
    index=False,
)

dim_payment.to_csv(
    star_schema_folder / "DimPayment.csv",
    index=False,
)

dim_time.to_csv(
    star_schema_folder / "DimTime.csv",
    index=False,
)

print("\nFILES EXPORTED SUCCESSFULLY")
print("Clean data folder:")
print(OUTPUT_FOLDER)

print("\nStar-schema folder:")
print(star_schema_folder)

# Working copy: AI-written implementation under project-owner direction.
# Paths adapted for local review; analytical logic unchanged; not execution-tested.
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# --------------------------------------------------
# 1. File locations
# --------------------------------------------------

CLEAN_FILE = Path(
    Path(__file__).resolve().parents[1] / "data" / "processed" / "Cleaned_Retail_Transactions.csv"
)

SUMMARY_FOLDER = Path(
    Path(__file__).resolve().parents[1] / "data" / "processed" / "Analysis Summaries"
)

CHART_FOLDER = Path(
    Path(__file__).resolve().parents[1] / "outputs" / "charts"
)

SUMMARY_FOLDER.mkdir(parents=True, exist_ok=True)
CHART_FOLDER.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load cleaned data
# --------------------------------------------------

data = pd.read_csv(
    CLEAN_FILE,
    parse_dates=["CleanDate", "TransactionTimestamp"]
)

print("CLEAN DATA LOADED")
print("Rows and columns:", data.shape)


# --------------------------------------------------
# 3. Overall business KPIs
# --------------------------------------------------

overall_kpis = pd.DataFrame(
    {
        "KPI": [
            "Transactions",
            "Total Sales Including Tax",
            "Units Sold",
            "Average Transaction Value",
            "Gross Income",
            "Average Customer Rating",
        ],
        "Value": [
            data["TransactionKey"].nunique(),
            data["Total"].sum(),
            data["Quantity"].sum(),
            data["Total"].mean(),
            data["GrossIncome"].sum(),
            data["Rating"].mean(),
        ],
    }
)

overall_kpis["Value"] = overall_kpis["Value"].round(2)


# --------------------------------------------------
# 4. Branch performance
# --------------------------------------------------

branch_summary = (
    data.groupby(["Branch", "City"], as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
        GrossIncome=("GrossIncome", "sum"),
        AverageTransaction=("Total", "mean"),
        AverageRating=("Rating", "mean"),
    )
    .sort_values("TotalSales", ascending=False)
)

branch_summary = branch_summary.round(2)


# --------------------------------------------------
# 5. Product-line performance
# --------------------------------------------------

product_summary = (
    data.groupby("ProductLine", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
        GrossIncome=("GrossIncome", "sum"),
        AverageRating=("Rating", "mean"),
    )
    .sort_values("TotalSales", ascending=False)
)

product_summary = product_summary.round(2)


# --------------------------------------------------
# 6. Monthly and daily performance
# --------------------------------------------------

monthly_summary = (
    data.groupby("Month", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
        GrossIncome=("GrossIncome", "sum"),
        AverageRating=("Rating", "mean"),
    )
)

monthly_summary = monthly_summary.round(2)

daily_summary = (
    data.groupby("CleanDate", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
    )
    .sort_values("CleanDate")
)

daily_summary["SevenDayAverage"] = (
    daily_summary["TotalSales"].rolling(window=7, min_periods=1).mean()
)

daily_summary = daily_summary.round(2)


# --------------------------------------------------
# 7. Customer and payment performance
# --------------------------------------------------

customer_summary = (
    data.groupby("CustomerType", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
        AverageTransaction=("Total", "mean"),
        AverageRating=("Rating", "mean"),
    )
    .sort_values("TotalSales", ascending=False)
)

customer_summary = customer_summary.round(2)

payment_summary = (
    data.groupby("Payment", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        AverageTransaction=("Total", "mean"),
        AverageRating=("Rating", "mean"),
    )
    .sort_values("TotalSales", ascending=False)
)

payment_summary = payment_summary.round(2)


# --------------------------------------------------
# 8. Hourly sales performance
# --------------------------------------------------

hourly_summary = (
    data.groupby("Hour", as_index=False)
    .agg(
        Transactions=("TransactionKey", "count"),
        TotalSales=("Total", "sum"),
        UnitsSold=("Quantity", "sum"),
    )
    .sort_values("Hour")
)

hourly_summary = hourly_summary.round(2)

highest_sales_hours = hourly_summary.nlargest(5, "TotalSales")


# --------------------------------------------------
# 9. Export summary tables
# --------------------------------------------------

overall_kpis.to_csv(
    SUMMARY_FOLDER / "Overall_KPIs.csv",
    index=False
)

branch_summary.to_csv(
    SUMMARY_FOLDER / "Branch_Summary.csv",
    index=False
)

product_summary.to_csv(
    SUMMARY_FOLDER / "Product_Summary.csv",
    index=False
)

monthly_summary.to_csv(
    SUMMARY_FOLDER / "Monthly_Summary.csv",
    index=False
)

daily_summary.to_csv(
    SUMMARY_FOLDER / "Daily_Summary.csv",
    index=False
)

customer_summary.to_csv(
    SUMMARY_FOLDER / "Customer_Summary.csv",
    index=False
)

payment_summary.to_csv(
    SUMMARY_FOLDER / "Payment_Summary.csv",
    index=False
)

hourly_summary.to_csv(
    SUMMARY_FOLDER / "Hourly_Summary.csv",
    index=False
)


# --------------------------------------------------
# 10. Chart 1: Sales by branch
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 5))

labels = (
    branch_summary["Branch"]
    + " - "
    + branch_summary["City"]
)

bars = ax.bar(
    labels,
    branch_summary["TotalSales"],
    color=["#2F75B5", "#5B9BD5", "#9DC3E6"],
)

ax.set_title("Total Sales by Branch")
ax.set_xlabel("Branch and City")
ax.set_ylabel("Sales Including Tax ($)")
ax.grid(axis="y", alpha=0.25)

for bar, value in zip(bars, branch_summary["TotalSales"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"${value:,.0f}",
        ha="center",
        va="bottom",
    )

plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "Figure_1_Sales_by_Branch.png",
    dpi=300,
)
plt.close()


# --------------------------------------------------
# 11. Chart 2: Sales by product line
# --------------------------------------------------

product_chart = product_summary.sort_values(
    "TotalSales",
    ascending=True
)

fig, ax = plt.subplots(figsize=(9, 6))

ax.barh(
    product_chart["ProductLine"],
    product_chart["TotalSales"],
    color="#70AD47",
)

ax.set_title("Total Sales by Product Line")
ax.set_xlabel("Sales Including Tax ($)")
ax.set_ylabel("Product Line")
ax.grid(axis="x", alpha=0.25)

plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "Figure_2_Sales_by_Product_Line.png",
    dpi=300,
)
plt.close()


# --------------------------------------------------
# 12. Chart 3: Daily sales trend
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 5))

ax.plot(
    daily_summary["CleanDate"],
    daily_summary["TotalSales"],
    color="#5B9BD5",
    linewidth=1.2,
    label="Daily sales",
)

ax.plot(
    daily_summary["CleanDate"],
    daily_summary["SevenDayAverage"],
    color="#C00000",
    linewidth=2.5,
    label="Seven-day average",
)

ax.set_title("Daily Sales Trend and Seven-Day Moving Average")
ax.set_xlabel("Date")
ax.set_ylabel("Sales Including Tax ($)")
ax.grid(alpha=0.25)
ax.legend()

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "Figure_3_Daily_Sales_Trend.png",
    dpi=300,
)
plt.close()


# --------------------------------------------------
# 13. Chart 4: Average rating by branch
# --------------------------------------------------

rating_chart = branch_summary.sort_values(
    "AverageRating",
    ascending=False
)

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    rating_chart["Branch"] + " - " + rating_chart["City"],
    rating_chart["AverageRating"],
    color="#ED7D31",
)

ax.set_title("Average Customer Rating by Branch")
ax.set_xlabel("Branch and City")
ax.set_ylabel("Average Rating")
ax.set_ylim(0, 10)
ax.grid(axis="y", alpha=0.25)

for bar, value in zip(bars, rating_chart["AverageRating"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"{value:.2f}",
        ha="center",
        va="bottom",
    )

plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "Figure_4_Rating_by_Branch.png",
    dpi=300,
)
plt.close()


# --------------------------------------------------
# 14. Display the main results
# --------------------------------------------------

print("\nOVERALL BUSINESS KPIs")
print(overall_kpis.to_string(index=False))

print("\nBRANCH PERFORMANCE")
print(branch_summary.to_string(index=False))

print("\nPRODUCT-LINE PERFORMANCE")
print(product_summary.to_string(index=False))

print("\nMONTHLY PERFORMANCE")
print(monthly_summary.to_string(index=False))

print("\nCUSTOMER PERFORMANCE")
print(customer_summary.to_string(index=False))

print("\nPAYMENT PERFORMANCE")
print(payment_summary.to_string(index=False))

print("\nFIVE HIGHEST-SALES HOURS")
print(highest_sales_hours.to_string(index=False))

print("\nANALYSIS COMPLETED SUCCESSFULLY")
print("Summary tables saved to:", SUMMARY_FOLDER)
print("Charts saved to:", CHART_FOLDER)

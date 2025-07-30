import pandas as pd

# Load your Excel file
df = pd.read_excel(
    r"D:\Desktop\AlinasPrograms\myenv\HBL Proj2\Deposit_Chatbot_Data_Schema.xlsx",
    sheet_name="Deposit_Transactions"
)

# Convert 'date' column to datetime (in case it's not already)
df['date'] = pd.to_datetime(df['date'])

# Group by customer segment and sum deposits
segment_deposits = df.groupby('customer_segment')['deposit_amount'].sum().round(2).reset_index()

# Sort by deposit amount descending
segment_deposits = segment_deposits.sort_values(by='deposit_amount', ascending=False)

# Print results
print("✅ Total deposits by customer segment (rounded to 2 decimals):\n")
print(segment_deposits)
print("Rows in DataFrame:", len(df))
print("Unique TXNs:", df['transaction_id'].nunique())


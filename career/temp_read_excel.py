import pandas as pd

# Read Excel file
df = pd.read_excel('user_mig/exports/idino_table_columns.xlsx')

print('=== Excel Columns ===')
for i, col in enumerate(df.columns):
    print(f'{i}: {col}')
print()

# First column is table name
table_col = df.columns[0]
print('=== Unique Table Names ===')
tables = df[table_col].dropna().unique().tolist()
for t in tables:
    print(f'  - {t}')
print()

# Find achievement related rows
print('=== Achievement Related Data ===')
achievement_df = df[df[table_col].astype(str).str.contains('achievement', case=False, na=False)]
if len(achievement_df) > 0:
    print(achievement_df.to_string())
else:
    # Search in any column
    for col in df.columns:
        mask = df[col].astype(str).str.contains('achievement', case=False, na=False)
        if mask.any():
            print(f'Found in column: {col}')
            print(df[mask].to_string())
            break

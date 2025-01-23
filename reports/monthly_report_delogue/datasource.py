import pandas as pd

def curate_data():
    data_new_sales = pd.read_excel(r'C:\Users\uhrsk\OneDrive - Lumo Technologies ApS\Lumo Technologies\Delogue Data - dummy dataset.xlsx', sheet_name='NewSales')
    data_pl = pd.read_excel(r'C:\Users\uhrsk\OneDrive - Lumo Technologies ApS\Lumo Technologies\Delogue Data - dummy dataset.xlsx', sheet_name='P&L')
    data_cashflow = pd.read_excel(r'C:\Users\uhrsk\OneDrive - Lumo Technologies ApS\Lumo Technologies\Delogue Data - dummy dataset.xlsx', sheet_name='CashFlow')
    data_renewals = pd.read_excel(r'C:\Users\uhrsk\OneDrive - Lumo Technologies ApS\Lumo Technologies\Delogue Data - dummy dataset.xlsx', sheet_name='Renewals')
    data_fte = pd.read_excel(r'C:\Users\uhrsk\OneDrive - Lumo Technologies ApS\Lumo Technologies\Delogue Data - dummy dataset.xlsx', sheet_name='FTE')

    return {
        "NewSales": data_new_sales,
        "P&L": data_pl,
        "CashFlow": data_cashflow,
        "Renewals": data_renewals,
        "FTE":data_fte,
    }

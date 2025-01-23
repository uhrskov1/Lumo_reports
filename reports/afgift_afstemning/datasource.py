import pandas as pd


def curate_data(input_date: dict):
    # mapping = pd.read_excel(r"C:\repo\Lumo\sample_datasets\semler_report_data.xlsx", sheet_name="mapping")
    # skat_data = pd.read_excel(r"C:\repo\Lumo\sample_datasets\semler_report_data.xlsx", sheet_name="SKAT")
    # coreview_gb = pd.read_excel(r"C:\repo\Lumo\sample_datasets\semler_report_data.xlsx", sheet_name="coreview_gb")
    # coreview_aktiveringer = pd.read_excel(r"C:\repo\Lumo\sample_datasets\semler_report_data.xlsx", sheet_name="coreview_aktiveringer")
    # coreview_termineringer = pd.read_excel(r"C:\repo\Lumo\sample_datasets\semler_report_data.xlsx", sheet_name="coreview_termineringer")

    mapping = input_date['mapping'].copy(deep=True)
    skat_data = input_date['SKAT'].copy(deep=True)
    coreview_gb = input_date['coreview_gb'].copy(deep=True)
    coreview_aktiveringer = input_date['coreview_aktiveringer'].copy(deep=True)
    coreview_termineringer = input_date['coreview_termineringer'].copy(deep=True)

    """
    Map typing using below logic on the SKAT raw data
    """
    # Shift columns to access previous and next rows
    skat_data['Previous_Registreringsnummer'] = skat_data['Registreringsnummer'].shift(1)
    skat_data['Next_Registreringsnummer'] = skat_data['Registreringsnummer'].shift(-1)
    skat_data['Previous_Type'] = None  # Placeholder for previously calculated type

    # Function to calculate the type for each row
    def calculate_type(row):
        if row['Afgifttype'] == "Refusion af leasingafg.":
            return "Terminering"
        elif row['Registreringsnummer'] == row['Next_Registreringsnummer']:
            return "Genberegning"
        elif (row['Previous_Type'] == "Genberegning" and
              row['Registreringsnummer'] == row['Previous_Registreringsnummer']):
            return "Genberegning"
        elif row['Afgifttype'] == "Leasingafgift":
            return "Aktivering"
        elif row['Afgifttype'] == "Leasing Ekstraopkr.":
            return "Frist overskridelse"
        elif row['Afgifttype'] == "Registreringsafgift":
            return "Max afgiftsændring"
        else:
            return "Mangler"

    # Apply the function row by row
    skat_data['Type'] = skat_data.apply(calculate_type, axis=1)

    # Shift the 'Type' column to simulate the "Previous_Type" dependency
    skat_data['Previous_Type'] = skat_data['Type'].shift(1)

    # Recalculate to handle the dependency on Previous_Type
    skat_data['Type'] = skat_data.apply(calculate_type, axis=1)
    skat_data = skat_data.drop(columns=['Previous_Registreringsnummer', 'Next_Registreringsnummer', 'Previous_Type'])

    # Map Customer Account number
    mapping['Customer Account'] = mapping['Customer Account'].astype('int64')
    skat_data = pd.merge(skat_data, mapping, how='left')

    """
    Fristoverskridelser Regafgift - Operations
    """
    fristoverskridelser = skat_data.copy(deep=True)
    fristoverskridelser = fristoverskridelser.loc[fristoverskridelser['Type'] == 'Frist overskridelse']
    fristoverskridelser = fristoverskridelser.loc[fristoverskridelser['Afgift'] != 0]

    """
    Aktiveringer Regafgift - Operations
    """
    aktiveringer = skat_data.copy(deep=True)
    aktiveringer = aktiveringer.loc[aktiveringer['Type'] == 'Aktivering']

    aktiveringer = pd.merge(aktiveringer, coreview_aktiveringer[['Customer Account', 'Amount']], how='left')
    aktiveringer['Diff'] = aktiveringer['Afgift'] - aktiveringer['Amount']
    aktiveringer = aktiveringer.loc[(aktiveringer['Diff'] > 1) | (aktiveringer['Diff'] < -1)]
    aktiveringer = aktiveringer.drop_duplicates()
    aktiveringer.rename(columns={'Amount': 'Coreview Amount'}, inplace=True)

    """
    Termineringer Regafgift - Operations
    """
    termineringer = skat_data.copy(deep=True)
    termineringer = termineringer.loc[termineringer['Type'] == 'Terminering']

    coreview_termineringer = coreview_termineringer.groupby(['Customer Account'], as_index=False).agg({'Amount': 'sum'})
    termineringer = pd.merge(termineringer, coreview_termineringer[['Customer Account', 'Amount']], how='left')
    termineringer['Diff'] = termineringer['Afgift'] - termineringer['Amount']
    termineringer = termineringer.loc[(termineringer['Diff'] > 1) | (termineringer['Diff'] < -1)| (termineringer['Diff'].isna())]
    termineringer.rename(columns={'Amount': 'Coreview Amount'}, inplace=True)

    """
    Genberegning Regafgift - RV
    """
    genberegning = skat_data.copy(deep=True)
    genberegning = genberegning.loc[genberegning['Type'] == 'Genberegning']

    coreview_gb = coreview_gb.groupby(['Customer Account'], as_index=False).agg({'Amount': 'sum'})
    genberegning = genberegning.groupby(['Dato', 'Registreringsnummer', 'Køretøj', 'Afgifttype', 'Type',
                                         'Customer Account'], as_index=False).agg({'Afgift': 'sum'})
    genberegning = pd.merge(genberegning, coreview_gb[['Customer Account', 'Amount']], how='left')
    genberegning['Diff'] = genberegning['Afgift'] - genberegning['Amount']
    genberegning = genberegning.loc[(genberegning['Diff'] > 1) | (genberegning['Diff'] < -1)]
    genberegning.rename(columns={'Amount': 'Coreview Amount'}, inplace=True)

    return {'fristoverskridelser': fristoverskridelser,
            'aktiveringer': aktiveringer,
            'termineringer': termineringer,
            'genberegning': genberegning}

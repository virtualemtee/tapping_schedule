import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
from io import BytesIO

# Load the trained model and label encoder
model = joblib.load('paired_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# Function to assign grade based on Si and Fe values
def assign_grade(si, fe):
    if si <= 0.03 and fe <= 0.03:
        return '0303'
    elif si <= 0.04 and fe <= 0.04:
        return '0404'
    elif si <= 0.04 and fe <= 0.06:
        return '0406'
    elif si <= 0.05 and fe <= 0.06:
        return '0506'
    elif si <= 0.06 and fe <= 0.10:
        return '0610'
    elif si <= 0.10 and fe <= 0.20:
        return '1020'
    elif si <= 0.15 and fe <= 0.35:
        return '1535'
    elif si >= 0.15 or fe >= 0.35:
        return '2050'
    return None

# Function to perform analysis on a section of data
def analyze_section(data):
    results = {
        "Poor Grades Bettered": [],
        "Non-Improved Grades": [],
        "Acceptable Grades": [],
        "Acceptable & Non-Improved": [],
        "Remaining Cells": []
    }
    used_cells = set()  # Track used cells

    # Logic to analyze and categorize the data as per the original code
    for index, row in data.iterrows():
        cell_id = row['CELL']
        si_a = row['Si']
        fe_a = row['Fe']
        individual_grade = row['Grade']
        # Add logic for pairing cells based on the original code
        # Populate results['Poor Grades Bettered'], results['Non-Improved Grades'], etc.
        # ...

    return results

# Streamlit app layout
st.title("Tapping Schedule")
st.write("Upload cell purity Excel file to generate the tapping schedule.")
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    st.write("Data Preview:")
    st.dataframe(data)
    
    if 'CELL' in data.columns and 'Si' in data.columns and 'Fe' in data.columns:
        data['Si'] = data['Si'].fillna(0)
        data['Fe'] = data['Fe'].fillna(0)
        data['Grade'] = data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

        # Group data into sections based on the `CELL` column
        sections = {
            "Section_1": data[(data['CELL'] >= 1) & (data['CELL'] <= 25)],
            "Section_2": data[(data['CELL'] >= 26) & (data['CELL'] <= 50)],
            "Section_3": data[(data['CELL'] >= 51) & (data['CELL'] <= 75)],
            "Section_4": data[(data['CELL'] >= 76) & (data['CELL'] <= 100)],
        }

        # Prepare an Excel file with separate tabs for each section
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for section_name, section_data in sections.items():
                if not section_data.empty:
                    results = analyze_section(section_data)
                    # Combine all results for the section
                    summary_data = []
                    for category, pairs in results.items():
                        for pair in pairs:
                            summary_data.append(pair)

                    # Convert results to DataFrame
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name=section_name, index=False)
        
        output_file.seek(0)
        st.download_button(
            label="Download Results by Sections",
            data=output_file,
            file_name='sectioned_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

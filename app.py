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
def perform_analysis(section_data):
    section_data['Si'] = section_data['Si'].fillna(0)
    section_data['Fe'] = section_data['Fe'].fillna(0)
    section_data = section_data[(section_data['Si'] > 0) & (section_data['Fe'] > 0)]
    section_data['Grade'] = section_data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

    # Add logic to process each section similar to the original code
    # Process and pair cells as per your original logic
    # This is a placeholder; the full logic will go here
    # For demonstration, just returning the processed data
    return section_data[['CELL', 'Si', 'Fe', 'Grade']]

# Streamlit app layout
st.title("Tapping Schedule")
st.write("Upload cell purity Excel file to generate the tapping schedule.")
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    st.write("Data Preview:")
    st.dataframe(data)

    if 'CELL' in data.columns and 'Si' in data.columns and 'Fe' in data.columns:
        # Divide data into sections
        sections = {
            "Section 1": data[data['CELL'].between(1, 25)],
            "Section 2": data[data['CELL'].between(26, 50)],
            "Section 3": data[data['CELL'].between(51, 75)],
            "Section 4": data[data['CELL'].between(76, 100)],
        }

        # Process each section and save results in Excel file
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for section_name, section_data in sections.items():
                if not section_data.empty:
                    processed_section = perform_analysis(section_data)
                    processed_section.to_excel(writer, sheet_name=section_name, index=False)

        output_file.seek(0)

        st.download_button(
            label="Download Sectioned Results",
            data=output_file,
            file_name='sectioned_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

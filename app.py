import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
from io import BytesIO  # Import BytesIO

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
    return None  # Fallback in case of unexpected values

# Streamlit app layout
st.title("Material Grading Application")
st.write("Upload an Excel file containing the Si and Fe values.")

# Upload the Excel file
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Load the data from the uploaded file
    data = pd.read_excel(uploaded_file)

    # Check the data structure
    st.write("Data Preview:")
    st.dataframe(data)

    # Ensure necessary columns are present
    if 'CELL' in data.columns and 'Si' in data.columns and 'Fe' in data.columns:
        # Fill missing values with zeros or another strategy
        data['Si'] = data['Si'].fillna(0)
        data['Fe'] = data['Fe'].fillna(0)

        # Apply grading function to each row
        data['Grade'] = data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

        # Display results
        st.write("Grading Results:")
        st.dataframe(data[['CELL', 'Si', 'Fe', 'Grade']])
        
        # Save results to an Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data.to_excel(writer, index=False, sheet_name='Grading Results')
        output.seek(0)

        # Add download button
        st.download_button(
            label="Download Grading Results",
            data=output,
            file_name='grading_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
from io import BytesIO
from itertools import combinations

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
        # Fill missing values with zeros and filter out rows with zero values
        data = data[(data['Si'].notnull()) & (data['Fe'].notnull()) & (data['Si'] > 0) & (data['Fe'] > 0)]

        # Apply grading function to each row
        data['Grade'] = data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

        # Generate combinations of the cells
        cell_combinations = list(combinations(data.index, 2))
        combination_results = []

        for (i, j) in cell_combinations:
            avg_si = (data.at[i, 'Si'] + data.at[j, 'Si']) / 2
            avg_fe = (data.at[i, 'Fe'] + data.at[j, 'Fe']) / 2
            combined_grade = assign_grade(avg_si, avg_fe)
            combination_results.append({
                'Cell_A': data.at[i, 'CELL'],
                'Cell_B': data.at[j, 'CELL'],
                'Avg_Si': avg_si,
                'Avg_Fe': avg_fe,
                'Combined_Grade': combined_grade
            })

        combination_df = pd.DataFrame(combination_results)

        # Pair cells based on the best grade without repeating cells
        paired_cells = {}
        unpaired_cells = set(data['CELL'])  # Start with all cells as unpaired

        for _, row in combination_df.iterrows():
            cell_a = row['Cell_A']
            cell_b = row['Cell_B']
            combined_grade = row['Combined_Grade']

            # If neither cell has been paired yet, pair them
            if cell_a not in paired_cells and cell_b not in paired_cells:
                paired_cells[cell_a] = cell_b
                unpaired_cells.discard(cell_a)
                unpaired_cells.discard(cell_b)

        # Convert paired_cells to a DataFrame for better visualization
        paired_df = pd.DataFrame(list(paired_cells.items()), columns=['Cell', 'Paired_With'])

        # Display results
        st.write("Grading Results:")
        st.dataframe(data[['CELL', 'Si', 'Fe', 'Grade']])

        st.write("Optimal Pairings Based on Combinations:")
        st.dataframe(paired_df)

        if unpaired_cells:
            st.write("Unpaired Cells:")
            st.write(list(unpaired_cells))
        
        # Save results to an Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data.to_excel(writer, index=False, sheet_name='Grading Results')
            paired_df.to_excel(writer, index=False, sheet_name='Optimal Pairings')
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

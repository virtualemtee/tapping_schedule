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
        # Fill missing values with zeros and filter out invalid rows
        data['Si'] = data['Si'].fillna(0)
        data['Fe'] = data['Fe'].fillna(0)
        filtered_data = data[(data['Si'] > 0) & (data['Fe'] > 0)]

        # Apply grading function to each row of filtered data
        filtered_data['Grade'] = filtered_data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

        # Display results for individual cells
        st.write("Grading Results for Individual Cells:")
        st.dataframe(filtered_data[['CELL', 'Si', 'Fe', 'Grade']])

        # Prepare lists to store pairings and unpaired cells
        all_pairings_data = []
        used_cells = set()

        # Iterate through filtered data to create pairings
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            # Skip cells already paired
            if cell_id in used_cells:
                continue

            # Initialize variables to find the best pair
            best_pairing = None
            best_combined_grade = None
            best_distance = float('inf')

            # Check for possible pairs
            for _, other_row in filtered_data.iterrows():
                other_cell_id = other_row['CELL']
                if other_cell_id == cell_id or other_cell_id in used_cells:
                    continue

                si_b = other_row['Si']
                fe_b = other_row['Fe']
                other_grade = other_row['Grade']

                # Compute average Si and Fe values
                avg_si = (si_a + si_b) / 2
                avg_fe = (fe_a + fe_b) / 2
                combined_grade = assign_grade(avg_si, avg_fe)

                # Calculate proximity and prioritize better grades
                distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                if combined_grade and distance < best_distance:
                    best_distance = distance
                    best_pairing = other_cell_id
                    best_combined_grade = combined_grade

            # If pairing is found, store it and mark cells as used
            if best_pairing:
                all_pairings_data.append({
                    "Base_Cell": cell_id,
                    "Pair_Cell": best_pairing,
                    "Resultant_Grade": best_combined_grade
                })
                used_cells.add(cell_id)
                used_cells.add(best_pairing)
            else:
                # If no pairing, record the cell with its own grade
                all_pairings_data.append({
                    "Base_Cell": cell_id,
                    "Pair_Cell": None,
                    "Resultant_Grade": individual_grade
                })
                used_cells.add(cell_id)

        # Display all pairings
        st.subheader("All Pairings Including Unpaired Cells:")
        st.dataframe(pd.DataFrame(all_pairings_data))

        # Optionally, save results to an Excel file
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            pd.DataFrame(all_pairings_data).to_excel(writer, sheet_name='All Pairings', index=False)
        
        output_file.seek(0)
        
        st.download_button(
            label="Download Grading Results",
            data=output_file,
            file_name='grading_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

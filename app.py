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

        # Prepare to compute averages for combinations
        suggested_schedule = []
        standalone_cells = []
        used_cells = set()  # Set to track used cells

        # Pairing logic remains the same as before
        # First pass: Poor Grades (1535 and 2050)
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            if individual_grade in ['1535', '2050'] and cell_id not in used_cells:
                best_pairing = None
                best_combined_grade = None
                best_distance = float('inf')  # Start with infinity
                
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    if other_grade in ['0506', '0610', '1020'] and other_cell_id not in used_cells:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)

                        if combined_grade not in ['1535', '2050']:
                            distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                            if distance < best_distance:
                                best_distance = distance
                                best_pairing = other_cell_id
                                best_combined_grade = combined_grade

                if best_pairing is None:
                    for _, other_row in filtered_data.iterrows():
                        other_cell_id = other_row['CELL']
                        si_b = other_row['Si']
                        fe_b = other_row['Fe']
                        other_grade = other_row['Grade']
                        
                        if other_grade in ['1535', '2050'] and other_cell_id != cell_id and other_cell_id not in used_cells:
                            avg_si = (si_a + si_b) / 2
                            avg_fe = (fe_a + fe_b) / 2
                            combined_grade = assign_grade(avg_si, avg_fe)

                            if combined_grade in ['1535', '2050']:
                                distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                                if distance < best_distance:
                                    best_distance = distance
                                    best_pairing = other_cell_id
                                    best_combined_grade = combined_grade

                if best_pairing is not None:
                    suggested_schedule.append({
                        "Base_Cell": cell_id,
                        "Paired_Cell": best_pairing,
                        "Resultant_Grade": best_combined_grade
                    })
                    used_cells.add(cell_id)
                    used_cells.add(best_pairing)

        # Pair acceptable grades (0506, 0610, 1020) with each other
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            if individual_grade in ['0506', '0610', '1020'] and cell_id not in used_cells:
                best_pairing = None
                best_combined_grade = None
                best_distance = float('inf')
                
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    if other_grade in ['0506', '0610', '1020'] and other_cell_id != cell_id and other_cell_id not in used_cells:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)

                        if combined_grade not in ['1535', '2050']:
                            distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                            if distance < best_distance:
                                best_distance = distance
                                best_pairing = other_cell_id
                                best_combined_grade = combined_grade

                if best_pairing is not None:
                    suggested_schedule.append({
                        "Base_Cell": cell_id,
                        "Paired_Cell": best_pairing,
                        "Resultant_Grade": best_combined_grade
                    })
                    used_cells.add(cell_id)
                    used_cells.add(best_pairing)

        # Handle any remaining cells as "Standalone Cells"
        for _, row in filtered_data.iterrows():
            cell_id = row['CELL']
            if cell_id not in used_cells:
                standalone_cells.append({
                    "Standalone_Cell": cell_id,
                    "Individual_Grade": row['Grade']
                })

        # Display the single consolidated table with paired results
        st.subheader("Suggested Tapping Schedule")
        st.dataframe(pd.DataFrame(suggested_schedule))

        # Display standalone cells table only if any unpaired cells remain
        if standalone_cells:
            st.subheader("Standalone Cells:")
            st.dataframe(pd.DataFrame(standalone_cells))

        # Save all results to Excel
        output_data = {
            "Suggested Tapping Schedule": suggested_schedule,
            "Standalone Cells": standalone_cells if standalone_cells else None
        }
        
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            pd.DataFrame(suggested_schedule).to_excel(writer, sheet_name="Suggested Tapping Schedule", index=False)
            if standalone_cells:
                pd.DataFrame(standalone_cells).to_excel(writer, sheet_name="Standalone Cells", index=False)
        
        output_file.seek(0)
        
        st.download_button(
            label="Download Grading Results",
            data=output_file,
            file_name='grading_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

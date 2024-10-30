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

        # Prepare to compute averages for combinations
        closest_improving_data = []
        pairable_grades_data = []
        acceptable_pairings_data = []
        remaining_cells = []
        additional_pairings = []  # To store additional pairings between acceptable and non-improved
        used_cells = set()  # Set to track used cells

        # First pass: Focus on poor grades
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            # Focus only on poor grades
            if individual_grade in ['1535', '2050'] and cell_id not in used_cells:
                best_pairing = None
                best_combined_grade = None
                best_distance = float('inf')  # Start with infinity
                
                # Create combinations with acceptable grades
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    # Check if the other cell is an acceptable grade and not already used
                    if other_grade in ['0506', '0610', '1020'] and other_cell_id not in used_cells:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)

                        # Update if this combination improves the grade
                        if combined_grade not in ['1535', '2050']:
                            distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                            if distance < best_distance:
                                best_distance = distance
                                best_pairing = other_cell_id
                                best_combined_grade = combined_grade

                # If no acceptable pair improved the grade, pair only with other poor grades
                if best_pairing is None:  # No acceptable grade found
                    for _, other_row in filtered_data.iterrows():
                        other_cell_id = other_row['CELL']
                        si_b = other_row['Si']
                        fe_b = other_row['Fe']
                        other_grade = other_row['Grade']
                        
                        # Only pair with other poor grades and not already used
                        if other_grade in ['1535', '2050'] and other_cell_id != cell_id and other_cell_id not in used_cells:
                            avg_si = (si_a + si_b) / 2
                            avg_fe = (fe_a + fe_b) / 2
                            combined_grade = assign_grade(avg_si, avg_fe)

                            # Only track if it remains a poor grade
                            if combined_grade in ['1535', '2050']:
                                distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                                if distance < best_distance:
                                    best_distance = distance
                                    best_pairing = other_cell_id
                                    best_combined_grade = combined_grade

                # Append the closest improving cell if found
                if best_pairing is not None:
                    closest_improving_data.append({
                        "Poor_Cell": cell_id,
                        "Improving_Cell": best_pairing,
                        "Resultant_Grade": best_combined_grade
                    })
                    # Mark both cells as used
                    used_cells.add(cell_id)
                    used_cells.add(best_pairing)

        # Second pass: Focus on pairable grades: 0303, 0404, 0406
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            # Focus on pairable grades: 0303, 0404, 0406
            if individual_grade in ['0303', '0404', '0406'] and cell_id not in used_cells:
                best_pairing = None
                best_combined_grade = None
                best_distance = float('inf')  # Start with infinity
                
                # Create combinations among themselves
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    # Only consider pairing within 0303, 0404, 0406 and not already used
                    if other_grade in ['0303', '0404', '0406'] and other_cell_id != cell_id and other_cell_id not in used_cells:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)

                        # Update if this combination improves the grade
                        if combined_grade in ['0404', '0406', '0303']:
                            distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                            if distance < best_distance:
                                best_distance = distance
                                best_pairing = other_cell_id
                                best_combined_grade = combined_grade

                # Append the closest pairing found if applicable
                if best_pairing is not None:
                    pairable_grades_data.append({
                        "Base_Cell": cell_id,
                        "Pairable_Cell": best_pairing,
                        "Resultant_Grade": best_combined_grade
                    })
                    # Mark both cells as used
                    used_cells.add(cell_id)
                    used_cells.add(best_pairing)

        # Third pass: Focus on acceptable grades: 0506, 0610, 1020
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            # Focus on acceptable grades
            if individual_grade in ['0506', '0610', '1020'] and cell_id not in used_cells:
                best_pairing = None
                best_combined_grade = None
                best_distance = float('inf')  # Start with infinity
                
                # Create combinations with other acceptable grades
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    # Only consider pairing within acceptable grades and not already used
                    if other_grade in ['0506', '0610', '1020'] and other_cell_id != cell_id and other_cell_id not in used_cells:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)

                        # Track if it improves the grade
                        if combined_grade not in ['1535', '2050']:
                            distance = abs(index - filtered_data[filtered_data['CELL'] == other_cell_id].index[0])
                            if distance < best_distance:
                                best_distance = distance
                                best_pairing = other_cell_id
                                best_combined_grade = combined_grade

                # Append if a pairing was found
                if best_pairing is not None:
                    acceptable_pairings_data.append({
                        "Acceptable_Cell": cell_id,
                        "Pairing_Cell": best_pairing,
                        "Resultant_Grade": best_combined_grade
                    })
                    # Mark both cells as used
                    used_cells.add(cell_id)
                    used_cells.add(best_pairing)

        # Pair remaining unpaired acceptable and non-improved grades
        unpaired_acceptables = [cell for cell in filtered_data['CELL'] if cell not in used_cells and filtered_data.loc[filtered_data['CELL'] == cell, 'Grade'].values[0] in ['0506', '0610', '1020']]
        unpaired_non_improved = [cell for cell in filtered_data['CELL'] if cell not in used_cells and filtered_data.loc[filtered_data['CELL'] == cell, 'Grade'].values[0] in ['0303', '0404', '0406']]

        for accept_cell in unpaired_acceptables:
            for non_improve_cell in unpaired_non_improved:
                si_accept = filtered_data.loc[filtered_data['CELL'] == accept_cell, 'Si'].values[0]
                fe_accept = filtered_data.loc[filtered_data['CELL'] == accept_cell, 'Fe'].values[0]
                si_non_improve = filtered_data.loc[filtered_data['CELL'] == non_improve_cell, 'Si'].values[0]
                fe_non_improve = filtered_data.loc[filtered_data['CELL'] == non_improve_cell, 'Fe'].values[0]

                avg_si = (si_accept + si_non_improve) / 2
                avg_fe = (fe_accept + fe_non_improve) / 2
                resultant_grade = assign_grade(avg_si, avg_fe)

                additional_pairings.append({
                    "Acceptable_Cell": accept_cell,
                    "Non_Improving_Cell": non_improve_cell,
                    "Resultant_Grade": resultant_grade
                })
                # Mark both as used
                used_cells.add(accept_cell)
                used_cells.add(non_improve_cell)
                break  # Exit after pairing one of each type

        # List any remaining unpaired cells
        for _, row in filtered_data.iterrows():
            cell_id = row['CELL']
            if cell_id not in used_cells:
                remaining_cells.append({
                    "Remaining_Cell": cell_id,
                    "Individual_Grade": row['Grade']
                })

        # Display the results
        st.subheader("Pairs for Poor Grades Bettered:")
        st.dataframe(pd.DataFrame(closest_improving_data))

        st.subheader("Pairs for Non-Improved Grades:")
        st.dataframe(pd.DataFrame(pairable_grades_data))

        st.subheader("Pairs for Acceptable Grades:")
        st.dataframe(pd.DataFrame(acceptable_pairings_data))

        st.subheader("Pairs for Acceptable and Non-Improved Grades:")
        st.dataframe(pd.DataFrame(additional_pairings))

        st.subheader("Remaining Cells without Pairs:")
        st.dataframe(pd.DataFrame(remaining_cells))


                # Combine all pairings and unpaired data into a summary table
        summary_data = []
        
        # Append paired cells for each category with necessary details
        for pairing in closest_improving_data:
            summary_data.append({
              #  "Type": "Poor Grades Bettered",
                "Main_Cell": pairing["Poor_Cell"],
                "Paired_Cell": pairing["Improving_Cell"],
                "Resultant_Grade": pairing["Resultant_Grade"]
            })
        
        for pairing in pairable_grades_data:
            summary_data.append({
              #  "Type": "Non-Improved Grades",
                "Main_Cell": pairing["Base_Cell"],
                "Paired_Cell": pairing["Pairable_Cell"],
                "Resultant_Grade": pairing["Resultant_Grade"]
            })
        
        for pairing in acceptable_pairings_data:
            summary_data.append({
           #     "Type": "Acceptable Grades",
                "Main_Cell": pairing["Acceptable_Cell"],
                "Paired_Cell": pairing["Pairing_Cell"],
                "Resultant_Grade": pairing["Resultant_Grade"]
            })
        
        for pairing in additional_pairings:
            summary_data.append({
           #     "Type": "Acceptable & Non-Improved",
                "Main_Cell": pairing["Acceptable_Cell"],
                "Paired_Cell": pairing["Non_Improving_Cell"],
                "Resultant_Grade": pairing["Resultant_Grade"]
            })
        
        # Append unpaired cells to the summary as well
        for cell in remaining_cells:
            summary_data.append({
          #      "Type": "Remaining Cells",
                "Main_Cell": cell["Remaining_Cell"],
                "Paired_Cell": None,
                "Resultant_Grade": cell["Individual_Grade"]
            })
        
        # Convert the summary to a DataFrame for display
        summary_df = pd.DataFrame(summary_data)
        
        # Display the overall summary table
        st.subheader("Overall Summary of Paired and Unpaired Cells")
        st.dataframe(summary_df)


                # Optionally, save results to an Excel file
        output_data = {
            "Poor Grades Bettered": closest_improving_data,  # Shortened
            "Non-Improved Grades": pairable_grades_data,      # Shortened
            "Acceptable Grades": acceptable_pairings_data,     # Shortened
            "Acceptable & Non-Improved": additional_pairings,  # Shortened
            "Remaining Cells": remaining_cells                 # Shortened
        }
        
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for sheet_name, data in output_data.items():
                pd.DataFrame(data).to_excel(writer, sheet_name=sheet_name, index=False)
        
        output_file.seek(0)
        
        st.download_button(
            label="Download Grading Results",
            data=output_file,
            file_name='grading_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

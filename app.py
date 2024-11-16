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
st.title("Tapping Schedule")
st.write("Upload cell purity Excel file to generate the tapping schedule.")
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    # Display uploaded data for verification
    st.write("Data Preview:")
    st.dataframe(data)
    
    if 'CELL' in data.columns and 'Si' in data.columns and 'Fe' in data.columns:
        # Fill missing Si and Fe values with 0
        data['Si'] = data['Si'].fillna(0)
        data['Fe'] = data['Fe'].fillna(0)
        data['Grade'] = data.apply(lambda row: assign_grade(row['Si'], row['Fe']), axis=1)

        # Divide the data into sections based on CELL column
        sections = {
            "Section_1": data[(data['CELL'] >= 1) & (data['CELL'] <= 25)],
            "Section_2": data[(data['CELL'] >= 26) & (data['CELL'] <= 50)],
            "Section_3": data[(data['CELL'] >= 51) & (data['CELL'] <= 75)],
            "Section_4": data[(data['CELL'] >= 76) & (data['CELL'] <= 100)]
        }

        output_data = {}

        # Process each section
        for section_name, section_data in sections.items():
            filtered_data = section_data[(section_data['Si'] > 0) & (section_data['Fe'] > 0)]

            closest_improving_data = []
            pairable_grades_data = []
            acceptable_pairings_data = []
            additional_pairings = []
            remaining_cells = []
            used_cells = set()

            # Perform pairing logic (as in the original code)
            for index, row in filtered_data.iterrows():
                cell_id = row['CELL']
                si_a = row['Si']
                fe_a = row['Fe']
                individual_grade = row['Grade']

                # Logic for improving poor grades
                if individual_grade in ['1535', '2050'] and cell_id not in used_cells:
                    best_pairing = None
                    best_combined_grade = None
                    best_distance = float('inf')

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
                        closest_improving_data.append({
                            "Cell": cell_id,
                            "Pair": best_pairing,
                            "Grade": best_combined_grade
                        })
                        used_cells.add(cell_id)
                        used_cells.add(best_pairing)

            # Add pairings for non-improved grades and acceptable grades here...

            # Remaining cells
            for _, row in filtered_data.iterrows():
                cell_id = row['CELL']
                if cell_id not in used_cells:
                    remaining_cells.append({
                        "Standalone": cell_id,
                        "Grade": row['Grade']
                    })

            # Compile section results
            section_summary = pd.DataFrame(closest_improving_data + pairable_grades_data + acceptable_pairings_data + additional_pairings + [{"Standalone": cell["Standalone"], "Grade": cell["Grade"]} for cell in remaining_cells])
            output_data[section_name] = section_summary

        # Save results to an Excel file with separate tabs
        output_file = BytesIO()
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for section_name, section_df in output_data.items():
                section_df.to_excel(writer, sheet_name=section_name, index=False)

        output_file.seek(0)

        # Allow downloading the file
        st.download_button(
            label="Download Sectioned Tapping Schedule",
            data=output_file,
            file_name='sectioned_tapping_schedule.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    else:
        st.error("Uploaded file must contain 'CELL', 'Si', and 'Fe' columns.")

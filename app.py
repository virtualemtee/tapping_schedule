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
        combination_data = []
        for index, row in filtered_data.iterrows():
            cell_id = row['CELL']
            si_a = row['Si']
            fe_a = row['Fe']
            individual_grade = row['Grade']

            # Focus only on poor grades
            if individual_grade in ['1535', '2050']:
                improved = False

                # Create combinations with acceptable grades
                for _, other_row in filtered_data.iterrows():
                    other_cell_id = other_row['CELL']
                    si_b = other_row['Si']
                    fe_b = other_row['Fe']
                    other_grade = other_row['Grade']

                    # Check if the other cell is an acceptable grade
                    if other_grade in ['0506', '0610', '1020']:
                        avg_si = (si_a + si_b) / 2
                        avg_fe = (fe_a + fe_b) / 2
                        combined_grade = assign_grade(avg_si, avg_fe)
                        if combined_grade not in ['1535', '2050']:
                            combination_data.append({
                                "Cell_A": cell_id,
                                "Cell_B": other_cell_id,
                                "Avg_Si": avg_si,
                                "Avg_Fe": avg_fe,
                                "Combined_Grade": combined_grade
                            })
                            improved = True  # Found an improving pair

                # If no acceptable pair improved the grade, pair only with other poor grades
                if not improved:
                    for _, other_row in filtered_data.iterrows():
                        other_cell_id = other_row['CELL']
                        si_b = other_row['Si']
                        fe_b = other_row['Fe']
                        other_grade = other_row['Grade']
                        
                        # Only pair with other poor grades
                        if other_grade in ['1535', '2050'] and other_cell_id != cell_id:
                            avg_si = (si_a + si_b) / 2
                            avg_fe = (fe_a + fe_b) / 2
                            combined_grade = assign_grade(avg_si, avg_fe)
                            combination_data.append({
                                "Cell_A": cell_id,
                                "Cell_B": other_cell_id,
                                "Avg_Si": avg_si,
                                "Avg_Fe": avg_fe,
                                "Combined_Grade": combined_grade
                            })

        # Create a DataFrame for combination results
        combinations_df = pd.DataFrame(combination_data)

        # Display combination results
        st.write("Grading Results for Combinations:")
        st.dataframe(combinations_df)

        # Save results to an Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_data.to_excel(writer, index=False, sheet_name='Individual Grading Results')
            combinations_df.to_excel(writer, index=False, sheet_name='Combination Grading Results')
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

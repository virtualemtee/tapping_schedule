# Streamlit app imports
import streamlit as st
import pandas as pd
import joblib
from itertools import combinations

# Load model and label encoder
model = joblib.load("paired_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Define grade ranking in descending order (good grades first)
grade_ranking = ["0303", "0404", "0406", "0506", "0610", "1020", "1535", "2050"]

# Title for the Streamlit App
st.title("Optimized Potline Cell Pairing Recommendation")

# File upload
uploaded_file = st.file_uploader("Upload Cell Data", type=["xlsx"])
if uploaded_file:
    # Load and preprocess data
    data = pd.read_excel(uploaded_file)
    data.columns = ["Cell", "Si", "Fe"]

    # Split data into sections
    sections = {
        1: data[data['Cell'].between(1, 25)],
        2: data[data['Cell'].between(26, 50)],
        3: data[data['Cell'].between(51, 75)],
        4: data[data['Cell'].between(76, 100)],
    }

    # Initialize list for storing the best pairs without reuse
    all_best_pairs = []

    # Iterate through each section, find the best pairs, and prioritize by grade
    for section_id, cells in sections.items():
        cells = cells.dropna()  # Exclude cells with missing values
        used_cells = set()  # Track cells that have already been paired

        section_best_pairs = []

        # Attempt to find pairs starting with the highest quality grade
        for target_grade in grade_ranking:
            # Generate all possible pairs in the section, but exclude reused cells
            available_cells = cells[~cells['Cell'].isin(used_cells)]
            cell_pairs = combinations(available_cells['Cell'].unique(), 2)

            # Check each pair for grade and prioritize the target grade
            for cell1, cell2 in cell_pairs:
                si1, fe1 = cells.loc[cells['Cell'] == cell1, ["Si", "Fe"]].values[0]
                si2, fe2 = cells.loc[cells['Cell'] == cell2, ["Si", "Fe"]].values[0]
                
                # Calculate the average Si and Fe for the pair
                avg_si = (si1 + si2) / 2
                avg_fe = (fe1 + fe2) / 2
                
                # Prepare the input DataFrame with feature names for the model
                input_data = pd.DataFrame({
                    "Pot1_Si": [si1], 
                    "Pot1_Fe": [fe1], 
                    "Pot2_Si": [si2], 
                    "Pot2_Fe": [fe2], 
                    "Avg_Si": [avg_si], 
                    "Avg_Fe": [avg_fe]
                })
                
                # Predict grade for this pairing
                pred = model.predict(input_data)
                grade = label_encoder.inverse_transform(pred)[0]

                # If the grade matches the target and neither cell is used, add it to best pairs
                if grade == target_grade and cell1 not in used_cells and cell2 not in used_cells:
                    section_best_pairs.append((cell1, cell2, grade))
                    used_cells.update([cell1, cell2])  # Mark cells as used

                    # Move to the next pair only if cells in current pair are unused and of best grade
                    break

        # Append the best pairs of the current section to the overall best pairs
        all_best_pairs.extend(section_best_pairs)

    # Display results in Streamlit
    st.write("Suggested Best Pairs Sorted by Grade (without cell reuse):")
    st.write(pd.DataFrame(all_best_pairs, columns=["Cell A", "Cell B", "Grade"]))

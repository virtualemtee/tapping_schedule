# Import libraries
import streamlit as st
import pandas as pd
import joblib
from itertools import combinations

# Load model and label encoder
model = joblib.load("paired_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Define grade ranking from best to worst for prioritizing suggestions
grade_ranking = ["0303", "0404", "0406", "0506", "0610", "1020", "1535", "2050"]

# Helper function to rank grades based on priority
def grade_rank(grade):
    try:
        return grade_ranking.index(grade)
    except ValueError:
        return len(grade_ranking)  # Assign lowest rank if grade is missing

# Streamlit app title and file upload
st.title("Potline Cell Pairing Optimization")
uploaded_file = st.file_uploader("Upload Cell Data (Excel file)", type=["xlsx"])

# Process file upload if provided
if uploaded_file:
    # Load and preprocess data
    data = pd.read_excel(uploaded_file)
    data.columns = ["Cell", "Si", "Fe"]

    # Drop rows where both Si and Fe are missing (offline cells)
    data = data.dropna(subset=["Si", "Fe"], how="all").reset_index(drop=True)

    # Split data into sections based on cell ranges for structured pairing
    sections = {
        1: data[data['Cell'].between(1, 25)],
        2: data[data['Cell'].between(26, 50)],
        3: data[data['Cell'].between(51, 75)],
        4: data[data['Cell'].between(76, 100)],
    }

    # Initialize list to store best pairs without reusing cells
    all_best_pairs = []

    # Iterate through each section, find the best pairs, and prioritize by grade
    for section_id, section_data in sections.items():
        used_cells = set()  # Track cells that have been paired

        # For each grade, generate all possible pairs within the section
        section_pairs = []
        for target_grade in grade_ranking:
            available_cells = section_data[~section_data["Cell"].isin(used_cells)]
            cell_pairs = combinations(available_cells["Cell"].unique(), 2)

            # Check each pair to find pairs matching the highest possible grade
            for cell1, cell2 in cell_pairs:
                # Retrieve Si and Fe values for both cells
                si1, fe1 = section_data.loc[section_data["Cell"] == cell1, ["Si", "Fe"]].values[0]
                si2, fe2 = section_data.loc[section_data["Cell"] == cell2, ["Si", "Fe"]].values[0]

                # Calculate the average Si and Fe for the pair
                avg_si = (si1 + si2) / 2
                avg_fe = (fe1 + fe2) / 2

                # Prepare input with correct feature names as used in model training
                input_data = pd.DataFrame({
                    "Si1": [si1], "Fe1": [fe1],
                    "Si2": [si2], "Fe2": [fe2],
                    "Avg_Si": [avg_si], "Avg_Fe": [avg_fe]
                })

                # Predict grade for this pairing
                pred = model.predict(input_data)
                grade = label_encoder.inverse_transform(pred)[0]

                # If grade matches the target and cells are available, pair them
                if grade == target_grade and cell1 not in used_cells and cell2 not in used_cells:
                    section_pairs.append((cell1, cell2, grade))
                    used_cells.update([cell1, cell2])  # Mark cells as used

                    # Move to next grade after finding the best available match
                    break

        # Add the section’s best pairs to the overall best pairs list
        all_best_pairs.extend(section_pairs)

    # Convert best pairs to DataFrame for display
    best_pairs_df = pd.DataFrame(all_best_pairs, columns=["Cell A", "Cell B", "Grade"])
    best_pairs_df["Rank"] = best_pairs_df["Grade"].apply(grade_rank)
    sorted_pairs_df = best_pairs_df.sort_values(by="Rank").reset_index(drop=True)

    # Display results in Streamlit
    st.write("Suggested Pairings Sorted by Grade (no cell reuse):")
    st.write(sorted_pairs_df[["Cell A", "Cell B", "Grade"]])

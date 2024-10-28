import streamlit as st
import pandas as pd
from itertools import combinations

# Title of the web app
st.title("Pot Pairing and Grading Analysis")

# Step 1: Upload the file
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Step 2: Load the data
    file_extension = uploaded_file.name.split('.')[-1]
    if file_extension == 'csv':
        df = pd.read_csv(uploaded_file)
    elif file_extension == 'xlsx':
        df = pd.read_excel(uploaded_file)

    st.write("Initial Data:")
    st.write(df.head())

    # Step 3: Convert Si and Fe columns to numeric
    df['Si'] = pd.to_numeric(df['Si'], errors='coerce')
    df['Fe'] = pd.to_numeric(df['Fe'], errors='coerce')

    # Step 4: Define purity grading function
    def calculate_grade(si, fe):
        if pd.isna(si) or pd.isna(fe):
            return None
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
        elif si >= 0.20 or fe >= 0.50:
            return '2050'
        else:
            return 'Undefined'

    # Apply grading function to each row
    df['grade'] = df.apply(lambda row: calculate_grade(row['Si'], row['Fe']), axis=1)

    # Drop rows with None values in the 'grade' column
    df = df.dropna(subset=['grade'])

    st.write("Data with Calculated Grades:")
    st.write(df)

    # Step 5: Generate possible pot pairings and calculate their combined grades
    def combined_grade(grade1, grade2):
        grade_priority = ['0303', '0404', '0406', '0506', '0610', '1020', '1535', '2050']
        combined_index = max(grade_priority.index(grade1), grade_priority.index(grade2))
        return grade_priority[combined_index]

    # Generate all possible unique pairs of pots
    pot_pairs = list(combinations(df['CELL'], 2))

    # Calculate the resulting grade for each pair and save to a list of dictionaries
    pair_results = []
    for pair in pot_pairs:
        pot1, pot2 = pair
        grade1 = df[df['CELL'] == pot1]['grade'].values[0]
        grade2 = df[df['CELL'] == pot2]['grade'].values[0]
        result_grade = combined_grade(grade1, grade2)

        # Only add the pair if the combined grade is at least 1020
        if result_grade in ['1020', '0610', '0506', '0406', '0404', '0303']:
            pair_results.append({
                'Pot1': pot1,
                'Pot2': pot2,
                'Grade1': grade1,
                'Grade2': grade2,
                'Combined_Grade': result_grade
            })

    # Convert the list to a DataFrame for easy analysis
    pair_df = pd.DataFrame(pair_results)

    # Step 6: Filter pairs by each grade and ensure each pot is only suggested once
    grade_priority = ['0303', '0404', '0406', '0506', '0610', '1020']
    selected_pots = set()
    suggested_pairs = []

    for grade in grade_priority:
        pairs_for_grade = pair_df[(pair_df['Combined_Grade'] == grade)]
        
        for _, row in pairs_for_grade.iterrows():
            if row['Pot1'] not in selected_pots and row['Pot2'] not in selected_pots:
                suggested_pairs.append({'Grade': grade, 'Pair': f"{row['Pot1']} & {row['Pot2']}"})
                selected_pots.add(row['Pot1'])
                selected_pots.add(row['Pot2'])

    # Convert the suggested pairs to a DataFrame
    suggested_pairs_df = pd.DataFrame(suggested_pairs, columns=['Grade', 'Pair'])

    # Identify any remaining pots that were not paired
    unpaired_pots = set(df['CELL']) - selected_pots
    unpaired_data = pd.DataFrame([{'Grade': 'Unpaired', 'Pair': pot} for pot in unpaired_pots])

    # Concatenate unpaired pots to the suggested pairs DataFrame
    suggested_pairs_df = pd.concat([suggested_pairs_df, unpaired_data], ignore_index=True)

    st.write("Suggested Pairings Table (Prioritizing Higher Purities):")
    st.write(suggested_pairs_df)

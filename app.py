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

    # Step 5: Generate possible pot pairings and calculate their combined averages and grades
    def average_grade(si1, fe1, si2, fe2):
        avg_si = (si1 + si2) / 2
        avg_fe = (fe1 + fe2) / 2
        return calculate_grade(avg_si, avg_fe)

    # Define the grades we want to avoid as primary pairings
    low_grades = ['1535', '2050']
    mid_grades = ['0406', '0506', '0610', '1020']

    # Generate all possible unique pairs of pots
    pot_pairs = list(combinations(df['CELL'], 2))

    # Calculate the resulting average grade for each pair
    pair_results = []
    for pot1, pot2 in pot_pairs:
        si1 = df.loc[df['CELL'] == pot1, 'Si'].values[0]
        fe1 = df.loc[df['CELL'] == pot1, 'Fe'].values[0]
        si2 = df.loc[df['CELL'] == pot2, 'Si'].values[0]
        fe2 = df.loc[df['CELL'] == pot2, 'Fe'].values[0]

        grade1 = df.loc[df['CELL'] == pot1, 'grade'].values[0]
        grade2 = df.loc[df['CELL'] == pot2, 'grade'].values[0]

        # Check if either of the pots has a low grade
        if grade1 in low_grades or grade2 in low_grades:
            # Calculate average and get new grade
            combined_grade = average_grade(si1, fe1, si2, fe2)
            pair_results.append({
                'Pot1': pot1,
                'Pot2': pot2,
                'Grade1': grade1,
                'Grade2': grade2,
                'Combined_Grade': combined_grade
            })

    # Convert the list to a DataFrame for easy analysis
    pair_df = pd.DataFrame(pair_results)

    # Step 6: Filter pairs by grade to ensure we're not using high purity pots to lower grades
    high_grade_results = []
    for pot1, pot2 in pot_pairs:
        si1 = df.loc[df['CELL'] == pot1, 'Si'].values[0]
        fe1 = df.loc[df['CELL'] == pot1, 'Fe'].values[0]
        si2 = df.loc[df['CELL'] == pot2, 'Si'].values[0]
        fe2 = df.loc[df['CELL'] == pot2, 'Fe'].values[0]

        grade1 = df.loc[df['CELL'] == pot1, 'grade'].values[0]
        grade2 = df.loc[df['CELL'] == pot2, 'grade'].values[0]

        # Check if both pots have mid grades
        if grade1 in mid_grades and grade2 in low_grades:
            combined_grade = average_grade(si1, fe1, si2, fe2)
            high_grade_results.append({
                'Pot1': pot1,
                'Pot2': pot2,
                'Grade1': grade1,
                'Grade2': grade2,
                'Combined_Grade': combined_grade
            })

    # Create a DataFrame for the results
    high_grade_results_df = pd.DataFrame(high_grade_results)

    st.write("Improvement Pairings (Low Grades with Mid Grades):")
    st.write(high_grade_results_df)

    st.write("All Possible Pairings with Resulting Grades:")
    st.write(pair_df)

# streamlit_app.py
import streamlit as st
import pandas as pd
from itertools import combinations

# Streamlit app setup and file uploader
st.title("Optimized Pot Pairing Grading App")
st.write("Upload your CSV or Excel file containing pot data with 'Si', 'Fe', and 'CELL' columns.")

# Upload file
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

if uploaded_file:
    # Load data based on file extension
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    
    # Display the uploaded data
    st.write("### Initial Data:")
    st.dataframe(df.head())

    # Convert Si and Fe columns to numeric
    df['Si'] = pd.to_numeric(df['Si'], errors='coerce')
    df['Fe'] = pd.to_numeric(df['Fe'], errors='coerce')

    # Define the grading function
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
        elif si >= 0.15 or fe >= 0.35:
            return '2050'
        else:
            return 'Undefined'

    # Apply grading function
    df['grade'] = df.apply(lambda row: calculate_grade(row['Si'], row['Fe']), axis=1)
    df = df.dropna(subset=['grade'])  # Drop rows where grade is None

    st.write("### Data with Calculated Grades:")
    st.dataframe(df)

    # Priority list for grades
    grade_priority = ['0303', '0404', '0406', '0506', '0610', '1020', '1535', '2050', 'Undefined']

    def get_best_grade_pair(pot, available_pots):
        """
        Tries to find the best pairing for a pot that maximizes the priority grade.
        If an optimal pairing for `0303` or `0404` is available, it prioritizes those.
        """
        pot_si = df[df['CELL'] == pot]['Si'].values[0]
        pot_fe = df[df['CELL'] == pot]['Fe'].values[0]
        
        best_partner = None
        best_grade = 'Undefined'
        
        for partner in available_pots:
            partner_si = df[df['CELL'] == partner]['Si'].values[0]
            partner_fe = df[df['CELL'] == partner]['Fe'].values[0]
            
            avg_si = (pot_si + partner_si) / 2
            avg_fe = (pot_fe + partner_fe) / 2
            avg_grade = calculate_grade(avg_si, avg_fe)
            
            # Prioritize pairings that achieve the best available grade
            if avg_grade in grade_priority and grade_priority.index(avg_grade) < grade_priority.index(best_grade):
                best_grade = avg_grade
                best_partner = partner

                # Stop if we reach optimal top grades
                if best_grade in ['0303', '0404']:
                    break
        
        return best_partner, best_grade

    # Automated pairing logic
    unpaired_pots = set(df['CELL'])
    suggested_pairs = []
    auto_trim_pots = df[df['grade'].isin(['0303', '0404'])]['CELL'].tolist()
    paired_pots = set()

    # Step 1: Attempt to pair all `0303` or `0404` cells first for optimal grades
    while auto_trim_pots:
        pot = auto_trim_pots.pop(0)
        best_partner, combined_grade = get_best_grade_pair(pot, auto_trim_pots)
        
        if best_partner:
            suggested_pairs.append({
                'Pot1': pot,
                'Pot2': best_partner,
                'Combined_Grade': combined_grade
            })
            paired_pots.update([pot, best_partner])
            auto_trim_pots.remove(best_partner)
        else:
            suggested_pairs.append({
                'Pot1': pot,
                'Pot2': None,
                'Combined_Grade': 'Standalone 0303 or 0404'
            })
            paired_pots.add(pot)

    # Remove already paired pots from the list of unpaired pots
    unpaired_pots -= paired_pots
    
    # Step 2: Pair remaining pots with the highest available grade
    while unpaired_pots:
        pot = unpaired_pots.pop()
        remaining_pots = list(unpaired_pots)
        
        if remaining_pots:
            best_partner, best_grade = get_best_grade_pair(pot, remaining_pots)
            
            if best_partner:
                suggested_pairs.append({
                    'Pot1': pot,
                    'Pot2': best_partner,
                    'Combined_Grade': best_grade
                })
                paired_pots.update([pot, best_partner])
                unpaired_pots.remove(best_partner)
    
    # Display the final optimized pairing table
    suggested_pairs_df = pd.DataFrame(suggested_pairs, columns=['Pot1', 'Pot2', 'Combined_Grade'])
    st.write("### Optimized Suggested Pairings Table:")
    st.dataframe(suggested_pairs_df)

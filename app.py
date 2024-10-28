# streamlit_app.py
import streamlit as st
import pandas as pd

# Streamlit app setup and file uploader
st.title("Enhanced Pot Pairing Grading App")
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

    def find_optimal_partner(pot, available_pots):
        """
        Finds the optimal partner for a pot to maximize grade improvement.
        It considers pairings that can result in higher-purity grades.
        """
        pot_si = df.loc[df['CELL'] == pot, 'Si'].values[0]
        pot_fe = df.loc[df['CELL'] == pot, 'Fe'].values[0]
        
        best_partner = None
        best_grade = 'Undefined'
        
        for partner in available_pots:
            partner_si = df.loc[df['CELL'] == partner, 'Si'].values[0]
            partner_fe = df.loc[df['CELL'] == partner, 'Fe'].values[0]
            
            # Calculate average Si and Fe for the pairing
            avg_si = (pot_si + partner_si) / 2
            avg_fe = (pot_fe + partner_fe) / 2
            avg_grade = calculate_grade(avg_si, avg_fe)
            
            # Choose pairing that achieves the highest-priority grade
            if avg_grade in grade_priority and grade_priority.index(avg_grade) < grade_priority.index(best_grade):
                best_grade = avg_grade
                best_partner = partner

        return best_partner, best_grade

    # Automated pairing logic
    unpaired_pots = set(df['CELL'])
    suggested_pairs = []
    auto_trim_pots = df[df['grade'].isin(['0303', '0404'])]['CELL'].tolist()
    paired_pots = set()

    # Step 1: Attempt to optimize pairs for high purity (like `0303`, `0404`)
    while auto_trim_pots:
        pot = auto_trim_pots.pop(0)
        best_partner, combined_grade = find_optimal_partner(pot, auto_trim_pots)
        
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

    # Step 2: Pair remaining pots aiming for the best available grade
    unpaired_pots -= paired_pots
    while unpaired_pots:
        pot = unpaired_pots.pop()
        remaining_pots = list(unpaired_pots)
        
        if remaining_pots:
            best_partner, best_grade = find_optimal_partner(pot, remaining_pots)
            
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

# streamlit_app.py
import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load the trained model and label encoder
model = joblib.load('pot_pairing_model.pkl')
label_encoder = joblib.load("label_encoder.pkl")

# Streamlit app setup
st.title("Pot Pairing Grading App")
st.write("Upload your CSV or Excel file containing pot data with 'CELL', 'Si', and 'Fe' columns.")

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
        # Use existing grading logic
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

    # Prepare data for model prediction
    def prepare_data_for_model(pot1_si, pot1_fe, pot2_si, pot2_fe):
        avg_si = (pot1_si + pot2_si) / 2
        avg_fe = (pot1_fe + pot2_fe) / 2
        return pd.DataFrame([[pot1_si, pot1_fe, pot2_si, pot2_fe, avg_si, avg_fe]],
                            columns=['Pot1_Si', 'Pot1_Fe', 'Pot2_Si', 'Pot2_Fe', 'Avg_Si', 'Avg_Fe'])

    # Collect all suggested pairs with grades
    suggested_pairs = []
    pot_cells = df['CELL'].tolist()

    # Iterate through all pairs of pots
    for i in range(len(pot_cells)):
        for j in range(i + 1, len(pot_cells)):
            pot1 = pot_cells[i]
            pot2 = pot_cells[j]

            pot1_si = df.loc[df['CELL'] == pot1, 'Si'].values[0]
            pot1_fe = df.loc[df['CELL'] == pot1, 'Fe'].values[0]
            pot2_si = df.loc[df['CELL'] == pot2, 'Si'].values[0]
            pot2_fe = df.loc[df['CELL'] == pot2, 'Fe'].values[0]
            
            # Prepare data for model prediction
            model_input = prepare_data_for_model(pot1_si, pot1_fe, pot2_si, pot2_fe)
            predicted_grade = model.predict(model_input)[0]

            suggested_pairs.append({
                'Pot1': pot1,
                'Pot2': pot2,
                'Predicted_Grade': predicted_grade
            })

    # Convert suggested pairs to DataFrame
    suggested_pairs_df = pd.DataFrame(suggested_pairs)

    # Sort by predicted grade to prioritize better purity grades
    # Assuming a lower string value means better grade (e.g., '0303' < '0610')
    grade_order = {
        '0303': 1,
        '0404': 2,
        '0406': 3,
        '0506': 4,
        '0610': 5,
        '1020': 6,
        '1535': 7,
        '2050': 8,
        'Undefined': 9
    }
    suggested_pairs_df['Grade_Score'] = suggested_pairs_df['Predicted_Grade'].map(grade_order)
    sorted_pairs_df = suggested_pairs_df.sort_values('Grade_Score').drop(columns='Grade_Score')

    # Display the final pairing table
    st.write("### Suggested Pairings Table (sorted by predicted grade):")
    st.dataframe(sorted_pairs_df)

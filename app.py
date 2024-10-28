import streamlit as st
import pandas as pd
from sklearn.pipeline import Pipeline
import joblib

# Load the trained model
model = joblib.load('pot_pairing_model.pkl')

# Step 1: Streamlit app setup and file uploader
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

    # Step 2: Convert Si and Fe columns to numeric
    df['Si'] = pd.to_numeric(df['Si'], errors='coerce')
    df['Fe'] = pd.to_numeric(df['Fe'], errors='coerce')

    # Step 3: Apply grading function to calculate grades based on the model
    df.dropna(subset=['Si', 'Fe'], inplace=True)  # Ensure no NaN values in critical columns
    df['Predicted_Grade'] = df.apply(lambda row: model.predict(pd.DataFrame([[row['Si'], row['Fe']]], columns=['Si', 'Fe']))[0], axis=1)

    st.write("### Data with Predicted Grades:")
    st.dataframe(df)

    # Step 4: Prepare data for model prediction
    def prepare_data_for_model(pot1_si, pot1_fe, pot2_si, pot2_fe):
        avg_si = (pot1_si + pot2_si) / 2
        avg_fe = (pot1_fe + pot2_fe) / 2
        return pd.DataFrame([[pot1_si, pot1_fe, pot2_si, pot2_fe, avg_si, avg_fe]],
                            columns=['Pot1_Si', 'Pot1_Fe', 'Pot2_Si', 'Pot2_Fe', 'Avg_Si', 'Avg_Fe'])

    # Step 5: Pair selection and result display
    suggested_pairs = []
    unpaired_pots = set(df['CELL'])

    # Create combinations of pots for potential pairings
    pot_combinations = [(pot1, pot2) for pot1 in unpaired_pots for pot2 in unpaired_pots if pot1 != pot2]

    for pot1, pot2 in pot_combinations:
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

    # Display the final pairing table
    suggested_pairs_df = pd.DataFrame(suggested_pairs, columns=['Pot1', 'Pot2', 'Predicted_Grade'])
    st.write("### Suggested Pairings Table:")
    st.dataframe(suggested_pairs_df)

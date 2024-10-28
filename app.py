import streamlit as st
import joblib
import pandas as pd

# Load the trained model and label encoder
model = joblib.load("pot_pairing_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Title of the app
st.title("Pot Pairing Prediction App")

# Input form
st.header("Enter the following features:")
pot1_si = st.number_input("Pot1 Si:", min_value=0.0, step=0.01)
pot1_fe = st.number_input("Pot1 Fe:", min_value=0.0, step=0.01)
pot2_si = st.number_input("Pot2 Si:", min_value=0.0, step=0.01)
pot2_fe = st.number_input("Pot2 Fe:", min_value=0.0, step=0.01)
avg_si = st.number_input("Average Si:", min_value=0.0, step=0.01)
avg_fe = st.number_input("Average Fe:", min_value=0.0, step=0.01)

# Button for prediction
if st.button("Predict"):
    # Prepare the input data for prediction
    input_data = pd.DataFrame({
        'Pot1_Si': [pot1_si],
        'Pot1_Fe': [pot1_fe],
        'Pot2_Si': [pot2_si],
        'Pot2_Fe': [pot2_fe],
        'Avg_Si': [avg_si],
        'Avg_Fe': [avg_fe]
    })
    
    # Make the prediction
    prediction = model.predict(input_data)
    predicted_grade = label_encoder.inverse_transform(prediction)
    
    # Display the result
    st.success(f"Predicted Grade: {predicted_grade[0]}")

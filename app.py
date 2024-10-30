# Streamlit app imports
import streamlit as st
import pandas as pd
import joblib
from itertools import combinations

# Load model and label encoder
model = joblib.load("paired_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

st.title("Potline Cell Pairing Recommendation")

# Upload the Excel file
uploaded_file = st.file_uploader("Upload Cell Data", type=["xlsx"])
if uploaded_file:
    data = pd.read_excel(uploaded_file)
    data.columns = ["Cell", "Si", "Fe"]

    sections = {1: data[data['Cell'].between(1, 25)],
                2: data[data['Cell'].between(26, 50)],
                3: data[data['Cell'].between(51, 75)],
                4: data[data['Cell'].between(76, 100)]}

    best_pairs = []

    for section_id, cells in sections.items():
        cells = cells.dropna()
        for cell1, cell2 in combinations(cells['Cell'].unique(), 2):
            si1, fe1 = cells.loc[cells['Cell'] == cell1, ["Si", "Fe"]].values[0]
            si2, fe2 = cells.loc[cells['Cell'] == cell2, ["Si", "Fe"]].values[0]
            avg_si, avg_fe = (si1 + si2) / 2, (fe1 + fe2) / 2

            pred = model.predict([[si1, fe1, si2, fe2, avg_si, avg_fe]])
            grade = label_encoder.inverse_transform(pred)[0]
            best_pairs.append((cell1, cell2, grade))

    st.write("Suggested Pairs:")
    st.write(best_pairs)

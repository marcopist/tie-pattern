import streamlit as st
import matplotlib.pyplot as plt
from pattern import TiePatternGenerator

st.set_page_config(page_title="Tie Pattern Generator", layout="wide")

st.title("👔 Custom Tie Pattern Generator")
st.markdown("Design your own 7-fold (or other) tie pattern and download the PDF.")

with st.sidebar:
    st.header("Dimensions")
    length = st.number_input("Total Length (cm)", value=135.0, step=1.0)
    wide_width = st.number_input("Wide Blade Width (cm)", value=6.0, step=0.1)
    narrow_width = st.number_input("Narrow Blade Width (cm)", value=4.0, step=0.1)
    neck_width = st.number_input("Neck Width (cm)", value=2.5, step=0.1)

    st.header("Construction")
    folds = st.selectbox("Number of Folds", options=[3, 5, 7], index=2)

    st.subheader("Cut Ratios (%)")
    st.caption("Where the tie is cut into 3 pieces (Wide, Neck, Narrow)")
    r1 = st.slider("First Cut Position (%)", 40, 60, 50)
    r2 = st.slider("Second Cut Length (%)", 20, 40, 30)
    # r3 is calculated
    r3 = 100 - r1 - r2
    st.text(f"Resulting Ratios: {r1} : {r2} : {r3}")

    if r3 <= 0:
        st.error("Invalid ratios! Sum must be < 100 for the first two.")

# Generate
generator = TiePatternGenerator(
    length_cm=length,
    wide_width_cm=wide_width,
    narrow_width_cm=narrow_width,
    neck_width_cm=neck_width,
    folds=folds,
    ratios=(r1, r2, r3)
)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Pattern Preview")
    try:
        fig = generator.plot_pattern()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating pattern: {e}")

with col2:
    st.subheader("Download")
    st.markdown("Get your production-ready PDF pattern.")

    # We generate the bytes eagerly for now as it's likely fast enough
    try:
        pdf_bytes = generator.export_pdf()
        st.download_button(
            label="Download PDF Pattern",
            data=pdf_bytes,
            file_name=f"tie_pattern_{folds}fold.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error preparing download: {e}")

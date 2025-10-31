import streamlit as st
import pandas as pd
import base64
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from dotenv import load_dotenv # Make sure dotenv is imported
from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_html_content,
)
from parse import parse_with_ollama, is_ollama_running

# --- Load Environment Variables ---
# This is now the first thing we do to ensure variables are loaded
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="AI Web Scraper",  # Changed title
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom CSS Injection ---
def load_css():
    st.markdown(
        """
        <style>
            /* Hide Streamlit's main menu and footer */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Vertically align items in all horizontal blocks */
            /* This will center the logo and title */
            div[data-testid="stHorizontalBlock"] {
                align-items: center;
            }

            /* Custom button styling (overrides theme) */
            .stButton>button {
                background-color: #E50914; /* A vibrant red */
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #F6121D; /* Brighter red on hover */
            }
            .stButton>button:active {
                background-color: #B20710; /* Darker red on click */
            }

            /* Style download buttons to be more subtle */
            .stDownloadButton>button {
                background-color: #2E8B57; /* Sea green */
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: normal;
                transition: background-color 0.3s ease;
            }
            .stDownloadButton>button:hover {
                background-color: #3CB371; /* Medium sea green */
            }
        
        </style>
        """,
        unsafe_allow_html=True,
    )

# PDF & Excel Export Functions
def to_excel(df):
    """Converts DataFrame to an in-memory Excel file."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()

def to_pdf(df):
    """Converts DataFrame to an in-memory PDF file."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    elements = []

    # Convert dataframe to list of lists
    # --- THIS IS THE FIX ---
    # Changed .to_list() to .tolist()
    data = [df.columns.tolist()] + df.values.tolist()
    # -----------------------

    # Create table style
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E8B57")), # Header color
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F0F0F0")), # Row color
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )

    # Create table
    col_widths = [((doc.width) / len(df.columns)) * 0.95] * len(df.columns)
    table = Table(data, colWidths=col_widths)
    table.setStyle(style)
    
    elements.append(table)
    doc.build(elements)
    return output.getvalue()

# Main App UI
load_css()

# Initialize session state variables
if "dom_content" not in st.session_state:
    st.session_state.dom_content = None
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None

# Header
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=80)
with col2:
    st.title("AI Web Scraper") 
    st.subheader("Provide a website URL and tell the AI what you want to extract.")

# Ollama Status
if is_ollama_running():
    st.sidebar.success("AI Status: Online")
else:
    st.sidebar.error("AI Status: Offline")
    st.sidebar.info("Ollama is not running. Please start your local Ollama server by typing 'ollama serve' in your terminal.")

st.divider()

# scraping the website 
st.header("Step 1: Scrape a Website")
st.info(
    "Enter a URL to scrape. This uses a proxy to bypass blocks and may take 15-30 seconds."
)
url = st.text_input(
    "Enter Website URL",
    placeholder="e.g., https://www.amazon.com/s?k=laptops",
    label_visibility="collapsed",
)

if st.button("Scrape Website"):
    if url:
        st.session_state.dom_content = None  # Clear previous content
        st.session_state.parsed_data = None # Clear previous data
        try:
            with st.spinner("Connecting to website... This may take a moment."):
                html_content = scrape_website(url)
            
            if html_content:
                body_content = extract_body_content(html_content)
                cleaned_content = clean_body_content(body_content)
                st.session_state.dom_content = cleaned_content
                st.success("Website scraped successfully! Ready for Step 2.")
            else:
                st.error("Failed to scrape the website. No content returned.")
        
        except Exception as e:
            st.error(f"An error occurred during scraping: {e}")
            st.exception(e) # To Show full traceback for debugging purposes
    else:
        st.warning("Please enter a URL to scrape.")


# Parsing section, shown only is scraping is successful
if st.session_state.dom_content:
    st.header("Step 2: Parse Content with AI")
    st.info("Your scraped content is ready. Now, tell the AI exactly what you want to extract.")

    parse_description = st.text_area(
        "Parsing Prompt",
        placeholder="e.g., 'Extract a table of all hotel names, their prices, and review scores.'",
        label_visibility="collapsed",
    )

    if st.button("Parse Content"):
        if parse_description:
            st.session_state.parsed_data = None # Clear old data
            try:
                with st.spinner("AI is analyzing content... This can take a moment."):
                    # Smart-split the HTML
                    html_chunks = split_html_content(st.session_state.dom_content)
                    
                    # Parse with Ollama
                    parsed_json_list = parse_with_ollama(
                        html_chunks, parse_description
                    )

                # Aggregate and display data
                all_data = []
                for json_obj in parsed_json_list:
                    if json_obj and "data" in json_obj:
                        all_data.extend(json_obj["data"])

                if not all_data:
                    st.warning("The AI finished, but did not find any matching data based on your prompt.")
                else:
                    # Convert to DataFrame for display and export
                    df = pd.DataFrame(all_data)
                    st.session_state.parsed_data = df # Save to session state
                    st.success("AI parsing complete! Here is your data.")

            except Exception as e:
                st.error(f"An unexpected error occurred during parsing: {e}")
                st.exception(e) # Show full traceback
        else:
            st.warning("Please describe what you want to parse.")

#  View and Download Data, this section appears only after parsing is done
if st.session_state.parsed_data is not None and not st.session_state.parsed_data.empty:
    
    st.header("Step 3: Your Extracted Data")
    
    df = st.session_state.parsed_data
    st.dataframe(df, use_container_width=True)

    st.subheader("Download Your Data")
    
    # Create columns for download buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV Download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv",
        )

    with col2:
        # Excel Download
        excel_data = to_excel(df)
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name="extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col3:
        # PDF Download
        pdf_data = to_pdf(df)
        st.download_button(
            label="📥 Download as PDF",
            data=pdf_data,
            file_name="extracted_data.pdf",
            mime="application/pdf",
        )


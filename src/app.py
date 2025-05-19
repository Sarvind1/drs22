"""Main Streamlit application for document review system."""

import streamlit as st
from datetime import datetime

from utils import (
    load_data,
    format_status_tag,
    format_portal_status,
    embed_pdf_base64,
    generate_comparison_pairs,
    export_audit_trail
)
from styles import STYLES

# Set page config
st.set_page_config(
    layout="wide",
    page_title="Document Review Panel",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
st.markdown(STYLES, unsafe_allow_html=True)

# Remove padding and margins
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .main > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'batch_statuses' not in st.session_state:
    st.session_state.batch_statuses = {}

if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = []

if 'review_notes' not in st.session_state:
    st.session_state.review_notes = ''

if 'review_decision' not in st.session_state:
    st.session_state.review_decision = 'Accept'

# Helper functions for state management
def on_batch_change():
    """Handle batch selection change."""
    update_document_options()

def on_doc_type_change():
    """Handle document type selection change."""
    update_document_options()

def update_document_options():
    """Update document version options based on current selections."""
    filtered = df[(df['batch'] == st.session_state.batch) & 
                 (df['type'] == st.session_state.doc_type)]
    versions = sorted(filtered['version'].unique())

    if len(versions) >= 1:
        if 'version_1' not in st.session_state or st.session_state.version_1 not in versions:
            st.session_state.version_1 = versions[0]
        if 'version_2' not in st.session_state or st.session_state.version_2 not in versions:
            st.session_state.version_2 = versions[1] if len(versions) > 1 else versions[0]

def get_batch_status(batch, doc_type):
    """Get the review status for a batch/document type combination."""
    key = f"{batch}/{doc_type}"
    return st.session_state.batch_statuses.get(key, 'not-reviewed')

# Load data
try:
    df = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()

# Prepare selection lists
batches = sorted(df['batch'].unique())
if 'batch' not in st.session_state and batches:
    st.session_state.batch = batches[0]
if 'doc_type' not in st.session_state:
    st.session_state.doc_type = 'CI'

update_document_options()

# Main layout
# title_col, download_col = st.columns([2, 1])
# with title_col:
#     st.title("Document Review Panel")

# Create main 2x3 grid layout
col1, col2 = st.columns([1, 1])  # 2/3 for main content, 1/3 for version comparison

# Left column contains both S1 and S2 stacked vertically
with col1:
    # Main layout with two columns
    #     st.title("Document Review Panel")

    # S1: Batch selection and Document type
    # with col1:
    st.title("Document Review Panel")

    st.selectbox("Select Batch", batches, key='batch', on_change=on_batch_change)
    if st.session_state.audit_trail:
        st.download_button(
            label="📊 Download Audit",
            data=export_audit_trail(st.session_state.audit_trail),
            file_name="audit_trail.csv",
            mime="text/csv"
            )
 
# Right column contains S3 (Version comparison)
with col2:
    col14, col16 = st.columns([3,2])
    with col14:
        st.markdown("### Document Comparison")
    with col16:
        st.radio("Document Type", ['CI','PL'], key='doc_type', 
                on_change=on_doc_type_change, horizontal=True)
    
    filtered = df[(df['batch'] == st.session_state.batch) & 
                 (df['type'] == st.session_state.doc_type)]
    versions = sorted(filtered['version'].unique())

    if len(versions) < 2:
        st.warning("Not enough versions available for comparison. At least 2 versions are required.")
        st.stop()
        
    pairs = generate_comparison_pairs(versions)
    if 'selected_comparison' not in st.session_state:
        st.session_state.selected_comparison = (versions[0], versions[1])

    # Create version comparison buttons
    st.markdown("#### Select Versions to Compare")
    cols = st.columns(3)
    for i, (v1, v2) in enumerate(pairs):
        label = f"Ver {v1} vs {v2}"
        col_index = i % 3
        with cols[col_index]:
            if st.button(label, key=f"btn_{v1}_{v2}", 
                        help=f"Compare version {v1} with version {v2}",
                        use_container_width=True):
                st.session_state.selected_comparison = (v1, v2)
                st.session_state.version_1, st.session_state.version_2 = v1, v2
                
                if st.session_state.selected_comparison == (v1, v2):
                    st.markdown("<p class='caption-selected'>✓ Selected</p>",
                              unsafe_allow_html=True)

# Document display section
st.markdown("---")
review_cols = st.columns(4)
# with review_cols[0]:
#     st.markdown("### Review Input")
with review_cols[0]:
    st.selectbox("Decision", ['Accept','Reject','Request More Information'],
                key='review_decision')
with review_cols[1]:
    st.text_input("Review Notes", key='review_notes')
with review_cols[3]:
    if st.button("Save Batch Review"):
        key = f"{st.session_state.batch}/{st.session_state.doc_type}"
        st.session_state.batch_statuses[key] = 'reviewed'
        entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'batch': st.session_state.batch,
            'doc_type': st.session_state.doc_type,
            'v1_v2': f"{st.session_state.version_1}-{st.session_state.version_2}",
            'status': 'reviewed',
            'notes': st.session_state.review_notes,
            'decision': st.session_state.review_decision
        }
        st.session_state.audit_trail.append(entry)
        st.success(f"Review saved for batch {st.session_state.batch} ({st.session_state.doc_type})")

# Display PDF comparison
if 'selected_comparison' in st.session_state:
    v1, v2 = st.session_state.selected_comparison
    col1, col2 = st.columns(2)
    
    with col1:
        v1_row = filtered[filtered['version']==v1]
        v1_status = v1_row['portal_status'].iloc[0] if not v1_row.empty else 'Unknown'
        v1_reason = v1_row['reason'].iloc[0] if not v1_row.empty else ''
        st.markdown(f"#### Version {v1} {format_portal_status(v1_status,v1_reason)}",
                   unsafe_allow_html=True)
        st.markdown(embed_pdf_base64(v1_row['file_path'].iloc[0] if not v1_row.empty else ''),
                   unsafe_allow_html=True)
    
    with col2:
        v2_row = filtered[filtered['version']==v2]
        v2_status = v2_row['portal_status'].iloc[0] if not v2_row.empty else 'Unknown'
        v2_reason = v2_row['reason'].iloc[0] if not v2_row.empty else ''
        st.markdown(f"#### Version {v2} {format_portal_status(v2_status,v2_reason)}",
                   unsafe_allow_html=True)
        st.markdown(embed_pdf_base64(v2_row['file_path'].iloc[0] if not v2_row.empty else ''),
                   unsafe_allow_html=True) 
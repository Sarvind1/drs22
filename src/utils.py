"""Utility functions for the document review system."""

import base64
import os
import pandas as pd
from datetime import datetime
from io import StringIO
import csv
import tempfile
from s3_utils import upload_file_to_s3, download_file_from_s3, get_s3_file_url, get_s3_client, get_full_s3_key
import streamlit as st
from s3_utils import get_secret

def load_data():
    """Load and prepare the review data."""
    try:
        # First try to load from S3
        try:
            s3_client = get_s3_client()
            # Test connection
            s3_client.list_objects(Bucket=get_secret('bucket_name'), MaxKeys=1)
            st.success("Successfully connected to S3")
            use_s3 = True
        except Exception as e:
            st.warning(f"S3 connection failed: {str(e)}")
            st.info("Using local demo data instead")
            use_s3 = False
            
        if os.path.exists("data/Manual_Review.csv"):
            df_batches = pd.read_csv("data/Manual_Review.csv")
        else:
            # Create demo data
            data = {
                'Batch': ['B001', 'B001', 'B002', 'B002', 'B003', 'B003'],
                'batch_count': [1, 2, 1, 2, 1, 2],
                'portal_status': ['Pending', 'Accepted', 'Rejected', 'Pending', 'Accepted', 'In Review'],
                'reason': ['', 'Approved by agent', 'Missing information', '', 'Complete documentation', 'Waiting for verification']
            }
            df_batches = pd.DataFrame(data)

        file_data = []
        for _, row in df_batches.iterrows():
            batch = row['Batch']
            count = row['batch_count']
            portal_status = row.get('portal_status', 'Unknown')
            reason = row.get('reason', '')

            for doc_type in ['CI', 'PL']:
                s3_key = f'{doc_type}/{batch}/{batch}_{count}.pdf'
                file_data.append({
                    'batch': batch,
                    'type': doc_type,
                    'version': count,
                    'file_path': s3_key,
                    'filename': f'{batch}_{count}.pdf',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'portal_status': portal_status,
                    'reason': reason
                })

        return pd.DataFrame(file_data)
    except Exception as e:
        raise Exception(f"Error loading data: {e}")

def format_status_tag(status):
    """Format the review status tag HTML."""
    cls = 'status-reviewed' if status == 'reviewed' else 'status-not-reviewed'
    label = 'Reviewed' if status == 'reviewed' else 'Not Reviewed'
    return f"<span class='status-tag {cls}'>{label}</span>"

def format_portal_status(status, reason=""):
    """Format the portal status tag HTML."""
    tooltip = f" title='{reason}'" if reason else ""
    return f"<span class='portal-status'{tooltip}>{status}</span>"

def embed_pdf_base64(s3_key):
    """Embed a PDF file from S3 as base64 in HTML."""
    try:
        # Download the PDF content from S3
        s3_client = get_s3_client()
        bucket_name = get_secret('bucket_name')
        full_key = get_full_s3_key(s3_key)
        
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=full_key)
            pdf_content = response['Body'].read()
            
            # Encode the PDF content as base64
            base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
            
            # Create the PDF viewer HTML using PDF.js
            pdf_display = f'''
                <div style="width:700px; height:1000px;">
                    <object
                        data="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{base64_pdf}"
                        type="text/html"
                        width="100%"
                        height="100%"
                        style="border: 1px solid #ddd; border-radius: 4px;"
                    >
                        <p>Unable to display PDF file. <a href="data:application/pdf;base64,{base64_pdf}" download="document.pdf">Download</a> instead.</p>
                    </object>
                </div>
            '''
            return pdf_display
        except Exception as s3_error:
            st.warning(f"Error fetching from S3: {str(s3_error)}")
            
            # Fallback to local file if it exists
            local_path = f"static/documents/{s3_key}"
            if os.path.exists(local_path):
                st.info(f"Using local file: {local_path}")
                with open(local_path, "rb") as f:
                    pdf_content = f.read()
                    base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
                    pdf_display = f'''
                        <div style="width:100%; height:60vh;">
                            <embed
                                type="application/pdf"
                                src="data:application/pdf;base64,{base64_pdf}"
                                width="100%"
                                height="100%"
                                style="border: 1px solid #ddd; border-radius: 4px;"
                            />
                        </div>
                    '''
                    return pdf_display
            else:
                # Display placeholder instead
                return f'''
                    <div style="width:100%; height:60vh; display:flex; align-items:center; justify-content:center; border:1px solid #ddd; background:#f8f9fa;">
                        <div style="text-align:center; padding:20px;">
                            <h3>PDF Preview Not Available</h3>
                            <p>S3 connection failed and no local fallback found</p>
                            <p>File path: {s3_key}</p>
                        </div>
                    </div>
                '''
    except Exception as e:
        return f"<div style='padding:20px; border:1px solid #ddd; background:#f9f9f9;'><h3>Error Loading PDF</h3><code>{str(e)}</code></div>"

def generate_comparison_pairs(versions):
    """Generate pairs of versions for comparison."""
    if len(versions) < 2:
        return []
    pairs = [(versions[i], versions[i+1]) for i in range(len(versions)-1)]
    if len(versions) > 2:
        pairs.append((versions[0], versions[-1]))
    return pairs

def export_audit_trail(audit_trail):
    """Export audit trail to CSV format and save to S3."""
    if not audit_trail:
        return ""

    all_keys = set().union(*(row.keys() for row in audit_trail))
    fieldnames = list(all_keys)

    # Create CSV in memory
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in audit_trail:
        writer.writerow({key: row.get(key) for key in fieldnames})
    
    # Save to temporary file and upload to S3
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(buffer.getvalue())
        temp_file.flush()
        
        # Generate S3 key with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        s3_key = f'audit/audit_trails/{timestamp}/audit_trail.csv'
        
        # Upload to S3
        upload_file_to_s3(temp_file.name, s3_key)
        
        # Clean up temporary file
        os.unlink(temp_file.name)
    
    return buffer.getvalue() 
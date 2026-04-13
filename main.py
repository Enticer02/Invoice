import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Riddhi Hardware Invoice", layout="wide")

# --- UI: INPUTS ---
with st.expander("Invoice Details", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        # Added Document Type Dropdown
        doc_type = st.selectbox("Document Type", ["Quotation", "Proforma Invoice"])
        client_name = st.text_input("Client Name", "ASTRAL PIPES LTD")
        client_gst = st.text_input("Client GST Number", "24XXXXXXXXXXXXZ1")
    with col2:
        client_mobile = st.text_input("Client Mobile Number", "9876543210")
        invoice_no = st.text_input("Invoice Number", "INV-001")
    with col3:
        invoice_date = st.date_input("Invoice Date", datetime.now())
        default_tax = st.number_input("Default GST Rate (%)", value=18.0, step=1.0)

# --- DATA ENTRY ---
default_row = {
    "SR": 1, 
    "PARTICULARS": "Item Name", 
    "HSN": "-", 
    "PCS": 0, 
    "QTY": 0.0, 
    "RATE": 0.0, 
    "DISC %": 0.0, 
    "GST %": 18.0
}

default_data = pd.DataFrame([default_row])

st.write("### Items List")
edited_df = st.data_editor(
    default_data, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "HSN": st.column_config.TextColumn(default="-"),
        "PCS": st.column_config.NumberColumn(default=0),
        "QTY": st.column_config.NumberColumn(default=0.0),
        "RATE": st.column_config.NumberColumn(default=0.0),
        "DISC %": st.column_config.NumberColumn(default=0.0),
        "GST %": st.column_config.NumberColumn(default=18.0),
    }
)

# --- LOGIC ---
if not edited_df.empty:
    edited_df["AMOUNT"] = edited_df["QTY"] * edited_df["RATE"] * (1 - edited_df["DISC %"]/100)
    edited_df["ROW_CGST"] = (edited_df["AMOUNT"] * (edited_df["GST %"] / 200))
    edited_df["ROW_SGST"] = edited_df["ROW_CGST"]
    
    total_taxable = edited_df["AMOUNT"].sum()
    total_cgst = edited_df["ROW_CGST"].sum()
    total_sgst = edited_df["ROW_SGST"].sum()
    
    grand_total_raw = total_taxable + total_cgst + total_sgst
    rounded_total = round(grand_total_raw)
    round_off = rounded_total - grand_total_raw

# --- PDF GENERATION ENGINE ---
class RiddhiPDF(FPDF):
    def __init__(self, doc_type_label, **kwargs):
        super().__init__(**kwargs)
        self.doc_type_label = doc_type_label

    def header(self):
        self.set_margins(10, 10, 10)
        if self.page_no() == 1:
            # Print Quotation/Proforma Invoice in Top Left
            self.set_font('helvetica', 'B', 10)
            self.cell(0, 5, self.doc_type_label.upper(), ln=False)
            
            # Center Title
            self.set_font('helvetica', 'B', 14)
            self.set_x(0)
            self.cell(0, 7, 'RIDDHI HARDWARE', align='C', ln=True)
            
            self.set_font('helvetica', '', 8)
            self.cell(0, 4, 'G-9 Swastik Apartment, Jivrajpark, Ahmedabad-380051', align='C', ln=True)
            self.cell(0, 4, 'Contact: +91 99999 99999 | Email: contact@riddhihardware.com', align='C', ln=True)
            self.ln(3)
            
            curr_y = self.get_y()
            self.set_font('helvetica', 'B', 9)
            self.text(10, curr_y + 4, f"Bill To: {client_name}")
            self.set_font('helvetica', '', 8)
            self.text(10, curr_y + 8, f"GST no: {client_gst}")
            self.text(10, curr_y + 12, f"Mobile: {client_mobile}")
            
            self.text(150, curr_y + 4, f"Invoice No: {invoice_no}")
            self.text(150, curr_y + 8, f"Date: {invoice_date.strftime('%d-%m-%Y')}")
            self.set_y(curr_y + 16)
        
        self.set_font('helvetica', 'B', 7)
        self.set_fill_color(230, 230, 230)
        self.widths = [8, 72, 15, 12, 15, 18, 12, 10, 28]
        headers = ["Sr", "Particulars", "HSN", "PCS", "Qty.", "Rate", "Disc %", "GST", "Amount"]
        for i, h in enumerate(headers):
            self.cell(self.widths[i], 6, h, border=1, fill=True, align='C')
        self.ln()

def generate_pdf(df, calcs, doc_type_label):
    pdf = RiddhiPDF(doc_type_label=doc_type_label)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("helvetica", size=7) 
    
    for index, row in df.iterrows():
        pdf.cell(pdf.widths[0], 5, str(index + 1), border=1, align='C')
        pdf.cell(pdf.widths[1], 5, str(row["PARTICULARS"])[:55], border=1, align='L')
        pdf.cell(pdf.widths[2], 5, str(row["HSN"]), border=1, align='C')
        pdf.cell(pdf.widths[3], 5, str(row["PCS"]), border=1, align='C')
        pdf.cell(pdf.widths[4], 5, str(row["QTY"]), border=1, align='C')
        pdf.cell(pdf.widths[5], 5, f"{row['RATE']:.2f}", border=1, align='R')
        pdf.cell(pdf.widths[6], 5, f"{row['DISC %']}%", border=1, align='C')
        pdf.cell(pdf.widths[7], 5, f"{row['GST %']}%", border=1, align='C')
        pdf.cell(pdf.widths[8], 5, f"{row['AMOUNT']:.2f}", border=1, align='R')
        pdf.ln()

    pdf.set_font('helvetica', 'B', 7)
    skip_width = sum(pdf.widths[:8])
    pdf.cell(skip_width, 6, "Total Taxable Amount (Excl. GST)", border=1, align='R')
    pdf.cell(pdf.widths[8], 6, f"{calcs['total_taxable']:.2f}", border=1, align='R', ln=True)

    pdf.ln(2)
    start_x = 135
    pdf.set_x(start_x)
    
    pdf.set_font("helvetica", '', 8)
    pdf.cell(30, 6, "CGST Total:", border=1)
    pdf.cell(35, 6, f"{calcs['total_cgst']:.2f}", border=1, align='R', ln=True)
    
    pdf.set_x(start_x)
    pdf.cell(30, 6, "SGST Total:", border=1)
    pdf.cell(35, 6, f"{calcs['total_sgst']:.2f}", border=1, align='R', ln=True)
    
    pdf.set_x(start_x)
    pdf.cell(30, 6, "Round off:", border=1)
    pdf.cell(35, 6, f"{calcs['round_off']:.2f}", border=1, align='R', ln=True)
    
    pdf.set_x(start_x)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 7, "GRAND TOTAL:", border=1, fill=True)
    pdf.cell(35, 7, f"{calcs['rounded_total']:.2f}", border=1, fill=True, align='R', ln=True)
    
    return bytes(pdf.output())

# --- DOWNLOAD ---
if not edited_df.empty:
    calcs = {
        "total_taxable": total_taxable,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "round_off": round_off, 
        "rounded_total": rounded_total
    }
    pdf_output = generate_pdf(edited_df, calcs, doc_type)
    st.download_button("📄 Download Invoice", pdf_output, f"{doc_type}_{invoice_no}.pdf", "application/pdf")
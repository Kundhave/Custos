from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)
lines = [
    "CUSTOS Regulatory Compliance Document",
    "Section 4.2 - Trading Limits",
    "The daily trading limit is 30000000 USD.",
    "The fat finger multiplier threshold is 50.",
    "Restricted securities list: BANNED_CORP, XYZ_HOLDINGS.",
    "Any order exceeding the daily limit must be rejected.",
    "Position limits apply to all equity instruments.",
    "Section 5.1 - Enforcement",
    "Violations must be reported within 24 hours.",
]
for line in lines:
    pdf.cell(200, 10, txt=line, ln=True)
pdf.output("test_regulation.pdf")
print("Done")
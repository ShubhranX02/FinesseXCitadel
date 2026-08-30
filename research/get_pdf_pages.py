from pypdf import PdfReader
reader = PdfReader("IITB_Team_Report_FinesseXCitadel.pdf")
print("Number of pages:", len(reader.pages))

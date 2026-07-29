import sys
from apply.ashby import apply_to_ashby

url = "https://jobs.ashbyhq.com/notion/5b15697c-fa91-4511-9482-c98a6ff29f90/application"
personal_info = {
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "phone": "555-555-5555"
}
pdf_path = "C:/Users/svspr/AppData/Local/SPravJobAI/resume.pdf"
# create a dummy pdf to test upload
with open(pdf_path, 'w') as f:
    f.write("dummy pdf")

print("Testing Ashby:", apply_to_ashby(url, personal_info, pdf_path))

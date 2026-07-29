import sys
from apply.smartrecruiters import apply_to_smartrecruiters

url = "https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer"
personal_info = {
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "phone": "555-555-5555"
}
pdf_path = "C:/Users/svspr/AppData/Local/SPravJobAI/resume.pdf"
print("Testing SmartRecruiters:", apply_to_smartrecruiters(url, personal_info, pdf_path))

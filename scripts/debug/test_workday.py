import sys
import asyncio
from apply.workday import apply_to_workday

url = "https://intel.wd1.myworkdayjobs.com/en-US/External/job/Senior-Software-Engineer_JR0285595"
personal_info = {
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "phone": "555-555-5555"
}
pdf_path = "C:/Users/svspr/AppData/Local/SPravJobAI/resume.pdf"
print("Testing Workday:", apply_to_workday(url, personal_info, pdf_path))

import requests
from bs4 import BeautifulSoup
import json

resp = requests.get("https://jobs.ashbyhq.com/Notion")
soup = BeautifulSoup(resp.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    if '/Notion/' in a['href']:
        links.append(a['href'])
print(json.dumps(links[:5], indent=2))

import re
import json
import os

KB_PATH = "knowledge_base/me.json"

# A conservative skill-token extractor.
# Looks for capitalized words, optionally with some symbols like C++, C#
SKILL_TOKEN_RE = re.compile(r'\b([A-Z][A-Za-z0-9+.#]{0,29}[A-Za-z0-9+#](?:\.[a-z]{2,4})?)(?!\w)')

STOPWORDS = {
    'the', 'and', 'for', 'with', 'you', 'your', 'our', 'this', 'that', 'these', 'those',
    'must', 'able', 'ability', 'strong', 'excellent', 'proven', 'a', 'an', 'or', 'in', 'of', 'to', 'as', 'is', 'are',
    'bachelor', 'bachelors', 'master', 'masters', 'degree', 'diploma', 'certification', 'certificate',
    'experience', 'years', 'year', 'senior', 'junior', 'entry', 'level', 'minimum', 'preferred', 'required',
    'candidates', 'candidate', 'applicants', 'applicant', 'ideal', 'successful',
    'knowledge', 'understanding', 'familiarity', 'exposure', 'background',
    'skills', 'skill', 'communication', 'team', 'teams', 'work', 'working',
    'development', 'software', 'engineer', 'engineering', 'design', 'architecture', 'solutions'
}

def extract_jd_skills(jd_text: str) -> list:
    """Extracts potential hard skills from JD text using purely mathematical Regex."""
    skills = set()
    for match in SKILL_TOKEN_RE.finditer(jd_text):
        token = match.group(1).strip()
        if token.lower() not in STOPWORDS and len(token) > 1:
            skills.add(token)
    return list(skills)

def load_user_kb_text() -> str:
    """Loads all textual data from me.json into a giant unformatted string for searching."""
    if not os.path.exists(KB_PATH):
        return ""
    with open(KB_PATH, "r") as f:
        data = json.load(f)
    
    # Dump everything into a flat string
    return json.dumps(data)

def skill_mentioned(skill: str, text: str) -> bool:
    """Case insensitive word boundary search."""
    escaped = re.escape(skill)
    # (?<!\w) and (?!\w) are equivalent to \b but work better with symbols like C++
    pattern = re.compile(rf'(?<!\w){escaped}(?!\w)', re.IGNORECASE)
    return bool(pattern.search(text))

ADJACENCY_MAP = {
    'react': ['vue', 'angular', 'svelte', 'next.js', 'react.js'],
    'vue': ['react', 'angular', 'svelte'],
    'angular': ['react', 'vue', 'svelte'],
    'aws': ['gcp', 'azure', 'cloud'],
    'gcp': ['aws', 'azure', 'cloud'],
    'azure': ['aws', 'gcp', 'cloud'],
    'python': ['java', 'c++', 'go', 'ruby', 'c#'],
    'java': ['python', 'c++', 'c#', 'go'],
    'c#': ['java', 'c++', 'python', '.net'],
    '.net': ['c#', 'java'],
    'sql': ['mysql', 'postgresql', 'postgres', 'nosql', 'mongodb'],
    'mysql': ['sql', 'postgresql', 'postgres'],
    'postgresql': ['sql', 'mysql', 'postgres'],
    'postgres': ['sql', 'mysql', 'postgresql'],
    'node': ['express', 'nest', 'deno', 'javascript', 'node.js'],
    'node.js': ['express', 'nest', 'deno', 'javascript', 'node'],
    'javascript': ['typescript', 'node.js', 'react', 'vue'],
    'typescript': ['javascript'],
    'docker': ['kubernetes', 'containers', 'k8s'],
    'kubernetes': ['docker', 'containers', 'k8s'],
    'k8s': ['docker', 'kubernetes', 'containers'],
    'machine learning': ['ai', 'deep learning', 'ml'],
    'ml': ['ai', 'deep learning', 'machine learning'],
    'ai': ['ml', 'machine learning', 'deep learning']
}

def analyze_skill_gap(jd_text: str) -> tuple[list, list, list]:
    """
    Returns (matched_skills, supported_skills, missing_skills)
    """
    jd_skills = extract_jd_skills(jd_text)
    user_text = load_user_kb_text()
    
    matched = []
    missing_initial = []
    
    for skill in jd_skills:
        if skill_mentioned(skill, user_text):
            matched.append(skill)
        else:
            missing_initial.append(skill)
            
    supported = []
    missing = []
    
    # Check for adjacent support
    for skill in missing_initial:
        lower_skill = skill.lower()
        is_supported = False
        
        # 1. Check strict adjacency map
        if lower_skill in ADJACENCY_MAP:
            for adjacent in ADJACENCY_MAP[lower_skill]:
                if any(adjacent == m.lower() for m in matched) or skill_mentioned(adjacent, user_text):
                    supported.append(skill)
                    is_supported = True
                    break
        
        # 2. Check simple substring (e.g. React.js missing but React matched)
        if not is_supported:
            for m in matched:
                if lower_skill in m.lower() or m.lower() in lower_skill:
                    supported.append(skill)
                    is_supported = True
                    break
                    
        if not is_supported:
            missing.append(skill)
            
    return matched, supported, missing

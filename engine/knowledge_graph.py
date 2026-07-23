import sqlite3
import os
from datetime import datetime

KG_DB_PATH = "knowledge_base/knowledge_graph.sqlite3"

def init_kg():
    os.makedirs(os.path.dirname(KG_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(KG_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS kg_triples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT,
            relation TEXT,
            target TEXT,
            valid_from TEXT,
            valid_to TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_triple(entity: str, relation: str, target: str, valid_from: str = None, valid_to: str = None):
    init_kg()
    if not valid_from:
        valid_from = datetime.utcnow().isoformat()
        
    conn = sqlite3.connect(KG_DB_PATH)
    c = conn.cursor()
    
    # Check if duplicate triple already exists
    c.execute("SELECT id FROM kg_triples WHERE entity = ? AND relation = ? AND target = ?", (entity, relation, target))
    if not c.fetchone():
        c.execute("INSERT INTO kg_triples (entity, relation, target, valid_from, valid_to) VALUES (?, ?, ?, ?, ?)",
                  (entity, relation, target, valid_from, valid_to))
        print(f"[Knowledge Graph] Stored Temporal Edge: [{entity}] --({relation})--> [{target}]")
    conn.commit()
    conn.close()

def query_entity(entity: str) -> list:
    """
    Retrieves all known relationships where the entity is either the source or the target.
    """
    init_kg()
    conn = sqlite3.connect(KG_DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT entity, relation, target, valid_from FROM kg_triples WHERE entity = ? OR target = ?", (entity, entity))
    results = c.fetchall()
    conn.close()
    
    return results

def get_entity_context(company_name: str) -> str:
    """
    Wraps query_entity to build a readable context string for the AI prompt.
    """
    results = query_entity(company_name)
    if not results:
        return f"No prior relationships or interactions known with {company_name}."
        
    context_lines = []
    for entity, relation, target, valid_from in results:
        date_str = valid_from[:10] if valid_from else "Unknown date"
        context_lines.append(f"- As of {date_str}: [{entity}] {relation} [{target}]")
        
    return "\n".join(context_lines)

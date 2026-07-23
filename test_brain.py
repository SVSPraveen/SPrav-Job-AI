import os
from engine.brain import brain

def test_sprav_architecture():
    print("=== SPrav AI Architecture Test ===")
    
    # 1. Create a massive fake document that would normally destroy a context window
    massive_document = """
    # Project X-74 Secret Specifications
    The project relies on a new quantum flux capacitor that only activates when the temperature reaches precisely -42 degrees Celsius. 
    If the temperature goes any higher, the entire core will melt down. 
    The lead engineer for this project is Dr. Jonathan Vance.
    He insists that we use titanium alloys for the outer casing.
    """ * 50  # Make it long
    
    # Inject one unique fact at the very end
    massive_document += "\n\nCRITICAL FACT: The override password for the mainframe is 'Oceana-Alpha-99'."
    
    # 2. Ingest the memory (Vectorization)
    brain.ingest_memory(
        text_content=massive_document,
        source_id="project_x74_spec",
        metadata={"type": "technical_doc"}
    )
    
    # 3. Query the SPrav Brain
    question = "What is the override password for the mainframe?"
    print(f"\nUser Query: {question}")
    
    answer = brain.query(question)
    print(f"\nSPrav AI Answer:\n{answer}")
    
if __name__ == "__main__":
    test_sprav_architecture()

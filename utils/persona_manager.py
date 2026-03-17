import os
import re

def load_personas(file_path=None):
    """
    Parses a markdown file into a dictionary of persona names and their prompts.
    Each persona is expected to be a header (e.g., # Persona Name).
    """
    if file_path is None:
        # Assume it's in the root of the project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "financial_persona_prompts.md")

    if not os.path.exists(file_path):
        # Fallback if file doesn't exist
        return {"General User": "Provide concise and accurate financial insights suitable for any user."}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by headers
    sections = re.split(r'^#\s+', content, flags=re.MULTILINE)
    
    personas = {}
    for section in sections:
        if not section.strip():
            continue
        
        lines = section.strip().split('\n')
        name = lines[0].strip()
        prompt = '\n'.join(lines[1:]).strip()
        
        if name:
            personas[name] = prompt
            
    return personas

def get_persona_names(file_path=None):
    return list(load_personas(file_path).keys())

def get_persona_prompt(name, file_path=None):
    personas = load_personas(file_path)
    return personas.get(name, personas.get("General User", "Provide concise and accurate financial insights suitable for any user."))

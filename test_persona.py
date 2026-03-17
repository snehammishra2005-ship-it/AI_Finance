import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.persona_manager import load_personas, get_persona_names, get_persona_prompt

def test_persona_manager():
    print("Testing Redesigned Persona Manager...")
    
    # Test load_personas
    personas = load_personas()
    print(f"Loaded {len(personas)} personas.")
    
    # Test get_persona_names
    names = get_persona_names()
    print(f"Persona names: {names}")
    
    # Test get_persona_prompt for Homemaker
    homemaker_prompt = get_persona_prompt("Homemaker")
    print(f"Homemaker Prompt: {homemaker_prompt}")
    assert "household budgeting" in homemaker_prompt
    
    # Test fallback
    general_prompt = get_persona_prompt("Unknown")
    print(f"Fallback Prompt: {general_prompt}")
    assert "concise and accurate" in general_prompt

if __name__ == "__main__":
    test_persona_manager()

import os
from google import genai
from google.genai import types

def generate_manim_code(prompt: str) -> str:
    """
    Given a user prompt, ask Gemini to generate Python code using the Manim library.
    Returns the python code as a string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return ""
    
    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are an expert at writing Manim code for generating math animations. "
            "Create a single class inheriting from Scene that fulfills the user's request. "
            "Return ONLY valid execution-ready python code, without any markdown formatting wrappers (like ```python ... ```). "
            "Make sure to import manim using `from manim import *` at the top. "
            "Make the animations visually beautiful, modern, and mathematically coherent. "
            "Ensure the default class name is always 'GeneratedScene'."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        code = response.text
        
        # Clean up in case the model returns markdown code blocks despite instructions
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
            
        return code.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return ""

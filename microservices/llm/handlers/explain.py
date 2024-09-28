from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI, OpenAIError
from pathlib import Path
from typing import List
import time
import json
import os

# Load the .env file from the parent directory
microservices_root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=microservices_root_dir / ".env")

# Set up Open AI client
client = OpenAI()

class Layer(BaseModel):
    what: str
    why: str
    how: str

class Concept(BaseModel):
    concept: str
    layers: List[Layer]

class Topic(BaseModel):
    topic: str
    concepts: List[Concept]

class StructuredExplanation(BaseModel):
    topics: List[Topic]
    main_takeaway: str


def generate_structured_explanation(text):
    """
    Generate a structured explanation of the given text using OpenAI's GPT model.

    This function analyzes the input text and produces a multi-layered explanation
    of the main topics and concepts within it. The explanation is structured into
    topics, concepts, and three layers of detail for each concept.

    Args:
        text (str): The input text to be analyzed and explained.

    Returns:
        StructuredExplanation: A structured object containing the explanation,
        including topics, concepts, and layered explanations.

    Raises:
        OpenAIError: If there's an issue with the OpenAI API call.
        JSONDecodeError: If the API response cannot be parsed as JSON.
    """

    prompt = f"""Analyze the following text and provide a structured explanation:

        1. Identify the main topics discussed in the text. The number of topics should reflect the content; there may be one dominant topic or multiple important topics.
        2. For each topic, list the key concepts. The number of concepts should be appropriate to fully represent the topic without redundancy.
        3. For each concept, provide a three-layered explanation using the 'What, Why, How' framework. Ensure that each layer builds upon the previous one, diving deeper without repeating information:
        - Layer 1: Provide a simple explanation for beginners. Be descriptive and use multiple sentences to explain the concept, why it is important, and how it works in layman's terms.
        - Layer 2: Build upon Layer 1 by providing a more detailed explanation with examples, analogies, or practical applications to illustrate the concept. Ensure it includes why it is significant in real-world scenarios and how it functions in practice. Introduce more complex aspects not covered in Layer 1.
        - Layer 3: Offer a thorough, technical explanation for advanced readers. Include technical definitions, components, and an in-depth exploration of how it operates on a technical level. Use examples from the field and explore its technical implications not discussed in previous layers.

        Ensure that the explanations across layers flow naturally, with each layer adding new information and insights rather than repeating previous content.

        4. Provide a short summary that captures the most significant takeaway from the entire text.

        Present the response in the following JSON format:

        {{
            "topics": [
                {{
                "topic": "Topic Name",
                "concepts": [
                    {{
                    "concept": "Concept Name",
                    "layers": [
                        {{
                        "layer_1": {{
                            "what": "Basic explanation of what it is.",
                            "why": "Simple explanation of why it's important.",
                            "how": "Basic explanation of how it works."
                        }}
                        }},
                        {{
                        "layer_2": {{
                            "what": "More detailed explanation, building on the previous layer",
                            "why": "Deeper exploration of its significance, with examples.",
                            "how": "More complex explanation of its mechanics, with practical applications."
                        }}
                        }},
                        {{
                        "layer_3": {{
                            "what": "Advanced technical definition and components.",
                            "why": "In-depth explanation of its importance on a technical level.",
                            "how": "Comprehensive technical explanation of its operation, with advanced examples."
                        }}
                        }}
                    ]
                    }}
                ]
                }}
            ],
            "main_takeaway": "A short summary capturing the most important point from the entire text."
        }}

        Text to analyze:
        {text}
    """

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing and explaining complex topics in a structured, multi-layered format. Identify all relevant topics and concepts without a predetermined number."},
                {"role": "user", "content": prompt}
            ],
            response_format=StructuredExplanation,
        )
        
        response_json = json.loads(completion.choices[0].message.content)
        print("Raw API response:", completion.choices[0].message.content)
        print("Parsed response:", response_json)
        result = StructuredExplanation(**response_json)
        print(f'Result: {result}')
        return result
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise
    except (IndexError, ValueError) as e:
        print(f"Unexpected response structure: {e}")
        raise

def generate_response(text):
    try:
        start_time = time.time()
        result = generate_structured_explanation(text)
        total_time = time.time() - start_time
        print(f'Total function runtime: {total_time:.2f} seconds')
        return {"explanations": result.model_dump()}
    except Exception as e:
        return f"Error: {str(e)}"
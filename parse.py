import json
import requests
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import LangChainException

# Load environment variables (like model name, if you add one)
load_dotenv()

# Define the model to use
# Make sure you have 'ollama pull llama3.1'
model = OllamaLLM(model="llama3.1", format="json")

# Define the JSON structure we want
parser = JsonOutputParser()

# --- PROMPT TEMPLATE ---
# This is the prompt that finally fixed the KeyError.
# We "escape" the curly braces around "data" so LangChain ignores them.
template = """
You are an expert HTML parsing assistant. A user will provide you with a chunk of HTML and a parsing instruction.
Your goal is to extract the requested information and return it ONLY as a valid JSON object.

Follow these instructions:
1.  Parse the HTML to find the data that matches the user's request.
2.  Format the extracted data into a JSON object. The object must have a single key "data", which holds a list of the extracted items.
3.  If no data is found, you MUST return: {{"data": []}}
4.  Do not include any other text, apologies, or explanations. Only return the JSON.

Parsing Request:
{parse_description}

HTML Content:
{dom_content}
"""

prompt = ChatPromptTemplate.from_template(template)

# --- CHAINS ---
# The main chain for parsing
chain = prompt | model | parser

def parse_with_ollama(html_chunks, parse_description):
    """
    Parses a list of HTML chunks in parallel using Ollama.
    """
    
    # Create a list of inputs for the batch operation
    # Each chunk gets the same parse_description
    batch_inputs = [
        {"dom_content": chunk, "parse_description": parse_description}
        for chunk in html_chunks
    ]

    print(f"Starting parallel parsing of {len(batch_inputs)} chunks...")

    # Use .batch() to run all chunks in parallel
    # This is much faster than a for loop.
    results = chain.batch(batch_inputs)
    
    print("Parallel parsing complete.")
    return results


def is_ollama_running():
    """
    Checks if the Ollama server is running on the default port.
    """
    try:
        # We check the default Ollama API endpoint
        response = requests.get("http://localhost:11434")
        return response.status_code == 200
    except requests.ConnectionError:
        # If it can't connect, it's not running
        return False
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Error checking Ollama status: {e}")
        return False


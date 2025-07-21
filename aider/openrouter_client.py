import os
import json
from dotenv import load_dotenv
import litellm

def load_openrouter_key():
    load_dotenv()
    return os.getenv("OPENROUTER_API_KEY")

def send_prompt_to_openrouter(prompt_string, model_name="google/gemini-flash-1.5"):
    api_key = load_openrouter_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")

    messages = [{"role": "user", "content": prompt_string}]

    try:
        response = litellm.completion(
            model=model_name,
            messages=messages,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        raw_response = response.json()
        parsed_response = response.choices[0].message.content
        return raw_response, parsed_response
    except Exception as e:
        print(f"Error sending prompt to OpenRouter: {e}")
        return None, None

if __name__ == "__main__":
    # Example usage:
    # Create a .env file in the project root with OPENROUTER_API_KEY="your_key_here"
    # For testing, you might want to use a dummy key or mock the litellm.completion call
    test_prompt = "What is the capital of France?"
    raw, parsed = send_prompt_to_openrouter(test_prompt)

    if raw and parsed:
        print("Raw Response:")
        print(json.dumps(raw, indent=2))
        print("\nParsed Response:")
        print(parsed)
    else:
        print("Failed to get response from OpenRouter.")

#!/usr/bin/env python

import os
import sys
import json
import requests

class OpenRouterClient:
    """A simplified client for making requests to the OpenRouter API."""

    def __init__(self, api_key, model_tiers=None):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model_tiers = model_tiers if model_tiers is not None else {}

    def send_request(self, model, messages):
        """Sends a request to the specified model and streams the response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        try:
            with requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, stream=True) as response:
                response.raise_for_status()
                for chunk in response.iter_lines():
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        if decoded_chunk.startswith("data: "):
                            json_str = decoded_chunk[len("data: "):]
                            if json_str.strip() == "[DONE]":
                                break
                            try:
                                json_obj = json.loads(json_str)
                                if "choices" in json_obj and json_obj["choices"]:
                                    if "delta" in json_obj["choices"][0] and "content" in json_obj["choices"][0]["delta"]:
                                        yield json_obj["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                # Ignore chunks that are not valid JSON
                                pass
        except requests.exceptions.RequestException as e:
            print(f"\nError making request to OpenRouter: {e}", file=sys.stderr)
            return
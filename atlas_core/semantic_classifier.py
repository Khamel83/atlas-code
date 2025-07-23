import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticClassifier:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.intents = {
            "generate": [
                "create new code", "write a script", "build a function", "generate a program"
            ],
            "edit": [
                "modify this file", "change the code", "update a function", "refactor this"
            ],
            "debug": [
                "fix this bug", "debug the error", "troubleshoot the issue", "resolve the problem"
            ],
            "review": [
                "review this code", "check for improvements", "analyze the quality", "provide feedback"
            ],
            "optimize": [
                "optimize performance", "make it faster", "reduce memory usage", "improve efficiency"
            ],
            "format": [
                "format the code", "clean up style", "lint this file", "beautify the code"
            ],
            "explain": [
                "explain this code", "document the function", "how does this work", "describe the logic"
            ]
        }
        self.embeddings = self._precompute_embeddings()

    def _precompute_embeddings(self):
        embeddings = {}
        for intent, examples in self.intents.items():
            embeddings[intent] = self.model.encode(examples)
        return embeddings

    def classify(self, text):
        text_embedding = self.model.encode([text])[0]
        
        best_intent = "default"
        max_similarity = -1

        for intent, example_embeddings in self.embeddings.items():
            for example_embedding in example_embeddings:
                similarity = np.dot(text_embedding, example_embedding) / (np.linalg.norm(text_embedding) * np.linalg.norm(example_embedding))
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_intent = intent
        
        return best_intent, max_similarity

import unittest
from unittest.mock import patch, MagicMock
import json
from handlers import explain  # Assuming the file is named explain.py
from openai import OpenAIError

class TestExplain(unittest.TestCase):

    @patch('handlers.explain.client.beta.chat.completions.parse')
    def test_generate_structured_explanation_success(self, mock_parse):
        # Mocking the response from OpenAI API with a structured explanation
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "topics": [
                    {
                        "topic": "Test Topic",
                        "concepts": [
                            {
                                "concept": "Test Concept",
                                "layers": [
                                    {
                                        "what": "Test what",
                                        "why": "Test why",
                                        "how": "Test how"
                                    },
                                    {
                                        "what": "Test what 2",
                                        "why": "Test why 2",
                                        "how": "Test how 2"
                                    },
                                    {
                                        "what": "Test what 3",
                                        "why": "Test why 3",
                                        "how": "Test how 3"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "main_takeaway": "Test takeaway"
            })))
        ]
        mock_parse.return_value = mock_response

        # Call the function
        result = explain.generate_structured_explanation("Test input")

        # Assert the result
        self.assertEqual(len(result.topics), 1)
        self.assertEqual(result.topics[0].topic, "Test Topic")
        self.assertEqual(len(result.topics[0].concepts), 1)
        self.assertEqual(result.topics[0].concepts[0].concept, "Test Concept")
        self.assertEqual(len(result.topics[0].concepts[0].layers), 3)
        self.assertEqual(result.topics[0].concepts[0].layers[0].what, "Test what")
        self.assertEqual(result.topics[0].concepts[0].layers[1].what, "Test what 2")
        self.assertEqual(result.main_takeaway, "Test takeaway")

    @patch('handlers.explain.client.beta.chat.completions.parse')
    def test_generate_structured_explanation_openai_error(self, mock_parse):
        # Simulate an OpenAIError
        mock_parse.side_effect = OpenAIError("API Error")

        # Assert that the function raises the error
        with self.assertRaises(OpenAIError):
            explain.generate_structured_explanation("Test input")

    @patch('handlers.explain.client.beta.chat.completions.parse')
    def test_generate_structured_explanation_json_error(self, mock_parse):
        # Simulate invalid JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Invalid JSON"))]
        mock_parse.return_value = mock_response

        # Assert that the function raises a JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            explain.generate_structured_explanation("Test input")

if __name__ == '__main__':
    unittest.main()
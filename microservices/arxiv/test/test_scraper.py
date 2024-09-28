import unittest
from unittest.mock import patch, MagicMock
from handlers.arxiv_client import ArXivClient

class TestArXivScraperClient(unittest.TestCase):
    def setUp(self):
        self.scraper = ArXivClient()

    @patch('handlers.arxiv_scraper.arxiv.Search')
    def test_get_random_papers(self, mock_search):
        # Mock the arxiv.Search results
        mock_result = MagicMock()
        mock_result.entry_id = 'http://arxiv.org/abs/1234.5678'
        mock_result.title = 'Test Paper'
        mock_result.summary = 'This is a test abstract.'
        mock_author = MagicMock()
        mock_author.name = 'John Doe'
        mock_result.authors = [mock_author]
        mock_result.published = MagicMock(strftime=MagicMock(return_value='2023-01-01'))
        mock_result.pdf_url = 'http://arxiv.org/pdf/1234.5678'

        mock_search.return_value.results.return_value = [mock_result]

        # Call the method
        papers = self.scraper.get_random_papers(num_categories=1, papers_per_category=1)

        # Assertions
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper['id'], '1234.5678')
        self.assertEqual(paper['title'], 'Test Paper')
        self.assertEqual(paper['abstract'], 'This is a test abstract.')
        self.assertIn(paper['category'], self.scraper.categories)
        self.assertEqual(paper['authors'], 'John Doe')
        self.assertEqual(paper['published'], '2023-01-01')
        self.assertEqual(paper['abstract_url'], 'http://arxiv.org/abs/1234.5678')
        self.assertEqual(paper['pdf_url'], 'http://arxiv.org/pdf/1234.5678')

    def test_extract_abstract(self):
        text = "This is a test abstract.\nIt has multiple lines."
        result = self.scraper.extract_abstract(text)
        self.assertEqual(result, "This is a test abstract. It has multiple lines.")

if __name__ == '__main__':
    unittest.main()
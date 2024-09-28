import random
import arxiv
import json
import time
import os


class ArXivClient:
    def __init__(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), 'arxiv_papers.json')
        self.categories = [
            'astro-ph', 'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat', 
            'hep-ph', 'hep-th', 'math-ph', 'nlin', 'nucl-ex', 
            'nucl-th', 'physics', 'quant-ph', 'math', 'cs'
        ]

    def get_random_papers_cache(self, cache_path, num_papers=3):
        with open(cache_path, 'r') as f:
            all_papers = json.load(f)

        # Ensure we don't try to sample more papers than are available
        num_papers = min(num_papers, len(all_papers))

        # Randomly sample the specified number of papers
        selected_papers = random.sample(all_papers, num_papers)

        return selected_papers

    def get_random_papers(self, num_categories=4, papers_per_category=1):

        if os.path.exists(self.cache_path):
            print('Loading papers from cache...')
            time.sleep(1)
            return self.get_random_papers_cache(self.cache_path, 3)
        
        print('Cache not found. Fetching from arXiv...')
        selected_categories = random.sample(self.categories, num_categories)
        papers = []

        for category in selected_categories:
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=papers_per_category,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            for result in search.results():
                papers.append({
                    'id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'abstract': self.extract_abstract(result.summary),
                    'category': category,
                    'authors': ', '.join(author.name for author in result.authors),
                    'published': result.published.strftime("%Y-%m-%d"),
                    'abstract_url': result.entry_id,
                    'pdf_url': result.pdf_url
                })

        return papers

    @staticmethod
    def extract_abstract(text):
        return text.replace('\n', ' ').strip()
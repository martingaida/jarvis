from handlers.arxiv_client import ArXivClient
import json


def lambda_handler(event, context):
    scraper = ArXivClient()
    papers = scraper.get_random_papers(num_categories=3, papers_per_category=1)
    print(f'Response: {papers}')

    return {
        'statusCode': 200,
        'body': json.dumps(papers, indent=2)
    }
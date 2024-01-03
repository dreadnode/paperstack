import argparse
import os

from notion_utils import (
    get_notion_client,
    get_papers_from_notion,
    write_papers_to_notion,
)
from arxiv_utils import fill_papers_with_arxiv, search_arxiv_as_paper
from openai_utils import (
    get_focus_label_from_abstract,
    get_openai_client,
    summarize_abstract_with_openai,
)
from scholar_utils import get_recommended_arxiv_ids_from_semantic_scholar

ARXIV_SEARCH = """\
"adversarial attacks" OR "language model attacks" OR "LLM vulnerabilities" OR \
"AI security" OR "machine learning security" OR "jailbreak" OR "bypassing AI"\
"""


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--notion-token",
        type=str,
        default=os.environ.get("NOTION_TOKEN"),
        help="Notion token",
    )
    parser.add_argument(
        "--database-id",
        type=str,
        default=os.environ.get("NOTION_DATABASE_ID"),
        help="Notion database id",
    )
    parser.add_argument(
        "--openai-token",
        type=str,
        default=os.environ.get("OPENAI_API_TOKEN"),
        help="OpenAI token",
    )
    parser.add_argument("--arxiv-search-query", type=str, default=ARXIV_SEARCH)
    parser.add_argument("--search-arxiv", action="store_true", default=False)
    parser.add_argument("--search-semantic-scholar", action="store_true", default=False)

    args = parser.parse_args()

    print("[+] Paperstack")

    notion_client = get_notion_client(args.notion_token)
    openai_client = get_openai_client(args.openai_token)

    # Get papers from Notion
    print(" |- Getting papers from Notion")
    papers = get_papers_from_notion(notion_client, args.database_id)

    # Fill in missing data from arXiv
    print(" |- Filling in missing data from arXiv")
    papers = fill_papers_with_arxiv(papers)

    if args.search_arxiv:
        # Search arXiv for new papers and deduplicate
        print(" |- Searching arXiv")
        existing_titles = [paper.title for paper in papers]
        for searched_paper in search_arxiv_as_paper(args.arxiv_search_query, max_results=10):
            if searched_paper.title not in existing_titles:
                print(f"    |- {searched_paper.title[:50]}...")
                papers.append(searched_paper)

    if args.search_semantic_scholar:
        print(" |- Getting related papers from Semantic Scholar")
        recommended_papers = get_recommended_arxiv_ids_from_semantic_scholar(papers)
        papers.extend(fill_papers_with_arxiv(recommended_papers))
        print(f"    |- {len(recommended_papers)} new papers")

    # Build summaries
    print(" |- Building summaries")
    for paper in papers:
        if not paper.summary and paper.abstract:
            print(f"    |- {paper.title[:50]}...")
            paper.summary = summarize_abstract_with_openai(
                openai_client, paper.abstract
            )

    # Assigning focus labels
    print(" |- Assigning focus labels")
    for paper in papers:
        if not paper.focus:
            paper.focus = get_focus_label_from_abstract(openai_client, paper.abstract)
            print(f"    |- {paper.focus}")

    print(f" |- Writing back to Notion [{len(papers)}]...")
    write_papers_to_notion(notion_client, args.database_id, papers)


if __name__ == "__main__":
    main()

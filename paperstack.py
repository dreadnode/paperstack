import argparse
import os

from arxiv_utils import fill_papers_with_arxiv, search_arxiv_as_paper
from notion_utils import (
    get_notion_client,
    get_papers_from_notion,
    write_papers_to_notion,
)
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

    print(f" |- Getting papers from Notion [{args.database_id}]")
    papers = get_papers_from_notion(notion_client, args.database_id)

    if not all([p.has_arxiv_props() for p in papers]):
        print(" |- Filling in missing data from arXiv")
        papers = fill_papers_with_arxiv(papers)

    if args.search_arxiv:
        print(" |- Searching arXiv for new papers")
        existing_titles = [paper.title for paper in papers]
        for searched_paper in search_arxiv_as_paper(
            args.arxiv_search_query, max_results=10
        ):
            if searched_paper.title not in existing_titles:
                print(f"    |- {searched_paper.title[:50]}...")
                papers.append(searched_paper)

    if args.search_semantic_scholar:
        to_explore = [p for p in papers if not p.explored]
        if to_explore:
            print(" |- Getting related papers from Semantic Scholar")
            recommended_papers = get_recommended_arxiv_ids_from_semantic_scholar(papers)
            papers.extend(fill_papers_with_arxiv(recommended_papers))
            print(f"    |- {len(recommended_papers)} new papers")
        else:
            print(" |- All papers have been explored")

    if not all([paper.summary for paper in papers]):
        print(" |- Building summaries with OpenAI")
        for paper in [p for p in papers if not p.summary and p.abstract]:
            print(f"    |- {paper.title[:50]}...")
            paper.summary = summarize_abstract_with_openai(
                openai_client, paper.abstract
            )

    if not all([paper.focus for paper in papers]):
        print(" |- Assigning focus labels with OpenAI")
        for paper in [p for p in papers if not p.focus and p.abstract]:
            paper.focus = get_focus_label_from_abstract(openai_client, paper.abstract)
            print(f"    |- {paper.focus}")

    to_write = [p for p in papers if p.has_changed()]
    if to_write:
        print(f" |- Writing {len(to_write)} updates back to Notion")
        write_papers_to_notion(notion_client, args.database_id, to_write)

    print("[+] Done!")


if __name__ == "__main__":
    main()

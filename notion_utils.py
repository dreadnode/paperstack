import asyncio
import typing as t
from datetime import datetime
import time

from notion_client import AsyncClient
from notion_client.errors import RequestTimeoutError, APIResponseError
from notion_client.helpers import async_collect_paginated_api
from tqdm import tqdm  # type: ignore

from _types import AttackType, Paper, Focus

# Retry constants
MAX_RETRIES = 5
RETRY_DELAY = 5
MAX_BATCH_SIZE = 5

NotionClient = AsyncClient


def get_notion_client(token: str) -> NotionClient:
    return NotionClient(auth=token, timeout_ms=60000)  # 60-second timeout


async def get_papers_from_notion(client: NotionClient, database_id: str, *, max: int | None = None) -> list[Paper]:
    retries = 0
    results = []

    while retries < MAX_RETRIES:
        try:
            if max:
                response = await client.databases.query(database_id=database_id, page_size=max)
                results = response['results']
            else:
                results = await async_collect_paginated_api(
                    client.databases.query, database_id=database_id
                )
            break
        except (RequestTimeoutError, APIResponseError) as e:
            retries += 1
            if retries >= MAX_RETRIES:
                print(f"Failed to get papers from Notion after {MAX_RETRIES} attempts: {str(e)}")
                return []
            else:
                print(f"Notion API error when fetching papers, retrying ({retries}/{MAX_RETRIES}): {str(e)}")
                # Exponential backoff with jitter
                wait_time = RETRY_DELAY * (2 ** (retries - 1)) + (RETRY_DELAY * 0.1 * retries)
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                await asyncio.sleep(wait_time)

    papers: list[Paper] = []
    for result in results:
        page_id = result["id"]
        properties = result["properties"]

        title = properties["Title"]["title"]
        title = title[0]["text"]["content"] if title else None
        url = properties["URL"]["url"]
        summary = properties["Summary"]["rich_text"]
        summary = summary[0]["text"]["content"] if summary else None
        authors = [author["name"] for author in properties["Authors"]["multi_select"]]
        published = properties["Published"]["date"]
        published = datetime.fromisoformat(published["start"]) if published else None
        focus = properties["Focus"]["select"]
        focus = Focus(focus["name"]) if focus else None
        attack_type = properties["Attack Type"]["select"]
        attack_type = AttackType(attack_type["name"]) if attack_type else None
        explored = properties["Explored"]["checkbox"]

        if not any([url, title]):
            continue

        papers.append(
            Paper(
                page_id=page_id,
                title=title,
                url=url,
                focus=focus,
                attack_type=attack_type,
                summary=summary,
                authors=authors,
                published=published,
                explored=explored,
                track_changes=True,
            )
        )

    return papers


async def write_papers_to_notion(
    client: NotionClient, database_id: str, papers: list[Paper]
) -> None:
    # Process papers in smaller batches with pauses between
    for i in range(0, len(papers), MAX_BATCH_SIZE):
        batch = papers[i:i+MAX_BATCH_SIZE]
        print(f"Processing batch {i//MAX_BATCH_SIZE + 1}/{(len(papers) + MAX_BATCH_SIZE - 1)//MAX_BATCH_SIZE}")

        for paper in tqdm(batch):
            properties: dict[str, t.Any] = {}
            if paper.title:
                properties["Title"] = {"title": [{"text": {"content": paper.title}}]}
            if paper.url:
                properties["URL"] = {"url": paper.url}
            if paper.summary:
                properties["Summary"] = {
                    "rich_text": [{"text": {"content": paper.summary}}]
                }
            if paper.authors:
                properties["Authors"] = {
                    "multi_select": [{"name": author} for author in paper.authors]
                }
            if paper.published:
                properties["Published"] = {"date": {"start": paper.published.isoformat()}}
            if paper.focus:
                properties["Focus"] = {"select": {"name": paper.focus.value}}
            if paper.attack_type:
                properties["Attack Type"] = {"select": {"name": paper.attack_type.value}}
            if paper.explored is not None:
                properties["Explored"] = {"checkbox": paper.explored}

            # Retry logic with progressive backoff
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    if paper.page_id:
                        await client.pages.update(paper.page_id, properties=properties)
                    else:
                        await client.pages.create(
                            parent={"database_id": database_id}, properties=properties
                        )
                    # Success, break out of retry loop
                    break
                except (RequestTimeoutError, APIResponseError) as e:
                    retries += 1
                    if retries >= MAX_RETRIES:
                        print(f"Failed to update/create paper after {MAX_RETRIES} attempts: {paper.title[:50]}...")
                        # Don't raise - continue with other papers
                        break
                    else:
                        print(f"Notion API error, retrying ({retries}/{MAX_RETRIES}): {str(e)}")
                        # Exponential backoff with longer delays
                        wait_time = RETRY_DELAY * (2 ** (retries - 1)) + (RETRY_DELAY * 0.1 * retries)
                        print(f"Waiting {wait_time:.1f} seconds before retry...")
                        await asyncio.sleep(wait_time)

            # Add a small delay between papers regardless of success/failure
            await asyncio.sleep(1)

        if i + MAX_BATCH_SIZE < len(papers):
            print(f"Pausing for 10 seconds between batches...")
            await asyncio.sleep(10)

    return None

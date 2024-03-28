# paperstack

Paperstack uses ArXiv and Semantic Scholar (relational) to sync academic paper information into a Notion DB. It also has some lightweight uses of OpenAI models for summarization and categorization. It was built for gathering machine learning and security related papers, but could be adapted easily to any other subject (`ARXIV_SEARCH`/`--arxiv-search-query`). It's deplyoment is focused on Github actions, but can be executed on the command line directly. It can also detect partial entries (ArXiv link or title) in the Notion DB and fill in the remaining information.

The Notion DB requires a semi-fixed structure as a function of the syncing logic (`notion_utils.py`), and you're free to add columns and custom syncing behavior as needed. Here is the mininmum database layout the tool currently expects:

```
Title [Title]
Summary [Text]
Focus [Select]
URL [URL]
Authors [Mutli-select]
Published [Date]
Explored [Checkbox]
```

The majority of command line arguments can be passed via environment variables as expected by the workflows.

```
NOTION_TOKEN
NOTION_DATABASE_ID
OPENAI_API_TOKEN
```

Hack away!

# Business case: MCP Server App

**A working pattern for giving an AI assistant safe, reusable access to company tools.**

## Who buys this

The buyer is a platform or internal-tools engineering lead whose company is adding AI assistants to several products or teams. The same integrations (search, a code host, a content system, internal APIs) keep getting rebuilt for each assistant. The users are the developers who build those assistants.

## The problem and what it costs

Every assistant that needs company data ends up with its own connectors. When Anthropic released the Model Context Protocol (MCP) in November 2024, it described the problem plainly: "Every new data source requires its own custom implementation, making truly connected systems difficult to scale." MCP replaces those one-off integrations with one open protocol: tools are exposed once by a server, and any MCP client can use them ([Anthropic, Nov 2024](https://www.anthropic.com/news/model-context-protocol)).

The cost is engineering time spent building and maintaining the same connector more than once. There is also risk: each one-off connector is another place where credentials and permissions are handled differently.

I couldn't find a sourced industry figure for the cost of duplicate AI integrations, so this case uses a worked model instead.

## How the repo solves it

| Need | What in the repo does it |
|---|---|
| Tools exposed once, used by any client | An MCP server in `server/` with dice, web search, social-post drafting, slide and quote images, and GitHub (`search_repositories`, `get_repository_info`, `get_file_content`, `list_repository_files`) |
| An agent that chooses tools | A LangGraph ReAct agent that talks to the server through `langchain-mcp-adapters` over stdio |
| A way for non-developers to try it | A FastAPI backend (`POST /api/chat`) and a Next.js chat UI that shows a trace of each tool call |
| Use from an IDE | Instructions for connecting the same server to Cursor |
| Confidence that tools behave | A pytest suite and `scripts/verify_docker.sh` |
| A template for the next tool | A documented "Add a tool" path in the README |

## Use-case scenarios

All of these organisations are fictional.

1. **A SaaS company's developer-experience team.** The team publishes an MCP server with read-only tools for the internal docs and the issue tracker. The support assistant, the IDE assistant and an on-call bot all use that one server instead of three separate integrations.
2. **A marketing agency.** The social-post and quote-card tools become a shared server that account managers reach from a chat UI. The tool trace shows which inputs produced each draft.
3. **An engineering org's code-review helper.** It starts from the GitHub tool here, which can search repos and read files, and adds a tool for the internal style guide.

## ROI: a worked model (illustrative)

These figures are **illustrative assumptions**.

| Input | Value | Basis |
|---|---|---|
| Assistants that need the same integration | 3 | Assumption |
| Developer days to build one bespoke connector | 5 | Assumption |
| Developer days a year to maintain each copy | 3 | Assumption |
| Developer daily cost | US$665 | BLS May 2024 median for software developers is $133,080 a year, about $64 an hour ([BLS OEWS](https://www.bls.gov/news.release/archives/ocwage_04022025.pdf)). Multiplied by 8 hours and an assumed 1.3 for overhead. |

Three bespoke copies: 15 build days plus 9 maintenance days a year. One shared MCP server: 5 build days plus 3 maintenance days. **Saving: 16 developer days, about US$10,600, per integration per year.** It grows with each new assistant or tool. The case is strongest in organisations with many assistants. With only one assistant it is weak.

## Path to production

1. Replace stdio transport with a remote transport behind authentication, so one server can serve many clients.
2. Add per-user authorisation. Tools should act with the caller's permissions, not a shared token.
3. Log every tool call with its inputs, caller and result, and rate-limit external API calls.
4. Remove the demo tools (dice) and add the organisation's real ones, each with tests.

`PRODUCTIONIZING.md` lists the engineering steps.

## Risks and limits

- The repo is a pattern, not a product. The tools are demos, and the value comes from replacing them with real ones.
- Tool-using agents can be steered by prompt injection in the content they read. Read-only tools and human confirmation for writes are a sensible default.
- MCP is still young and the spec is changing, so plan for upgrades.

## Sources

- Anthropic, "Introducing the Model Context Protocol" (Nov 25, 2024): https://www.anthropic.com/news/model-context-protocol
- U.S. Bureau of Labor Statistics, OEWS May 2024 (software developers): https://www.bls.gov/news.release/archives/ocwage_04022025.pdf

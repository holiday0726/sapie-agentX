"""
Component metadata for NL-to-Flow system.

This file defines metadata for all Langflow components to improve
LLM's understanding of component roles, use cases, and priorities.

Based on actual Langflow category structure from:
- Frontend: src/frontend/src/utils/styleUtils.ts (SIDEBAR_CATEGORIES)
- Backend: Component data from /api/v1/all endpoint

Metadata Structure:
- category: Component classification matching SIDEBAR_CATEGORIES
- role: What this component does (functional description)
- use_case: When to use this component (situational guidance)
- priority: Selection priority (1-10, higher = prefer more)
- keywords: Additional search keywords for better matching
- alternative_names: Common alternative names for the component
"""

from typing import TypedDict


class ComponentMetadata(TypedDict):
    """Type definition for component metadata."""

    category: str  # Category name matching SIDEBAR_CATEGORIES
    role: str  # What the component does
    use_case: str  # When to use it
    priority: int  # Selection priority (1-10)
    keywords: list[str]  # Additional search keywords
    alternative_names: list[str]  # Alternative component names


# ============================================================================
# CATEGORY DEFINITIONS (matching frontend SIDEBAR_CATEGORIES)
# ============================================================================
# Source: src/frontend/src/utils/styleUtils.ts

CATEGORIES = {
    "saved_components": "User's saved components",
    "input_output": "User interaction and data I/O (Chat Input, Chat Output, Text Input, Text Output)",
    "agents": "Autonomous agents with tool use (Agent, MCP Tools)",
    "models": "Language models and embedding models",
    "data": "Data sources and APIs (API Request, Directory, Mock Data, Read File, SQL Database, URL, Web Search, Webhook, Write File)",
    "knowledge_bases": "Knowledge base management (optional)",
    "vectorstores": "Vector databases and embeddings",
    "processing": "Data transformation (Prompt Template, Batch, etc.)",
    "logic": "Logical operations and flow control",
    "helpers": "Helper utilities and tools",
    "inputs": "Input components",
    "outputs": "Output components",
    "prompts": "Prompt engineering components",
    "chains": "LangChain chains",
    "documentloaders": "Document loaders",
    "link_extractors": "Link extraction tools",
    "output_parsers": "Output parsing utilities",
    "prototypes": "Experimental components",
    "retrievers": "Retrieval components",
    "textsplitters": "Text splitting utilities",
    "toolkits": "Agent toolkits",
    "tools": "Agent tools",
}


# ============================================================================
# COMPONENT METADATA REGISTRY
# ============================================================================
# Add your component metadata here following the structure below

COMPONENT_METADATA: dict[str, ComponentMetadata] = {
    # ========================================================================
    # INPUT/OUTPUT COMPONENTS (category: "input_output")
    # ========================================================================
    "ChatInput": {
        "category": "input_output",
        "role": "User input collection for chat conversations",
        "use_case": "Always use for chatbots and conversational interfaces - this is the entry point for user messages",
        "priority": 10,
        "keywords": ["user input", "chat interface", "conversation start", "message input", "chatbot input"],
        "alternative_names": ["Chat Input", "UserInput", "ConversationInput"],
    },
    "ChatOutput": {
        "category": "input_output",
        "role": "Display chat responses to users",
        "use_case": "Always use to display chat responses - this is the exit point showing AI responses to users",
        "priority": 10,
        "keywords": ["chat response", "output display", "conversation end", "message output", "chatbot output"],
        "alternative_names": ["Chat Output", "ResponseOutput", "ConversationOutput"],
    },
    "TextInput": {
        "category": "input_output",
        "role": "Generic text input component",
        "use_case": "Use for non-chat text inputs or when you need a simple text entry point",
        "priority": 7,
        "keywords": ["text input", "string input", "data input"],
        "alternative_names": ["Text Input", "StringInput"],
    },
    "TextOutput": {
        "category": "input_output",
        "role": "Generic text output component",
        "use_case": "Use for non-chat text outputs or when you need a simple text display",
        "priority": 7,
        "keywords": ["text output", "string output", "data output"],
        "alternative_names": ["Text Output", "StringOutput"],
    },
    # ========================================================================
    # AGENTS (category: "agents")
    # ========================================================================
    "Agent": {
        "category": "agents",
        "role": "Autonomous agent for complex task execution with tool use and function calling",
        "use_case": "Use when you need tool use, function calling, multi-step reasoning, or autonomous problem solving. The agent can decide which tools to use and when. IMPORTANT: Agent itself is NOT in tool_mode (set tool_mode: false)",
        "priority": 8,
        "keywords": [
            "agent",
            "autonomous",
            "tool use",
            "function calling",
            "multi-step",
            "reasoning",
            "agentic",
            "agent-based",
            "intelligent agent",
        ],
        "alternative_names": ["AI Agent", "Autonomous Agent", "Tool Agent", "ReAct Agent", "LLM Agent"],
    },
    "ToolCallingAgent": {
        "category": "agents",
        "role": "Tool-enabled agent with explicit function calling capabilities",
        "use_case": "Use when you need explicit tool/function calling with structured outputs",
        "priority": 8,
        "keywords": ["tool calling", "function calling", "agent", "tools", "function agent"],
        "alternative_names": ["Tool Calling Agent", "Function Agent", "Function Calling Agent"],
    },
    "MCPTools": {
        "category": "agents",
        "role": "MCP (Model Context Protocol) tools integration for agents",
        "use_case": "Use when integrating MCP tools with agents for extended capabilities",
        "priority": 6,
        "keywords": ["mcp", "mcp tools", "model context protocol", "agent tools"],
        "alternative_names": ["MCP Tools", "MCP Integration"],
    },
    # ========================================================================
    # MODELS (category: "models")
    # ========================================================================
    "ChatOpenAI": {
        "category": "models",
        "role": "Conversational AI model for chat interactions using OpenAI GPT models",
        "use_case": "Use for chat conversations, Q&A, and dialogue systems requiring GPT-3.5/GPT-4. Preferred for most chatbot use cases.",
        "priority": 9,
        "keywords": ["openai", "gpt", "chat model", "llm", "language model", "gpt-4", "gpt-3.5", "gpt-4o"],
        "alternative_names": ["OpenAI Chat", "GPT", "ChatGPT", "OpenAI", "GPT-4", "GPT-3.5"],
    },
    "ChatAnthropic": {
        "category": "models",
        "role": "Conversational AI model using Anthropic Claude",
        "use_case": "Use for chat conversations requiring Claude models (longer context, better reasoning, function calling)",
        "priority": 9,
        "keywords": ["anthropic", "claude", "chat model", "llm", "language model", "claude-3", "sonnet", "opus"],
        "alternative_names": ["Anthropic", "Claude", "Claude Chat", "Claude-3"],
    },
    "LanguageModel": {
        "category": "models",
        "role": "Generic language model component",
        "use_case": "Use for general-purpose language model tasks when you don't need a specific provider",
        "priority": 7,
        "keywords": ["llm", "language model", "ai model", "text generation"],
        "alternative_names": ["LLM", "Language Model", "Text Model"],
    },
    "EmbeddingModel": {
        "category": "models",
        "role": "Generate embeddings for text",
        "use_case": "Use for RAG systems to create vector embeddings from text for semantic search",
        "priority": 7,
        "keywords": ["embeddings", "vector embeddings", "text embeddings", "semantic embeddings"],
        "alternative_names": ["Embedding Model", "Embeddings", "Text Embeddings"],
    },
    # ========================================================================
    # DATA COMPONENTS (category: "data")
    # ========================================================================
    "APIRequest": {
        "category": "data",
        "role": "Make HTTP API requests to external services",
        "use_case": "Use when you need to fetch data from REST APIs or web services",
        "priority": 6,
        "keywords": ["api", "http", "rest", "api call", "web request", "fetch"],
        "alternative_names": ["API Request", "HTTP Request", "REST API"],
    },
    "Directory": {
        "category": "data",
        "role": "Load files from a directory",
        "use_case": "Use when loading multiple files from a folder for batch processing",
        "priority": 6,
        "keywords": ["directory", "folder", "batch load", "multiple files"],
        "alternative_names": ["Directory Loader", "Folder Loader"],
    },
    "MockData": {
        "category": "data",
        "role": "Generate mock/test data",
        "use_case": "Use for testing and prototyping without real data sources",
        "priority": 4,
        "keywords": ["mock", "test data", "fake data", "sample data"],
        "alternative_names": ["Mock Data", "Test Data", "Sample Data"],
    },
    "ReadFile": {
        "category": "data",
        "role": "Read content from a file",
        "use_case": "Use when loading PDFs, text files, or documents for RAG or processing",
        "priority": 7,
        "keywords": ["file", "read file", "document", "pdf", "text file", "load file"],
        "alternative_names": ["Read File", "File Loader", "Document Loader", "File"],
    },
    "SQLDatabase": {
        "category": "data",
        "role": "Connect to and query SQL databases",
        "use_case": "Use when you need to fetch data from databases (PostgreSQL, MySQL, SQLite, etc.)",
        "priority": 6,
        "keywords": ["sql", "database", "postgres", "mysql", "sqlite", "query"],
        "alternative_names": ["SQL Database", "Database", "SQL"],
    },
    "URL": {
        "category": "data",
        "role": "Load and crawl content from web URLs",
        "use_case": "Use when you need URL crawling, web page loading, or scraping online content for RAG or processing",
        "priority": 7,
        "keywords": [
            "url",
            "url crawling",
            "url crawler",
            "web crawling",
            "web crawler",
            "crawl",
            "scrape",
            "web page",
            "website",
            "web content",
            "web loader",
            "page scraper",
        ],
        "alternative_names": ["URL", "URL Loader", "Web Loader", "URL Crawler", "Web Scraper", "Web Crawler"],
    },
    "WebSearch": {
        "category": "data",
        "role": "Search the web for information",
        "use_case": "Use with agents when web search capability is needed. IMPORTANT: Set tool_mode: true when using with agents",
        "priority": 6,
        "keywords": ["web search", "search", "google", "internet search", "search api", "serp"],
        "alternative_names": ["Web Search", "Search API", "Google Search", "Internet Search"],
    },
    "Webhook": {
        "category": "data",
        "role": "Receive data via webhooks",
        "use_case": "Use when you need to receive real-time data from external services via HTTP callbacks",
        "priority": 5,
        "keywords": ["webhook", "http callback", "real-time data"],
        "alternative_names": ["Webhook", "HTTP Callback"],
    },
    "WriteFile": {
        "category": "data",
        "role": "Write content to a file",
        "use_case": "Use when you need to save results, logs, or data to files",
        "priority": 5,
        "keywords": ["write file", "save file", "export", "file output"],
        "alternative_names": ["Write File", "File Writer", "Save File"],
    },
    # ========================================================================
    # VECTOR STORES (category: "vectorstores")
    # ========================================================================
    "AstraDB": {
        "category": "vectorstores",
        "role": "Store and retrieve vector embeddings using DataStax Astra DB",
        "use_case": "Use for production RAG systems requiring scalable cloud vector storage",
        "priority": 7,
        "keywords": ["vector store", "vector database", "embeddings", "astra", "datastax", "rag"],
        "alternative_names": ["Astra DB", "DataStax", "Astra Vector Store"],
    },
    "Pinecone": {
        "category": "vectorstores",
        "role": "Store and retrieve vector embeddings using Pinecone",
        "use_case": "Use for production RAG systems with high-performance vector search",
        "priority": 7,
        "keywords": ["vector store", "vector database", "embeddings", "pinecone", "rag"],
        "alternative_names": ["Pinecone DB", "Pinecone Vector Store"],
    },
    "InMemoryVectorStore": {
        "category": "vectorstores",
        "role": "Temporary in-memory vector storage",
        "use_case": "Use for testing, prototyping, or small-scale RAG systems (data lost on restart)",
        "priority": 6,
        "keywords": ["vector store", "in-memory", "temporary", "testing", "rag"],
        "alternative_names": ["In-Memory Store", "Memory Vector Store", "Temp Vector Store"],
    },
    # ========================================================================
    # PROCESSING (category: "processing")
    # ========================================================================
    "PromptTemplate": {
        "category": "processing",
        "role": "Create structured prompts with variables",
        "use_case": "Use when you need dynamic prompt templates with variable substitution",
        "priority": 6,
        "keywords": ["prompt", "template", "prompt engineering", "dynamic prompt"],
        "alternative_names": ["Prompt", "Template", "Prompt Builder"],
    },
    "Batch": {
        "category": "processing",
        "role": "Process data in batches",
        "use_case": "Use when you need to process multiple items efficiently in batches",
        "priority": 5,
        "keywords": ["batch", "batch processing", "bulk processing"],
        "alternative_names": ["Batch Processing", "Bulk Processing"],
    },
    "BatchRun": {
        "category": "processing",
        "role": "Execute batch operations on data",
        "use_case": "Use for running batch operations on multiple data items sequentially or in parallel",
        "priority": 5,
        "keywords": ["batch run", "batch execution", "batch operation", "bulk operation"],
        "alternative_names": ["Batch Run", "Batch Executor"],
    },
    "DataOperations": {
        "category": "processing",
        "role": "Perform operations on data structures",
        "use_case": "Use for data manipulation, filtering, mapping, and transformation operations",
        "priority": 6,
        "keywords": ["data operations", "data manipulation", "data transform", "filter", "map"],
        "alternative_names": ["Data Operations", "Data Transform"],
    },
    "DataframeOperations": {
        "category": "processing",
        "role": "Perform operations on pandas DataFrames",
        "use_case": "Use for DataFrame-specific operations like filtering rows, selecting columns, aggregations",
        "priority": 6,
        "keywords": ["dataframe", "pandas", "dataframe operations", "data analysis", "tabular data"],
        "alternative_names": ["Dataframe Operations", "DataFrame", "Pandas Operations"],
    },
    "DynamicCreateData": {
        "category": "processing",
        "role": "Dynamically create data structures at runtime",
        "use_case": "Use when you need to generate data structures dynamically based on runtime conditions",
        "priority": 5,
        "keywords": ["dynamic data", "runtime data", "data generation", "dynamic creation"],
        "alternative_names": ["Dynamic Create Data", "Dynamic Data Generator"],
    },
    "LLMRouter": {
        "category": "processing",
        "role": "Route requests to different LLMs based on conditions",
        "use_case": "Use for intelligent routing between multiple LLMs based on query type, cost, or performance",
        "priority": 6,
        "keywords": ["llm router", "model routing", "dynamic routing", "model selection"],
        "alternative_names": ["LLM Router", "Model Router", "AI Router"],
    },
    "Parser": {
        "category": "processing",
        "role": "Parse and extract structured data from text",
        "use_case": "Use for parsing text into structured formats (JSON, XML, CSV) or extracting specific data patterns",
        "priority": 6,
        "keywords": ["parser", "parsing", "data extraction", "text parsing", "structured output"],
        "alternative_names": ["Parser", "Data Parser", "Text Parser"],
    },
    "PythonInterpreter": {
        "category": "processing",
        "role": "Execute Python code dynamically",
        "use_case": "Use when you need to run custom Python logic or transformations at runtime",
        "priority": 7,
        "keywords": ["python", "code execution", "python interpreter", "dynamic code", "scripting"],
        "alternative_names": ["Python Interpreter", "Python Executor", "Python Code Runner"],
    },
    "SmartTransform": {
        "category": "processing",
        "role": "Intelligent data transformation with LLM assistance",
        "use_case": "Use for complex transformations that benefit from LLM understanding (e.g., reformatting, summarizing)",
        "priority": 6,
        "keywords": ["smart transform", "ai transform", "intelligent transform", "llm transform"],
        "alternative_names": ["Smart Transform", "AI Transform", "Intelligent Transform"],
    },
    "SplitText": {
        "category": "processing",
        "role": "Split text into smaller chunks or segments",
        "use_case": "Use for basic text splitting without the complexity of text splitters",
        "priority": 5,
        "keywords": ["split text", "text splitting", "chunking", "segment"],
        "alternative_names": ["Split Text", "Text Splitter"],
    },
    "StructuredOutput": {
        "category": "processing",
        "role": "Format outputs into structured formats",
        "use_case": "Use when you need to enforce structured output formats (JSON, schema-based) from LLMs",
        "priority": 7,
        "keywords": ["structured output", "json output", "schema", "format", "output parsing"],
        "alternative_names": ["Structured Output", "JSON Output", "Schema Output"],
    },
    "TypeConvert": {
        "category": "processing",
        "role": "Convert data between different types",
        "use_case": "Use for type conversion operations (string to int, list to dict, etc.)",
        "priority": 5,
        "keywords": ["type conversion", "data type", "convert", "casting"],
        "alternative_names": ["Type Convert", "Type Conversion", "Data Type Convert"],
    },
    # ========================================================================
    # LOGIC (category: "logic")
    # ========================================================================
    "IfElse": {
        "category": "logic",
        "role": "Conditional branching logic",
        "use_case": "Use for if-then-else conditional flow control based on conditions",
        "priority": 7,
        "keywords": ["if else", "conditional", "branching", "condition", "decision"],
        "alternative_names": ["If-Else", "Conditional", "Branch"],
    },
    "Listen": {
        "category": "logic",
        "role": "Listen for events or triggers",
        "use_case": "Use when you need to wait for and respond to specific events or conditions",
        "priority": 5,
        "keywords": ["listen", "event listener", "trigger", "wait for"],
        "alternative_names": ["Listen", "Event Listener", "Trigger Listener"],
    },
    "Loop": {
        "category": "logic",
        "role": "Iterate over data or repeat operations",
        "use_case": "Use for repeating operations multiple times or iterating over collections",
        "priority": 6,
        "keywords": ["loop", "iteration", "repeat", "for loop", "while loop"],
        "alternative_names": ["Loop", "Iteration", "Repeat"],
    },
    "Notify": {
        "category": "logic",
        "role": "Send notifications or alerts",
        "use_case": "Use for sending notifications when specific conditions are met",
        "priority": 5,
        "keywords": ["notify", "notification", "alert", "message"],
        "alternative_names": ["Notify", "Notification", "Alert"],
    },
    "RunFlow": {
        "category": "logic",
        "role": "Execute another flow as a sub-flow",
        "use_case": "Use for composing complex workflows by calling other flows",
        "priority": 6,
        "keywords": ["run flow", "sub-flow", "nested flow", "flow execution"],
        "alternative_names": ["Run Flow", "Sub-Flow", "Execute Flow"],
    },
    "SmartRouter": {
        "category": "logic",
        "role": "Intelligent routing based on content or conditions",
        "use_case": "Use for dynamic routing decisions based on LLM analysis or complex conditions",
        "priority": 7,
        "keywords": ["smart router", "intelligent routing", "ai routing", "dynamic routing"],
        "alternative_names": ["Smart Router", "AI Router", "Intelligent Router"],
    },
    # ========================================================================
    # HELPERS (category: "helpers")
    # ========================================================================
    "CurrentDate": {
        "category": "helpers",
        "role": "Get the current date and time",
        "use_case": "Use when you need to access current date/time information",
        "priority": 5,
        "keywords": ["current date", "date", "time", "timestamp", "now"],
        "alternative_names": ["Current Date", "Date Time", "Now"],
    },
    "MessageHistory": {
        "category": "helpers",
        "role": "Store and retrieve conversation history",
        "use_case": "Use for maintaining context in multi-turn conversations and chatbots",
        "priority": 8,
        "keywords": ["message history", "conversation history", "chat history", "memory", "context"],
        "alternative_names": ["Message History", "Chat Memory", "Conversation Memory"],
    },
    # ========================================================================
    # TEXT SPLITTERS (category: "textsplitters")
    # ========================================================================
    "RecursiveCharacterTextSplitter": {
        "category": "textsplitters",
        "role": "Split text into chunks using recursive algorithm",
        "use_case": "Use after loading documents, before vector storage. Best for most use cases (intelligently splits on paragraphs, sentences, then characters)",
        "priority": 7,
        "keywords": ["text splitter", "chunking", "split documents", "text processing", "rag"],
        "alternative_names": ["Text Splitter", "Document Splitter", "Recursive Splitter"],
    },
    "CharacterTextSplitter": {
        "category": "textsplitters",
        "role": "Split text into chunks by character count",
        "use_case": "Use when you need simple character-based text splitting",
        "priority": 5,
        "keywords": ["text splitter", "chunking", "character split"],
        "alternative_names": ["Character Splitter", "Simple Splitter"],
    },
    # ========================================================================
    # TOOLS (category: "tools")
    # ========================================================================
    "SearchAPI": {
        "category": "tools",
        "role": "Web search tool for agents",
        "use_case": "Use with agents when web search is needed. IMPORTANT: Set tool_mode: true in config",
        "priority": 6,
        "keywords": ["web search", "search", "google", "internet search", "search api", "agent tool"],
        "alternative_names": ["Search API", "Web Search", "Google Search"],
    },
    "SerpAPI": {
        "category": "tools",
        "role": "Google Search results tool via SerpAPI",
        "use_case": "Use with agents for Google search results. IMPORTANT: Set tool_mode: true in config",
        "priority": 6,
        "keywords": ["serp", "google search", "search results", "web search", "agent tool"],
        "alternative_names": ["SERP API", "Google Search API"],
    },
    "Calculator": {
        "category": "tools",
        "role": "Mathematical calculation tool for agents",
        "use_case": "Use with agents when mathematical calculations are needed. IMPORTANT: Set tool_mode: true",
        "priority": 5,
        "keywords": ["calculator", "math", "calculation", "arithmetic", "agent tool"],
        "alternative_names": ["Math Tool", "Calculation Tool"],
    },
    # ========================================================================
    # DEPRECATED / LOW PRIORITY
    # ========================================================================
    "BaiduQianfanChatModel": {
        "category": "models",
        "role": "Generate text using Baidu Qianfan LLMs (DEPRECATED - prefer OpenAI/Anthropic)",
        "use_case": "Avoid unless specifically required - use ChatOpenAI or ChatAnthropic instead",
        "priority": 2,
        "keywords": ["baidu", "qianfan", "chinese llm"],
        "alternative_names": ["Qianfan", "Baidu"],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_component_metadata(component_name: str) -> ComponentMetadata | None:
    """
    Get metadata for a component by name.

    Args:
        component_name: Name of the component (case-insensitive)

    Returns:
        Component metadata dict or None if not found
    """
    # Try exact match first
    if component_name in COMPONENT_METADATA:
        return COMPONENT_METADATA[component_name]

    # Try case-insensitive match
    component_name_lower = component_name.lower()
    for name, metadata in COMPONENT_METADATA.items():
        if name.lower() == component_name_lower:
            return metadata

    # Try alternative names
    for name, metadata in COMPONENT_METADATA.items():
        if component_name_lower in [alt.lower() for alt in metadata["alternative_names"]]:
            return metadata

    return None


def get_components_by_category(category: str) -> dict[str, ComponentMetadata]:
    """
    Get all components in a specific category.

    Args:
        category: Category name (e.g., "agents", "data", "models")

    Returns:
        Dictionary of component_name -> metadata for components in that category
    """
    return {name: meta for name, meta in COMPONENT_METADATA.items() if meta["category"] == category}


def get_high_priority_components(min_priority: int = 7) -> dict[str, ComponentMetadata]:
    """
    Get components with priority >= min_priority.

    Args:
        min_priority: Minimum priority threshold (default: 7)

    Returns:
        Dictionary of high-priority components
    """
    return {name: meta for name, meta in COMPONENT_METADATA.items() if meta["priority"] >= min_priority}


def search_components_by_keyword(keyword: str) -> dict[str, ComponentMetadata]:
    """
    Search components by keyword (searches in keywords, role, use_case, and name).

    Args:
        keyword: Search keyword (case-insensitive)

    Returns:
        Dictionary of matching components
    """
    keyword_lower = keyword.lower()
    results = {}

    for name, meta in COMPONENT_METADATA.items():
        # Search in component name
        if keyword_lower in name.lower():
            results[name] = meta
            continue

        # Search in keywords
        if any(keyword_lower in kw.lower() for kw in meta["keywords"]):
            results[name] = meta
            continue

        # Search in role
        if keyword_lower in meta["role"].lower():
            results[name] = meta
            continue

        # Search in use_case
        if keyword_lower in meta["use_case"].lower():
            results[name] = meta
            continue

        # Search in alternative names
        if any(keyword_lower in alt.lower() for alt in meta["alternative_names"]):
            results[name] = meta
            continue

    return results


# ============================================================================
# TEMPLATE FOR ADDING NEW COMPONENTS
# ============================================================================
"""
To add a new component, copy this template and fill in the values:

"ComponentName": {
    "category": "input_output|agents|models|data|vectorstores|processing|textsplitters|tools|...",
    "role": "Brief description of what this component does",
    "use_case": "When and why to use this component (be specific and actionable)",
    "priority": 1-10,  # 10=essential, 8-9=preferred, 6-7=common, 4-5=specialized, 2-3=deprecated
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "alternative_names": ["Alternative Name 1", "Alternative Name 2"],
},

Priority Guidelines:
- 10: Essential components (ChatInput, ChatOutput)
- 9: Preferred models (ChatOpenAI, ChatAnthropic)
- 8: Core functionality (Agent, ToolCallingAgent)
- 7: Common use cases (File loaders, vector stores, text splitters, models)
- 6: Specialized but useful (specific tools, data sources)
- 5: Medium priority (memory, embeddings, utilities)
- 4: Default for unclassified
- 2-3: Deprecated or discouraged

Category Guidelines (matching SIDEBAR_CATEGORIES from frontend):
- input_output: Chat Input/Output, Text Input/Output
- agents: Agent, ToolCallingAgent, MCP Tools
- models: ChatOpenAI, ChatAnthropic, LanguageModel, EmbeddingModel
- data: API Request, Directory, ReadFile, SQLDatabase, URL, WebSearch, Webhook, WriteFile
- vectorstores: AstraDB, Pinecone, InMemoryVectorStore
- processing: PromptTemplate, Batch, data transformation
- textsplitters: RecursiveCharacterTextSplitter, CharacterTextSplitter
- tools: SearchAPI, Calculator, agent tools (set tool_mode: true)
- documentloaders: Document loading utilities
- retrievers: Retrieval components
- helpers: Helper utilities
- logic: Logical operations
- prompts: Prompt engineering
- chains: LangChain chains
- inputs: Generic inputs
- outputs: Generic outputs
"""

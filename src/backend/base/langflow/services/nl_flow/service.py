"""Service for converting natural language to Langflow flows using LLM Function Calling."""

import json
import os
from typing import Any

from loguru import logger

from langflow.services.nl_flow.component_metadata import get_component_metadata


class NLFlowService:
    """Service for generating flows from natural language using LLM."""

    def __init__(self):
        """Initialize NL Flow Service."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set - NL to Flow will not work")

    async def generate_flow(self, prompt: str, available_components: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a flow from natural language description.

        Args:
            prompt: Natural language description of the flow
            available_components: Available Langflow components from /all endpoint

        Returns:
            Dictionary with nodes and edges for the flow
        """
        if not self.openai_api_key:
            msg = "OPENAI_API_KEY environment variable not set"
            raise ValueError(msg)

        try:
            # Import here to avoid dependency issues if openai not installed
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.openai_api_key)

            # Simplify component data for LLM context
            simplified_components = self._simplify_components(available_components)

            # Define functions for LLM to call
            functions = [
                {
                    "name": "search_components",
                    "description": "Search for Langflow components by capability or type",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What the component should do (e.g., 'chat model', 'memory', 'document loader')",
                            }
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "create_flow",
                    "description": "Create the final flow with nodes and connections",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nodes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "component_name": {"type": "string"},
                                        "config": {
                                            "type": "object",
                                            "description": """Configuration for component parameters. Use the parameter information from search_components results.

Examples:
- ChatModel: {"system_message": "You are a helpful assistant", "max_tokens": 1000, "temperature": 0.7}
- Agent: {"tool_mode": false} (Agent itself is NOT in tool mode, but tools connected to it should be)
- Tool components (SearchAPI, Calculator): {"tool_mode": true}
- TextSplitter: {"chunk_size": 1000, "chunk_overlap": 200}
- VectorStore: {"collection_name": "my_documents"}

Format: {"parameter_name": value, "another_param": value}""",
                                            "additionalProperties": True,
                                        },
                                    },
                                    "required": ["id", "component_name"],
                                },
                            },
                            "edges": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "target": {"type": "string"},
                                        "source_output": {
                                            "type": "string",
                                            "description": "Name of output field from source (e.g., 'message', 'text_output'). Optional - will auto-detect if not specified.",
                                        },
                                        "target_input": {
                                            "type": "string",
                                            "description": "Name of input field on target (e.g., 'input_value', 'documents'). Optional - will auto-detect if not specified.",
                                        },
                                    },
                                    "required": ["source", "target"],
                                },
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Brief explanation of what the flow does",
                            },
                        },
                        "required": ["nodes", "edges"],
                    },
                },
            ]

            # System prompt
            system_prompt = """You are a Langflow expert assistant. Help users build flows by:
1. Understanding their requirements
2. Finding appropriate components using search_components
3. Creating a valid flow structure with create_flow and configuring components properly

Guidelines:
- Build flows with as many components as needed (no limit on component count)
- For complex requirements, use 5-10+ components if necessary
- Common patterns:
  * Simple Chatbot: ChatInput → ChatModel → ChatOutput
  * RAG System: File → TextSplitter → VectorStore → ChatModel → ChatOutput
  * Agent with Tools: ChatInput → Agent + [Tool1, Tool2, Tool3 in tool_mode] → ChatOutput
  * Multi-step Processing: Input → Processor1 → Processor2 → Validator → Output
- Ensure component connections are compatible
- ALWAYS configure component parameters in the config field

Component Configuration Rules (CRITICAL):
1. ChatModel Components:
   - ALWAYS set system_message parameter with appropriate instructions for the task
   - Set max_tokens (default: 1000-4000 depending on complexity)
   - Set temperature (0.0 for deterministic, 0.7 for creative tasks)
   - Example: {"system_message": "You are a helpful assistant that answers questions about documents", "max_tokens": 2000, "temperature": 0.7}

2. Agent Components:
   - Agent itself: {"tool_mode": false} (Agent is NOT a tool)
   - When tools are needed:
     a) Add tool components (SearchAPI, Calculator, etc.)
     b) Set tool_mode: true in EACH tool component's config
     c) Connect all tool components to the Agent
   - Example Agent config: {"tool_mode": false}
   - Example Tool config: {"tool_mode": true}

3. TextSplitter Components:
   - Set chunk_size (default: 1000 for general, 500 for precise retrieval)
   - Set chunk_overlap (default: 200, helps maintain context)
   - Example: {"chunk_size": 1000, "chunk_overlap": 200}

4. VectorStore Components:
   - Set collection_name to a descriptive name
   - Example: {"collection_name": "my_documents"}

5. File/Document Components:
   - Usually no special config needed
   - Can set file_types filter if specific formats required

Component Selection Rules:
- LLM/Model Components: Use standard components (OpenAI, Anthropic, ChatOpenAI, etc.)
  * DO NOT use Qianfan models - use generic Language Model components
  * Prefer "ChatOpenAI", "Anthropic" for chat tasks
- Vector Stores: Use "Astra DB" or "Pinecone" for production, "In-Memory Vector Store" for testing
- Text Processing: Use "RecursiveCharacterTextSplitter" or "CharacterTextSplitter"

Connection Rules:
- Specify source_output and target_input when you know the exact field names
- Example: ChatInput.message → ChatModel.input_value
- Example: ChatModel.text_output → ChatOutput.input_value
- If unsure, leave blank and let the system auto-detect

IMPORTANT - Parameter Setting Strategy:
- ALWAYS configure critical parameters (system_message for ChatModel, chunk_size for TextSplitter, tool_mode for tools)
- Use sensible defaults based on the use case
- Prioritize user experience and result quality
- When in doubt, set parameters to commonly used values

IMPORTANT - Fallback Strategy:
- If you cannot find exact component after 2-3 searches, use closest alternative
- For PDF/documents: use 'File' or 'Read File' component
- For web search/URL crawling: These components may not exist - create a simple chatbot instead and explain limitations
- If a component doesn't exist after 3 searches, STOP searching and use what you found
- ALWAYS call create_flow with available components, even if user request cannot be fully satisfied
- Do NOT keep searching beyond 3 attempts - build with what's available
- Better to create a partial flow than no flow at all

CRITICAL - Maximum 3 searches per component type:
- If search returns empty [] more than once, STOP searching for that component
- Use generic alternatives (ChatInput, ChatModel, ChatOutput work for most cases)
- ALWAYS proceed to create_flow after finding basic components
"""

            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

            # Function calling loop
            max_iterations = 5  # Increased to allow more complex flows
            flow_result = None

            for i in range(max_iterations):
                response = await client.chat.completions.create(
                    model="gpt-4-turbo-preview", messages=messages, functions=functions, function_call="auto"
                )

                message = response.choices[0].message

                # If no function call, we're done
                if not message.function_call:
                    logger.warning(f"Iteration {i+1}: No function call from LLM. Message: {message.content}")
                    break

                # Execute function
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                logger.info(f"Iteration {i+1}: Calling function {function_name} with args: {function_args}")

                if function_name == "search_components":
                    result = self._search_components(function_args["query"], simplified_components)
                    # Warn if search returned empty
                    if not result or len(result) == 0:
                        logger.warning(f"Search for '{function_args['query']}' returned no results - component may not exist")
                elif function_name == "create_flow":
                    flow_result = function_args
                    result = {"status": "success", "message": "Flow created"}
                else:
                    result = {"error": f"Unknown function: {function_name}"}

                # Add function result to conversation
                messages.append({"role": "assistant", "content": None, "function_call": message.function_call})

                # Add hint for empty search results
                if function_name == "search_components" and (not result or len(result) == 0):
                    hint_message = json.dumps({
                        "results": [],
                        "hint": "Component not found. Consider using basic components (ChatInput, ChatModel, ChatOutput) or search for alternatives. If you've searched 3+ times, proceed to create_flow with available components."
                    })
                    messages.append({"role": "function", "name": function_name, "content": hint_message})
                else:
                    messages.append({"role": "function", "name": function_name, "content": json.dumps(result)})

                # If flow was created, we're done
                if flow_result:
                    break

            if not flow_result:
                # Log the last message from LLM for debugging
                if messages:
                    last_msg = messages[-1]
                    logger.error(f"No flow created. Last message: {last_msg}")
                msg = "Failed to generate flow - LLM did not call create_flow function. Try a clearer prompt like 'Create a simple chatbot'"
                raise ValueError(msg)

            # Convert to frontend format
            return self._format_flow_response(flow_result, available_components)

        except ImportError as e:
            msg = "openai package not installed. Install with: pip install openai"
            raise ImportError(msg) from e
        except Exception as e:
            logger.error(f"Error in generate_flow: {e}")
            raise

    def _simplify_components(self, components: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Simplify component data for LLM context."""
        simplified = {}

        for category, category_components in components.items():
            simplified[category] = []
            for name, component in category_components.items():
                # Generate keywords based on component capabilities
                keywords = []
                valid_extensions = component.get("VALID_EXTENSIONS", [])

                # Add file type keywords based on supported extensions
                if valid_extensions:
                    ext_lower = [str(ext).lower().replace(".", "") for ext in valid_extensions]

                    # PDF keywords
                    if "pdf" in ext_lower:
                        keywords.extend(["PDF", "PDF loader", "PDF reader", "PDF parser", "document loader"])

                    # Office document keywords
                    if any(ext in ext_lower for ext in ["docx", "doc", "xlsx", "xls", "pptx", "ppt"]):
                        keywords.extend(["document loader", "office document", "word", "excel", "powerpoint"])

                    # Image keywords
                    if any(ext in ext_lower for ext in ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]):
                        keywords.extend(["image loader", "image reader", "picture"])

                    # Text file keywords
                    if any(ext in ext_lower for ext in ["txt", "md", "csv"]):
                        keywords.extend(["text loader", "text reader", "file reader"])

                # Add component type keywords based on name/display_name
                component_name_lower = name.lower()
                display_name_lower = component.get("display_name", "").lower()

                if "split" in component_name_lower or "split" in display_name_lower:
                    keywords.extend(["text splitter", "chunk", "chunking"])

                if "chat" in component_name_lower or "chat" in display_name_lower:
                    keywords.extend(["chat", "conversation", "chatbot"])

                if "vector" in component_name_lower or "vector" in display_name_lower:
                    keywords.extend(["vector store", "embeddings", "vector database"])

                if "model" in component_name_lower or "llm" in component_name_lower:
                    keywords.extend(["language model", "LLM", "AI model"])

                # Get metadata from metadata file first, fallback to inference
                metadata = get_component_metadata(name)

                if metadata:
                    # Use metadata file definitions (more accurate)
                    role = metadata["role"]
                    use_case = metadata["use_case"]
                    priority = metadata["priority"]
                    # Merge keywords from metadata with auto-generated ones
                    keywords.extend(metadata["keywords"])
                    logger.debug(f"Using metadata file for component: {name}")
                else:
                    # Fallback to dynamic inference for components not in metadata
                    role = self._infer_component_role(category, name, component)
                    use_case = self._infer_use_case(category, name, component)
                    priority = self._infer_priority(category, name, component)
                    logger.debug(f"Using inference for component: {name} (not in metadata file)")

                # Extract parameter information from template
                template = component.get("template", {})
                required_params = []
                optional_params = []
                supports_tool_mode = False

                for field_name, field_data in template.items():
                    if isinstance(field_data, dict):
                        # Check for tool mode support
                        if field_name == "tool_mode" or "tool" in field_name.lower():
                            supports_tool_mode = True

                        # Extract parameter info
                        param_info = {
                            "name": field_name,
                            "type": field_data.get("type", "str"),
                            "display_name": field_data.get("display_name", field_name),
                        }

                        # Add description if available
                        if field_data.get("info"):
                            param_info["description"] = field_data.get("info")

                        # Categorize as required or optional
                        if field_data.get("required", False):
                            required_params.append(param_info)
                        elif not field_data.get("advanced", False) and field_data.get("show", True):
                            # Include non-advanced, visible parameters
                            optional_params.append(param_info)

                simplified[category].append(
                    {
                        "name": name,
                        "display_name": component.get("display_name", name),
                        "description": component.get("description", ""),
                        "keywords": list(set(keywords)),  # Remove duplicates
                        "input_types": component.get("input_types", []),
                        "output_types": component.get("output_types", []),
                        "required_params": required_params,
                        "optional_params": optional_params[:3],  # Limit to top 3 to save tokens
                        "supports_tool_mode": supports_tool_mode,
                        "role": role,  # What this component does
                        "use_case": use_case,  # When to use it
                        "priority": priority,  # Selection priority (1-10)
                    }
                )

        return simplified

    def _infer_component_role(self, category: str, name: str, component: dict[str, Any]) -> str:
        """Infer the role of a component based on its category and name."""
        name_lower = name.lower()
        category_lower = category.lower()

        # Input components
        if "input" in category_lower or "input" in name_lower:
            if "chat" in name_lower:
                return "User input collection for chat conversations"
            if "file" in name_lower or "document" in name_lower:
                return "File/document input and loading"
            return "Data input and collection"

        # Output components
        if "output" in category_lower or "output" in name_lower:
            if "chat" in name_lower:
                return "Display chat responses to users"
            if "text" in name_lower:
                return "Display text output"
            return "Data output and display"

        # Model/LLM components
        if "model" in category_lower or "llm" in category_lower:
            if "chat" in name_lower:
                return "Conversational AI model for chat interactions"
            if "embedding" in name_lower:
                return "Generate embeddings for text"
            return "Language model for text generation and understanding"

        # Agent components
        if "agent" in category_lower or "agent" in name_lower:
            if "tool" in name_lower:
                return "Tool-enabled agent with function calling"
            return "Autonomous agent for complex task execution"

        # Processing components
        if "process" in category_lower or "split" in name_lower:
            if "text" in name_lower or "character" in name_lower:
                return "Split text into chunks for processing"
            return "Data processing and transformation"

        # Vector/Embedding components
        if "vector" in category_lower or "vector" in name_lower or "embedding" in name_lower:
            if "store" in name_lower or "database" in name_lower:
                return "Store and retrieve vector embeddings"
            if "search" in name_lower:
                return "Search vectors for similarity"
            return "Vector operations and storage"

        # Memory components
        if "memory" in category_lower or "memory" in name_lower:
            return "Store conversation history and context"

        # Tool components
        if "tool" in category_lower or "tool" in name_lower:
            if "search" in name_lower or "api" in name_lower:
                return "External tool for agents (set tool_mode: true)"
            return "Utility tool for specific tasks"

        # Default
        return component.get("description", "Component for data processing")[:80]

    def _infer_use_case(self, category: str, name: str, component: dict[str, Any]) -> str:
        """Infer when to use this component."""
        name_lower = name.lower()
        category_lower = category.lower()

        # Chatbot use cases
        if "chatinput" in name_lower:
            return "Always use for chatbots and conversational interfaces"
        if "chatoutput" in name_lower:
            return "Always use to display chat responses"
        if "chat" in name_lower and ("openai" in name_lower or "anthropic" in name_lower or "model" in category_lower):
            return "Use for chat conversations, Q&A, and dialogue systems"

        # RAG use cases
        if "file" in name_lower or "document" in name_lower:
            return "Use when loading PDFs, documents, or files"
        if "split" in name_lower and "text" in name_lower:
            return "Use after loading documents, before vector storage"
        if "vector" in name_lower and "store" in name_lower:
            return "Use for RAG systems, semantic search, and document Q&A"

        # Agent use cases
        if "agent" in name_lower:
            return "Use when you need tool use, function calling, or multi-step reasoning"
        if "tool" in name_lower and "search" in name_lower:
            return "Use with agents when web search is needed (set tool_mode: true)"
        if "tool" in category_lower or component.get("supports_tool_mode"):
            return "Use with agents as tools (set tool_mode: true)"

        # Memory use cases
        if "memory" in name_lower:
            return "Use when chat needs to remember previous conversation"

        return "General-purpose component"

    def _infer_priority(self, category: str, name: str, component: dict[str, Any]) -> int:
        """Infer selection priority (1-10, higher = prefer)."""
        name_lower = name.lower()
        category_lower = category.lower()

        # High priority (8-10): Essential, commonly used
        if name_lower in ["chatinput", "chatoutput"]:
            return 10  # Always needed for chatbots
        if "chatopenai" in name_lower or "chatanthropic" in name_lower:
            return 9  # Preferred chat models
        if "agent" in name_lower and "tool" not in name_lower:
            return 8  # Core agent component

        # Medium-high priority (6-7): Common use cases
        if "file" in name_lower and "input" in category_lower:
            return 7  # Common for RAG
        if "recursivecharactertextsplitter" in name_lower.replace(" ", ""):
            return 7  # Preferred text splitter
        if "vector" in name_lower and "store" in name_lower:
            if "inmemory" in name_lower.replace(" ", ""):
                return 6  # Good for testing
            return 7  # Production vector stores

        # Medium priority (4-5): Specialized but useful
        if "memory" in name_lower:
            return 5
        if "embedding" in name_lower:
            return 5
        if "tool" in category_lower:
            return 5  # Tools for agents

        # Lower priority (2-3): Less common or deprecated
        if "qianfan" in name_lower:
            return 2  # Avoid per system prompt
        if "legacy" in name_lower or "deprecated" in component.get("description", "").lower():
            return 2

        # Default priority
        return 4

    def _search_components(self, query: str, components: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Search for components matching a query with enhanced keyword matching and priority weighting."""
        query_lower = query.lower()
        results = []
        scored_results = []

        for category, category_components in components.items():
            for comp in category_components:
                score = 0

                # Exact name match (highest priority)
                if query_lower == comp["name"].lower():
                    score += 100

                # Display name match
                if query_lower in comp["display_name"].lower():
                    score += 50

                # Name substring match
                if query_lower in comp["name"].lower():
                    score += 30

                # Description match
                if query_lower in comp["description"].lower():
                    score += 20

                # Keywords match (new!)
                keywords_str = " ".join(comp.get("keywords", [])).lower()
                if query_lower in keywords_str:
                    score += 40

                # Check for partial keyword matches
                for keyword in comp.get("keywords", []):
                    if query_lower in keyword.lower() or keyword.lower() in query_lower:
                        score += 35
                        break

                # Role match (semantic understanding)
                role = comp.get("role", "")
                if role and query_lower in role.lower():
                    score += 45

                # Use case match (when to use)
                use_case = comp.get("use_case", "")
                if use_case and query_lower in use_case.lower():
                    score += 45

                # Apply priority multiplier (1-10 scale → 1.0-2.0 multiplier)
                priority = comp.get("priority", 5)
                priority_multiplier = 1.0 + (priority / 10.0)  # 1.1x to 2.0x boost
                final_score = int(score * priority_multiplier)

                # Add to results if any match found
                if final_score > 0:
                    scored_results.append((final_score, {**comp, "category": category}))

        # Sort by score (descending) and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_results[:10]]

        # Debug logging for top results
        if results:
            logger.info(f"Search '{query}' found {len(scored_results)} components, returning top {len(results)}:")
            for idx, (score, comp_data) in enumerate(scored_results[:5], 1):
                logger.info(f"  {idx}. {comp_data['name']} (score: {score}, priority: {comp_data.get('priority', 5)})")

        return results

    def _format_flow_response(self, flow_data: dict[str, Any], all_components: dict[str, Any]) -> dict[str, Any]:
        """Format the flow data for frontend consumption."""
        formatted_nodes = []
        node_positions = {}

        # Generate positions for nodes (simple vertical layout)
        for i, node in enumerate(flow_data["nodes"]):
            node_id = node["id"]
            node_positions[node_id] = {"x": 250, "y": 100 + i * 200}

            # Find full component data
            component_name = node["component_name"]
            component_data = None

            for category_components in all_components.values():
                if component_name in category_components:
                    component_data = category_components[component_name]
                    break

            if not component_data:
                logger.warning(f"Component {component_name} not found in available components")
                continue

            # Merge LLM config into component template
            template = component_data.get("template", {}).copy()
            llm_config = node.get("config", {})

            for param_name, param_value in llm_config.items():
                if param_name in template and isinstance(template[param_name], dict):
                    # Update the template field's value with LLM-provided config
                    template[param_name]["value"] = param_value
                    logger.info(f"Set {component_name}.{param_name} = {param_value}")
                else:
                    # Parameter not in template, log warning
                    logger.warning(f"Parameter {param_name} not found in {component_name} template")

            # Create updated component data with merged template
            updated_component_data = {**component_data, "template": template}

            formatted_nodes.append(
                {
                    "id": node_id,  # Include the node ID from LLM
                    "component_name": component_name,
                    "display_name": component_data.get("display_name", component_name),
                    "position": node_positions[node_id],
                    "data": {**component_data, "config": node.get("config", {})},
                }
            )

        formatted_edges = []
        for edge in flow_data["edges"]:
            formatted_edges.append(
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "source_handle": edge.get("source_handle") or edge.get("source_output"),
                    "target_handle": edge.get("target_handle") or edge.get("target_input"),
                }
            )

        return {
            "nodes": formatted_nodes,
            "edges": formatted_edges,
            "explanation": flow_data.get("explanation", ""),
        }

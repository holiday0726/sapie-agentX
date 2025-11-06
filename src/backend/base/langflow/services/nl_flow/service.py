"""Service for converting natural language to Langflow flows using LLM Function Calling."""

import json
import os
from typing import Any

from loguru import logger


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
                                            "description": "Configuration for the component (e.g., prompts, parameters)",
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
3. Creating a valid flow structure with create_flow

Guidelines:
- Keep flows simple (2-4 components for MVP)
- Common patterns:
  * Chatbot: ChatInput → ChatModel → ChatOutput
  * RAG: DocumentLoader → TextSplitter → VectorStore → ChatModel
  * Agent: ChatInput → Agent → ChatOutput
- Ensure component connections are compatible
- Generate appropriate prompts for model components
"""

            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

            # Function calling loop
            max_iterations = 5
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
                elif function_name == "create_flow":
                    flow_result = function_args
                    result = {"status": "success", "message": "Flow created"}
                else:
                    result = {"error": f"Unknown function: {function_name}"}

                # Add function result to conversation
                messages.append({"role": "assistant", "content": None, "function_call": message.function_call})
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
                simplified[category].append(
                    {
                        "name": name,
                        "display_name": component.get("display_name", name),
                        "description": component.get("description", ""),
                        "input_types": component.get("input_types", []),
                        "output_types": component.get("output_types", []),
                    }
                )

        return simplified

    def _search_components(self, query: str, components: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Search for components matching a query."""
        query_lower = query.lower()
        results = []

        for category, category_components in components.items():
            for comp in category_components:
                # Simple keyword matching
                if (
                    query_lower in comp["name"].lower()
                    or query_lower in comp["display_name"].lower()
                    or query_lower in comp["description"].lower()
                ):
                    results.append({**comp, "category": category})

        return results[:10]  # Limit to top 10 results

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
                    "source_handle": edge.get("source_handle"),
                    "target_handle": edge.get("target_handle"),
                }
            )

        return {
            "nodes": formatted_nodes,
            "edges": formatted_edges,
            "explanation": flow_data.get("explanation", ""),
        }

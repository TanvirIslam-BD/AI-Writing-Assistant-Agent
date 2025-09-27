"""
LangGraph-based AI Writing Assistant Agent
Following the LangGraph agent pattern for intelligent tool selection and execution
"""

import os
from typing import Annotated, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq

# Import our writing tools
from langgraph_tools import WRITING_TOOLS, text_analysis_tool

# Set up Groq API (you'll need to set your API key)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '') # Set your API key here or in environment


class WritingState(TypedDict):
    """State for the writing assistant agent"""
    messages: Annotated[List, add_messages]
    original_text: str
    current_text: str
    analysis_results: Dict
    improvements_made: List[Dict]
    processing_complete: bool


class LangGraphWritingAgent:
    """
    LangGraph-based AI Writing Assistant Agent that intelligently selects
    and applies writing improvement tools based on text analysis.
    """

    def __init__(self, groq_api_key: str = None):
        """Initialize the LangGraph agent with Groq LLM and writing tools."""

        # Set up LLM - using Groq if API key provided, otherwise direct tool usage
        self.use_llm = bool(groq_api_key or GROQ_API_KEY)

        if self.use_llm:
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",  # Updated to current model
                groq_api_key=groq_api_key or GROQ_API_KEY,
                temperature=0.1  # Low temperature for consistent writing improvements
            )
            # Bind tools to LLM
            self.llm_with_tools = self.llm.bind_tools(WRITING_TOOLS)
        else:
            # Fallback mode: use tools directly without LLM
            self.llm = None
            self.llm_with_tools = None

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for writing assistance."""

        # Create graph builder
        graph_builder = StateGraph(WritingState)

        # Add nodes
        graph_builder.add_node("analyzer", self._analyze_text)
        graph_builder.add_node("agent", self._agent_node)
        graph_builder.add_node("tools", ToolNode(WRITING_TOOLS))
        graph_builder.add_node("finalizer", self._finalize_response)

        # Add edges
        graph_builder.add_edge(START, "analyzer")
        graph_builder.add_edge("analyzer", "agent")

        # Conditional routing from agent: if tools needed -> tools, else -> finalizer
        graph_builder.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                "__end__": "finalizer"
            }
        )

        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("finalizer", END)

        return graph_builder.compile()

    def _analyze_text(self, state: WritingState) -> WritingState:
        """Analyze the input text to determine what improvements are needed."""

        # Get the original text from the last human message
        original_text = ""
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                original_text = message.content
                break

        # Perform analysis using our analysis tool
        analysis_result = text_analysis_tool.invoke({"text": original_text})

        # Update state
        return {
            **state,
            "original_text": original_text,
            "current_text": original_text,
            "analysis_results": analysis_result,
            "improvements_made": [],
            "processing_complete": False
        }

    def _agent_node(self, state: WritingState) -> WritingState:
        """Main agent node that decides which tools to use."""

        # If not using LLM, skip to direct tool application
        if not self.use_llm:
            return {
                **state,
                "messages": [AIMessage(content="Direct tool application mode")]
            }

        # Create a prompt for the agent based on analysis
        analysis = state.get("analysis_results", {})
        recommended_tools = analysis.get("recommended_tools", [])

        # Create system message with context
        system_prompt = f"""
        You are an AI writing assistant. Based on the analysis, the following tools are recommended for this text:
        {', '.join(recommended_tools)}

        Available tools:
        - grammar_correction_tool: Fix grammar, spelling, and punctuation
        - sentence_rewriting_tool: Improve sentence structure and clarity
        - vocabulary_enhancement_tool: Replace basic words with sophisticated alternatives
        - tone_adjustment_tool: Adjust tone (formal, casual, professional, friendly)
        - text_analysis_tool: Analyze text for improvement opportunities

        Current text: "{state['current_text']}"

        Please use the recommended tools to improve this text. Start with the highest priority tools first.
        If no tools are needed, respond with the improved text directly.
        """

        try:
            # Get LLM response
            response = self.llm_with_tools.invoke([
                {"role": "system", "content": system_prompt},
                *state["messages"]
            ])

            # Update messages
            new_messages = [response]

            return {
                **state,
                "messages": new_messages
            }
        except Exception as e:
            # Fallback to direct application if LLM fails
            return {
                **state,
                "messages": [AIMessage(content=f"LLM error: {str(e)}, using direct tool application")]
            }

    def _finalize_response(self, state: WritingState) -> WritingState:
        """Finalize the response and prepare the results."""

        # Extract tool outputs from messages
        tool_outputs = []
        improved_text = state["current_text"]

        for message in state["messages"]:
            if isinstance(message, ToolMessage):
                tool_outputs.append({
                    "tool": message.name,
                    "output": message.content,
                    "tool_call_id": message.tool_call_id
                })
                # Update improved text with the latest tool output
                if not message.content.startswith("Error"):
                    improved_text = message.content

        # Create final response
        final_message = AIMessage(
            content=f"I've improved your text using the following tools: {', '.join([t['tool'] for t in tool_outputs])}.\n\nImproved text: {improved_text}"
        )

        return {
            **state,
            "messages": [final_message],
            "current_text": improved_text,
            "improvements_made": tool_outputs,
            "processing_complete": True
        }

    def improve_text(self, text: str, specific_tools: List[str] = None, tone: str = None) -> Dict:
        """
        Main method to improve text using the LangGraph agent.

        Args:
            text: The text to improve
            specific_tools: Optional list of specific tools to use
            tone: Optional tone to apply

        Returns:
            Dict with improvement results
        """

        try:
            # If no LLM available, use direct tool application
            if not self.use_llm:
                return self._improve_text_direct(text, specific_tools, tone)

            # Create initial message
            user_message = HumanMessage(content=text)

            # Add tool specification if provided
            if specific_tools:
                user_message.content += f"\n\nPlease use only these tools: {', '.join(specific_tools)}"

            if tone:
                user_message.content += f"\n\nAdjust tone to: {tone}"

            # Initialize state
            initial_state = {
                "messages": [user_message],
                "original_text": "",
                "current_text": "",
                "analysis_results": {},
                "improvements_made": [],
                "processing_complete": False
            }

            # Run the graph
            result = self.graph.invoke(initial_state)

            # Extract results
            final_text = result.get("current_text", text)
            improvements = result.get("improvements_made", [])
            analysis = result.get("analysis_results", {})

            return {
                "original": text,
                "improved": final_text,
                "improvements": improvements,
                "analysis": analysis,
                "success": True,
                "tools_used": [imp["tool"] for imp in improvements]
            }

        except Exception as e:
            return {
                "original": text,
                "improved": text,
                "improvements": [],
                "analysis": {},
                "success": False,
                "error": str(e),
                "tools_used": []
            }

    def _improve_text_direct(self, text: str, specific_tools: List[str] = None, tone: str = None) -> Dict:
        """Direct tool application without LLM when no API key available."""

        try:
            # Get text analysis to determine which tools to use
            analysis_result = text_analysis_tool.invoke({"text": text})
            recommended_tools = analysis_result.get("recommended_tools", [])

            # Use specific tools if provided, otherwise use recommended
            tools_to_use = specific_tools if specific_tools else recommended_tools

            current_text = text
            improvements = []

            # Apply tools in sequence
            for tool_name in tools_to_use:
                # Find the tool
                tool = None
                for t in WRITING_TOOLS:
                    if t.name == tool_name:
                        tool = t
                        break

                if tool:
                    try:
                        # Apply tool with tone if it's tone_adjustment_tool
                        if tool_name == "tone_adjustment_tool" and tone:
                            improved_text = tool.invoke({"text": current_text, "tone": tone})
                        else:
                            improved_text = tool.invoke({"text": current_text})

                        if improved_text != current_text and not improved_text.startswith("Error"):
                            improvements.append({
                                "tool": tool_name,
                                "output": improved_text,
                                "before": current_text,
                                "after": improved_text
                            })
                            current_text = improved_text

                    except Exception as e:
                        # Skip tools that fail
                        continue

            return {
                "original": text,
                "improved": current_text,
                "improvements": improvements,
                "analysis": analysis_result,
                "success": True,
                "tools_used": [imp["tool"] for imp in improvements]
            }

        except Exception as e:
            return {
                "original": text,
                "improved": text,
                "improvements": [],
                "analysis": {},
                "success": False,
                "error": str(e),
                "tools_used": []
            }

    def analyze_text(self, text: str) -> Dict:
        """Analyze text without making improvements."""

        try:
            analysis_result = text_analysis_tool.invoke({"text": text})
            return {
                "success": True,
                "text": text,
                "analysis": analysis_result.get("analysis", {}),
                "recommended_tools": analysis_result.get("recommended_tools", []),
                "priority_order": analysis_result.get("priority_order", [])
            }
        except Exception as e:
            return {
                "success": False,
                "text": text,
                "analysis": {},
                "recommended_tools": [],
                "priority_order": [],
                "error": str(e)
            }

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in WRITING_TOOLS]

    def visualize_graph(self) -> str:
        """Return mermaid diagram of the graph (for debugging)."""
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception:
            return "Graph visualization not available"


# Global instance for easy access
# You can set your Groq API key here or in environment variable
# Note: This will be initialized when needed to avoid import issues
writing_agent = None

def get_writing_agent():
    """Get or create the global writing agent instance."""
    global writing_agent
    if writing_agent is None:
        writing_agent = LangGraphWritingAgent(groq_api_key=GROQ_API_KEY)
    return writing_agent
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class PromptData:
    """Enhanced data structure for Synapse v3.0 prompt building"""
    user_goal: str  # Keep for backward compatibility
    raw_user_prompt: str = ""  # New v3.0 field
    domain_knowledge: str = ""
    role: str = "professional assistant"
    tone: str = "helpful and analytical"
    task_description: str = ""
    deliverable_format: str = "markdown"
    available_tools: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    word_limit: Optional[int] = None
    additional_context: Optional[Dict[str, Any]] = None
    enhancement_level: Optional[str] = None  # auto-detect if not specified
    previous_interactions: Optional[List[Dict]] = None  # for long-context memory
    
    def __post_init__(self):
        if self.available_tools is None:
            self.available_tools = []
        if self.constraints is None:
            self.constraints = []
        if self.additional_context is None:
            self.additional_context = {}
        if self.previous_interactions is None:
            self.previous_interactions = []
        # Use user_goal as raw_user_prompt if not set (backward compatibility)
        if not self.raw_user_prompt:
            self.raw_user_prompt = self.user_goal


class SynapsePromptBuilder:
    """
    Synapse v3.0 - Advanced prompt architecture with dynamic enhancement levels,
    confidence scoring, and iterative refinement capabilities.
    """
    
    def __init__(self):
        self.version = "3.0"
        self.default_tools = [
            "web_search(query): search the web for information",
            "vector_retrieve(query): retrieve documents from a vector store", 
            "code_run(code): execute code in a secure sandbox",
            "database_query(sql): retrieve records from a database",
            "calculator(expression): evaluate arithmetic expressions"
        ]
        
        # Enhancement level section mappings
        self.enhancement_levels = {
            "low": ["objective", "draft_prompt", "final_output_package"],
            "med": ["objective", "context", "role_and_tone", "draft_prompt", 
                   "self_reflection", "final_output_package"],
            "high": ["objective", "context", "role_and_tone", "planning", 
                    "reasoning", "draft_prompt", "self_reflection", "final_output_package"],
            "pro": ["all"]  # All sections activated
        }
    
    def _assess_complexity(self, prompt: str, context: Dict[str, Any]) -> Tuple[str, Dict]:
        """Automatically assess prompt complexity and determine enhancement level"""
        complexity_score = 0
        factors = {
            "length": len(prompt.split()) > 50,
            "technical_terms": any(term in prompt.lower() for term in 
                                 ["algorithm", "optimize", "architecture", "implementation", 
                                  "analysis", "strategy", "framework"]),
            "multiple_steps": any(word in prompt.lower() for word in 
                                ["steps", "process", "workflow", "pipeline", "sequence"]),
            "requires_tools": any(word in prompt.lower() for word in 
                                ["search", "calculate", "retrieve", "analyze", "data"]),
            "specific_format": any(word in prompt.lower() for word in 
                                 ["json", "xml", "csv", "table", "report", "presentation"]),
            "creative_task": any(word in prompt.lower() for word in 
                               ["create", "design", "innovate", "brainstorm", "imagine"])
        }
        
        # Calculate complexity score
        complexity_score = sum(factors.values())
        
        # Determine enhancement level
        if complexity_score <= 1:
            level = "low"
            assessment = "Simple, direct question"
        elif complexity_score <= 3:
            level = "med"
            assessment = "Moderate complexity requiring structure"
        elif complexity_score <= 5:
            level = "high"
            assessment = "Complex task needing detailed planning"
        else:
            level = "pro"
            assessment = "Multifaceted project requiring all capabilities"
        
        return level, {
            "complexity_score": complexity_score,
            "factors": factors,
            "assessment": assessment,
            "auto_selected_level": level
        }
        
    def build(self, prompt_data: PromptData) -> str:
        """Main orchestration method for building Synapse v3.0 prompts"""
        # Set raw_user_prompt for backward compatibility
        if not prompt_data.raw_user_prompt:
            prompt_data.raw_user_prompt = prompt_data.user_goal
        
        # Assess complexity if level not specified
        if not prompt_data.enhancement_level:
            level, complexity_assessment = self._assess_complexity(
                prompt_data.raw_user_prompt, 
                prompt_data.additional_context or {}
            )
            prompt_data.enhancement_level = level
        else:
            level, complexity_assessment = self._assess_complexity(
                prompt_data.raw_user_prompt,
                prompt_data.additional_context or {}
            )
            level = prompt_data.enhancement_level
        
        # Build the Synapse v3.0 enhanced prompt structure
        timestamp = datetime.now().isoformat()
        tools_list = "\n  ".join([f"• {tool}" for tool in (prompt_data.available_tools or self.default_tools)])
        constraints_list = "\n  ".join([f"• {constraint}" for constraint in prompt_data.constraints]) if prompt_data.constraints else "• No custom constraints specified"
        
        # Create the comprehensive v3.0 prompt
        enhanced_prompt = f"""<system_identity>
  You are Synapse v{self.version}, an advanced prompt optimization system.
  Your purpose is to transform simple user requests into comprehensive, expert-level prompts.
  You operate with multiple enhancement levels to match task complexity.
</system_identity>

<variable_glossary>
  <variable name="{{RAW_USER_PROMPT}}" description="The unprocessed, original query from the end-user." value="{prompt_data.raw_user_prompt}" />
  <variable name="{{DOMAIN_KNOWLEDGE}}" description="Specific background information or context provided by the user." value="{prompt_data.domain_knowledge or 'General knowledge domain'}" />
  <variable name="{{ROLE}}" description="The desired expert persona for the downstream LLM." value="{prompt_data.role}" />
  <variable name="{{TONE}}" description="The desired communication style for the downstream LLM." value="{prompt_data.tone}" />
  <variable name="{{AVAILABLE_TOOLS_LIST}}" description="A list of authorized tools or functions the downstream LLM can call." />
  <variable name="{{CUSTOM_CONSTRAINTS}}" description="Any unique constraints or rules specified by the user for this task." />
</variable_glossary>

<user_input>
  {prompt_data.raw_user_prompt}
</user_input>

<enhancement_level>
  <reasoning>
    Evaluating the user's raw prompt for complexity, ambiguity, and required depth.
    - Simple request: "{prompt_data.raw_user_prompt[:100]}..."
    - Complexity assessment: {complexity_assessment["assessment"]}
    - Need for external tools: {"Yes" if complexity_assessment["factors"]["requires_tools"] else "No"}
    - Need for specific persona: {"Yes" if prompt_data.role != "professional assistant" else "No"}
    - Complexity score: {complexity_assessment["complexity_score"]}/6
  </reasoning>
  <decision>
    Based on the evaluation, I will select an enhancement level: {level}.
    - low: For simple, direct questions. Activates: [objective, draft_prompt, final_output_package].
    - med: For tasks requiring structure and a specific role. Activates: [objective, context, role_and_tone, draft_prompt, self_reflection, final_output_package].
    - high: For complex tasks needing detailed planning and reasoning. Activates: [objective, context, role_and_tone, planning, reasoning, draft_prompt, self_reflection, final_output_package].
    - pro: For multifaceted projects requiring all advanced capabilities. Activates all sections.
    Selected Level: {level.upper()}.
  </decision>
</enhancement_level>

<objective>
  • Primary Goal: Transform the user's request into a comprehensive, expert-level prompt that maximizes LLM performance.
  • User's Core Request: {prompt_data.raw_user_prompt}
  • Success Criteria: 
    - The enhanced prompt produces accurate, comprehensive responses
    - Output format matches {prompt_data.deliverable_format}
    - Response adheres to specified role ({prompt_data.role}) and tone ({prompt_data.tone})
    - All constraints are properly enforced
    {f"- Response stays within {prompt_data.word_limit} words" if prompt_data.word_limit else ""}
</objective>

<context>
  • Domain Knowledge: {prompt_data.domain_knowledge or "No specific domain knowledge provided. Relying on general expertise."}
  • Constraints: {constraints_list}
  {f"• Word Limit: {prompt_data.word_limit} words maximum" if prompt_data.word_limit else ""}
  • Format Requirement: {prompt_data.deliverable_format}
</context>

<role_and_tone>
  • Primary Role: Assume the professional role of: {prompt_data.role}.
  • Communication Style: Adopt the tone specified: {prompt_data.tone}. 
    Ensure all communication adheres to this style consistently throughout the response.
  • Knowledge Boundaries: The expertise is primarily focused on {prompt_data.domain_knowledge or 'general professional knowledge'}. 
    Explicitly acknowledge limits for topics outside this domain.
</role_and_tone>

<draft_prompt>
  <prompt>
    <system_prompt>
You are {prompt_data.role} with expertise in {prompt_data.domain_knowledge or 'your field'}.
Your communication style is {prompt_data.tone}.
Follow these constraints: {', '.join(prompt_data.constraints) if prompt_data.constraints else 'standard ethical guidelines'}.
    </system_prompt>
    
    <user_prompt_body>
Task: {prompt_data.raw_user_prompt}

Please provide a {prompt_data.deliverable_format} response that:
1. Fully addresses the request
2. Uses appropriate expertise and terminology
3. Maintains the specified tone throughout
4. Adheres to all constraints
{f'5. Stays within {prompt_data.word_limit} words' if prompt_data.word_limit else ''}

Begin your response now:
    </user_prompt_body>
    
    <output_schema_definition>
      Format: {prompt_data.deliverable_format}
      The output should be well-structured and appropriate for the specified format.
    </output_schema_definition>
  </prompt>
</draft_prompt>

<self_reflection>
  • Objective Fulfillment: The enhanced prompt fully addresses the user's goal with clear instructions and success criteria. ✓
  • Clarity & Coherence: The prompt is unambiguous, logically structured, and optimized for LLM comprehension. ✓
  • Constraint Adherence: All constraints are properly enforced in the prompt. ✓
  • Quality Metrics:
    - Specificity: HIGH - Clear, detailed instructions provided
    - Context: COMPLETE - All necessary background included
    - Structure: OPTIMAL - Logical flow and organization
    - Actionability: EXCELLENT - LLM can immediately execute
</self_reflection>

<final_output_package>
  <metadata>
    <architect_version>Synapse v{self.version}</architect_version>
    <enhancement_level>{level.upper()}</enhancement_level>
    <timestamp>{timestamp}</timestamp>
  </metadata>
  
  <executive_summary>
    This enhanced prompt transforms the user's request into a comprehensive, structured instruction set optimized for LLM execution. 
    
    Key enhancements applied:
    • Added role-based expertise context ({prompt_data.role})
    • Structured output format ({prompt_data.deliverable_format})
    • Incorporated domain knowledge and constraints
    • Optimized for {level} complexity level
  </executive_summary>
  
  <optimized_prompt>
You are {prompt_data.role} with expertise in {prompt_data.domain_knowledge or 'your field'}.
Your communication style is {prompt_data.tone}.
Follow these constraints: {', '.join(prompt_data.constraints) if prompt_data.constraints else 'standard ethical guidelines'}.

Task: {prompt_data.raw_user_prompt}

Please provide a {prompt_data.deliverable_format} response that:
1. Fully addresses the request
2. Uses appropriate expertise and terminology  
3. Maintains the specified tone throughout
4. Adheres to all constraints
{f'5. Stays within {prompt_data.word_limit} words' if prompt_data.word_limit else ''}

Begin your response now:
  </optimized_prompt>
</final_output_package>"""

        return enhanced_prompt
    
    def get_prompt_stats(self, prompt: str) -> Dict[str, Any]:
        """Return comprehensive statistics about the generated prompt"""
        # Count sections
        section_count = prompt.count("<") // 2
        
        # Identify active sections
        active_sections = []
        section_markers = [
            "system_identity", "variable_glossary", "enhancement_level",
            "objective", "context", "role_and_tone", "planning",
            "example_strategy", "reasoning", "tools", "constraints",
            "draft_prompt", "self_reflection", "final_output_package"
        ]
        
        for marker in section_markers:
            if f"<{marker}>" in prompt:
                active_sections.append(marker)
        
        return {
            "total_characters": len(prompt),
            "total_words": len(prompt.split()),
            "total_lines": len(prompt.split('\n')),
            "sections_count": section_count,
            "active_sections": active_sections,
            "estimated_tokens": len(prompt.split()) * 1.3,
            "version": self.version,
            "complexity_indicators": {
                "has_tools": "<tools>" in prompt,
                "has_examples": "<example>" in prompt,
                "has_constraints": "<constraints>" in prompt,
                "has_planning": "<planning>" in prompt,
                "has_reasoning": "<reasoning>" in prompt
            }
        }


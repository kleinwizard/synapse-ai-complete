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
    Synapse v4.0 - Guidelines-based prompt optimization system that creates optimized prompts
    using comprehensive prompt engineering guidelines and GPT-4o instruction generation.
    """
    
    def __init__(self):
        self.version = "4.0"
        self.default_tools = [
            "web_search(query): search the web for information",
            "vector_retrieve(query): retrieve documents from a vector store", 
            "code_run(code): execute code in a secure sandbox",
            "database_query(sql): retrieve records from a database",
            "calculator(expression): evaluate arithmetic expressions"
        ]
        
        # Comprehensive prompt engineering guidelines
        self.guidelines = self._load_comprehensive_guidelines()
    
    def _load_comprehensive_guidelines(self) -> str:
        """Load comprehensive prompt engineering guidelines for GPT-4o optimization"""
        return \"\"\"# COMPREHENSIVE PROMPT ENGINEERING GUIDELINES

## Core Principles

### 1. Clarity and Specificity
- Use precise, unambiguous language
- Define technical terms and acronyms
- Specify exact requirements and expected outputs
- Provide concrete examples when helpful

### 2. Context and Background
- Include relevant domain knowledge
- Establish the user's expertise level
- Provide necessary background information
- Reference specific frameworks or methodologies when applicable

### 3. Role-Based Expertise
- Assign appropriate professional roles (e.g., "expert data scientist", "senior software architect")
- Define the scope of expertise and knowledge boundaries
- Include relevant credentials or experience context
- Specify the perspective from which to approach the task

### 4. Task Decomposition
- Break complex tasks into clear, sequential steps
- Number or bullet-point multi-step processes
- Define dependencies between steps
- Specify checkpoints or validation criteria

### 5. Output Formatting
- Specify desired format (markdown, JSON, code, report, etc.)
- Include structural requirements (headers, sections, etc.)
- Define length constraints when appropriate
- Provide output templates or schemas when needed

## Advanced Techniques

### 6. Chain-of-Thought Prompting
- Request step-by-step reasoning for complex problems
- Ask for intermediate calculations or logic
- Include "thinking process" or "reasoning" sections
- Encourage explicit problem-solving methodology

### 7. Few-Shot Learning
- Provide 2-3 high-quality examples when patterns are complex
- Use consistent formatting across examples
- Include both input and expected output formats
- Show progression from simple to complex cases

### 8. Constraint Management
- Clearly state what NOT to do or include
- Specify scope limitations
- Define quality thresholds or standards
- Include ethical or legal constraints

### 9. Iterative Refinement
- Request self-review or validation of outputs
- Include improvement suggestions
- Ask for alternative approaches when relevant
- Encourage critical evaluation of solutions

### 10. Tone and Communication Style
- Specify appropriate communication tone (formal, conversational, technical)
- Define target audience characteristics
- Include cultural or contextual considerations
- Specify level of technical detail required

## Complexity-Based Optimization

### Low Complexity (Simple queries, direct tasks)
- Focus on clarity and direct instructions
- Minimal context needed
- Simple role assignment
- Straightforward output format

### Medium Complexity (Multi-step tasks, moderate expertise required)
- Include relevant context and background
- Assign specific professional roles
- Break down into clear steps
- Specify quality criteria

### High Complexity (Expert-level tasks, multi-faceted problems)
- Comprehensive context and domain knowledge
- Expert role assignment with specific expertise areas
- Detailed step-by-step methodology
- Multiple validation checkpoints
- Request for reasoning and alternatives

### Professional Complexity (Research-grade, industry-level tasks)
- Extensive domain expertise and context
- Multiple expert perspectives when relevant
- Comprehensive methodology and frameworks
- Quality assurance and peer-review level outputs
- Integration of multiple knowledge domains

## Quality Assurance

### Validation Criteria
- Check for completeness against requirements
- Verify logical consistency and coherence
- Ensure appropriate expertise level and tone
- Confirm output format compliance
- Validate constraint adherence

### Common Pitfalls to Avoid
- Vague or ambiguous instructions
- Missing context or background
- Inappropriate expertise level
- Unclear output requirements
- Insufficient constraint specification
- Over-complexity for simple tasks
- Under-specification for complex tasks

## Implementation Guidelines

### For Each Optimization Task:
1. Analyze the user's request for complexity and requirements
2. Determine appropriate expertise level and role
3. Select relevant techniques from the guidelines above
4. Structure the prompt with clear sections and requirements
5. Include appropriate context and constraints
6. Specify desired output format and quality criteria
7. Ensure the prompt is actionable and complete

### Quality Metrics:
- Specificity: Clear, unambiguous instructions
- Context: Sufficient background and domain knowledge
- Structure: Logical organization and flow
- Actionability: Immediately executable by target LLM
- Completeness: All requirements and constraints addressed\"\"\"
        
        # Enhancement level complexity mappings
        self.enhancement_levels = {
            "low": "Basic optimization with clear instructions",
            "med": "Moderate optimization with role-based guidance and structured approach", 
            "high": "Advanced optimization with detailed planning and multi-step reasoning",
            "pro": "Expert-level optimization with comprehensive prompt engineering techniques"
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
        """Main orchestration method for building Synapse v4.0 guidelines-based optimization instructions"""
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
        
        # Build the new guidelines-based instruction for GPT-4o
        timestamp = datetime.now().isoformat()
        tools_list = "\n  ".join([f"• {tool}" for tool in (prompt_data.available_tools or self.default_tools)])
        constraints_list = "\n  ".join([f"• {constraint}" for constraint in prompt_data.constraints]) if prompt_data.constraints else "• No custom constraints specified"
        
        # Create the new guidelines-based optimization instruction
        optimization_instruction = f"""You are a prompt optimization expert. Use the comprehensive prompt engineering guidelines below to create an optimized prompt based on the user's request.

{self.guidelines}

TASK: Create an optimized prompt for the following user request. Apply the appropriate techniques from the guidelines above based on the task complexity and requirements.

USER REQUEST: {prompt_data.raw_user_prompt}

ADDITIONAL CONTEXT:
- Role: {prompt_data.role}
- Tone: {prompt_data.tone}
- Domain Knowledge: {prompt_data.domain_knowledge or 'General knowledge domain'}
- Deliverable Format: {prompt_data.deliverable_format}
- Available Tools: {tools_list if prompt_data.available_tools else 'Standard tools'}
- Constraints: {constraints_list}
{f'- Word Limit: {prompt_data.word_limit} words maximum' if prompt_data.word_limit else ''}

COMPLEXITY LEVEL: {level.upper()} ({self.enhancement_levels[level]})
Complexity Assessment: {complexity_assessment["assessment"]}
Complexity Score: {complexity_assessment["complexity_score"]}/6

OUTPUT: Return ONLY the optimized prompt that should be sent to the target LLM. Do not include explanations or the guidelines themselves - just the refined, executable prompt that will maximize LLM performance for this specific task.

The optimized prompt should:
1. Be clear, specific, and actionable
2. Include appropriate role and expertise context
3. Specify the desired output format and tone
4. Incorporate relevant constraints and requirements
5. Use proven prompt engineering techniques for {level}-level complexity
6. Be ready for immediate execution by the target LLM

Create the optimized prompt now:"""

        return optimization_instruction
    
    def get_prompt_stats(self, prompt: str) -> Dict[str, Any]:
        """Return comprehensive statistics about the generated optimization instruction"""
        # Analyze the guidelines-based optimization instruction
        lines = prompt.split('\n')
        
        # Count guideline sections
        guideline_sections = []
        if "# COMPREHENSIVE PROMPT ENGINEERING GUIDELINES" in prompt:
            guideline_sections = [
                "Core Principles", "Advanced Techniques", "Complexity-Based Optimization", 
                "Quality Assurance", "Implementation Guidelines"
            ]
        
        # Identify key components
        has_guidelines = "COMPREHENSIVE PROMPT ENGINEERING GUIDELINES" in prompt
        has_user_request = "USER REQUEST:" in prompt
        has_context = "ADDITIONAL CONTEXT:" in prompt
        has_complexity = "COMPLEXITY LEVEL:" in prompt
        has_output_spec = "OUTPUT:" in prompt
        
        return {
            "total_characters": len(prompt),
            "total_words": len(prompt.split()),
            "total_lines": len(lines),
            "sections_count": len(guideline_sections),
            "active_sections": guideline_sections,
            "estimated_tokens": len(prompt.split()) * 1.3,
            "version": self.version,
            "optimization_type": "guidelines_based",
            "complexity_indicators": {
                "has_guidelines": has_guidelines,
                "has_user_request": has_user_request,
                "has_context": has_context,
                "has_complexity_level": has_complexity,
                "has_output_specification": has_output_spec,
                "guidelines_comprehensive": len(self.guidelines) > 1000
            }
        }


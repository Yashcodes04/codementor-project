import google.generativeai as genai
import json
import os
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
import logging
import asyncio
import time
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiHintService:
    def __init__(self):
        # Initialize Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Rate limiting (Gemini free tier: 15 requests/minute)
        self.request_timestamps = []
        self.max_requests_per_minute = 14  # Stay under 15 limit
        
        # Hint cache to avoid duplicate requests
        self.hint_cache = {}
        
        logger.info("Google Gemini client initialized successfully")
        
        # Setup prompt templates
        self.setup_prompts()
    
    def setup_prompts(self):
        """Setup prompt templates for different hint levels"""
        
        self.level_1_template = """
You are a coding mentor helping a student with a programming problem. Provide a Level 1 hint that identifies the problem type and suggests the general approach WITHOUT giving away the solution.

Problem: {title}
Difficulty: {difficulty}
Description: {description}
Examples: {examples}

Level 1 Hint Guidelines:
- Identify the problem category (array, string, tree, graph, dynamic programming, etc.)
- Suggest the general algorithmic approach
- Mention relevant data structures
- DO NOT provide specific implementation details
- Keep it educational and encouraging
- Limit to 2-3 sentences

Provide only the hint text, nothing else:
"""
        
        self.level_2_template = """
You are a coding mentor providing a Level 2 hint. The student already received Level 1 guidance.

Problem: {title}
Difficulty: {difficulty}
Description: {description}
Examples: {examples}
Previous Hint: {level_1_hint}

Level 2 Hint Guidelines:
- Build upon the Level 1 hint
- Provide more specific algorithmic guidance
- Suggest the step-by-step approach
- Mention time/space complexity considerations
- Give hints about edge cases to consider
- Still avoid giving exact implementation code
- Keep it educational and progressive
- Limit to 3-4 sentences

Provide only the hint text, nothing else:
"""
        
        self.level_3_template = """
You are a coding mentor providing a Level 3 hint. This is the most detailed hint before revealing the full solution.

Problem: {title}
Difficulty: {difficulty}
Description: {description}
Examples: {examples}
Previous Hints:
Level 1: {level_1_hint}
Level 2: {level_2_hint}

User Progress: {user_progress}

Level 3 Hint Guidelines:
- Provide implementation-level guidance
- Suggest specific coding patterns or templates
- Help with the most challenging part of the solution
- Give debugging tips if the user seems stuck
- Mention specific functions/methods that might help
- Provide pseudocode or code structure hints
- Still let the user write the actual code
- Be specific but educational
- Limit to 4-5 sentences

Provide only the hint text, nothing else:
"""

    def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            timestamp for timestamp in self.request_timestamps 
            if current_time - timestamp < 60
        ]
        
        # Check if we can make another request
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            logger.warning("Rate limit reached, waiting...")
            return False
        
        return True
    
    def wait_for_rate_limit(self):
        """Wait if we've hit the rate limit"""
        if not self.check_rate_limit():
            # Wait until we can make the next request
            oldest_request = min(self.request_timestamps)
            wait_time = 60 - (time.time() - oldest_request)
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.1f} seconds for rate limit...")
                time.sleep(wait_time + 1)  # Add 1 second buffer
    
    def generate_cache_key(self, problem: Dict[str, Any], level: int) -> str:
        """Generate cache key for hint"""
        title = problem.get('title', '')
        difficulty = problem.get('difficulty', '')
        return f"{title}_{difficulty}_{level}".lower().replace(' ', '_')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
    def generate_hint_with_gemini(self, prompt: str) -> str:
        """Generate hint using Gemini API with retry logic"""
        
        # Check rate limit before making request
        self.wait_for_rate_limit()
        
        try:
            # Record request timestamp
            self.request_timestamps.append(time.time())
            
            # Generate content with Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            # Extract text from response
            if response.text:
                hint = response.text.strip()
                logger.info(f"Successfully generated hint with Gemini (length: {len(hint)})")
                return self.clean_hint(hint)
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def clean_hint(self, hint: str) -> str:
        """Clean and format the hint text"""
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "Here's a hint:",
            "Hint:",
            "Here's your hint:",
            "For this problem:",
            "Level 1 hint:",
            "Level 2 hint:", 
            "Level 3 hint:"
        ]
        
        hint_clean = hint.strip()
        
        for prefix in prefixes_to_remove:
            if hint_clean.lower().startswith(prefix.lower()):
                hint_clean = hint_clean[len(prefix):].strip()
        
        # Remove any JSON formatting if present
        if hint_clean.startswith('{') and hint_clean.endswith('}'):
            try:
                parsed = json.loads(hint_clean)
                hint_clean = parsed.get('hint', hint_clean)
            except json.JSONDecodeError:
                pass
        
        return hint_clean
    
    def generate_hint(
        self, 
        problem: Dict[str, Any], 
        level: int, 
        previous_hints: List[str] = None,
        user_progress: Dict[str, Any] = None
    ) -> str:
        """
        Generate a hint for the given problem and level
        
        Args:
            problem: Problem data (title, description, difficulty, etc.)
            level: Hint level (1, 2, or 3)
            previous_hints: List of previously given hints
            user_progress: User's coding progress data
        
        Returns:
            Generated hint text
        """
        
        logger.info(f"Generating Level {level} hint for: {problem.get('title', 'Unknown')}")
        
        # Check cache first
        cache_key = self.generate_cache_key(problem, level)
        if cache_key in self.hint_cache:
            logger.info(f"Returning cached hint for {cache_key}")
            return self.hint_cache[cache_key]
        
        try:
            # Prepare prompt based on level
            if level == 1:
                prompt = self.level_1_template.format(
                    title=problem.get('title', ''),
                    description=self.truncate_text(problem.get('description', ''), 400),
                    difficulty=problem.get('difficulty', 'Unknown'),
                    examples=self.format_examples(problem.get('examples', []))
                )
            elif level == 2:
                prompt = self.level_2_template.format(
                    title=problem.get('title', ''),
                    description=self.truncate_text(problem.get('description', ''), 400),
                    difficulty=problem.get('difficulty', 'Unknown'),
                    examples=self.format_examples(problem.get('examples', [])),
                    level_1_hint=previous_hints[0] if previous_hints else "No previous hint available"
                )
            elif level == 3:
                prompt = self.level_3_template.format(
                    title=problem.get('title', ''),
                    description=self.truncate_text(problem.get('description', ''), 400),
                    difficulty=problem.get('difficulty', 'Unknown'),
                    examples=self.format_examples(problem.get('examples', [])),
                    level_1_hint=previous_hints[0] if previous_hints and len(previous_hints) > 0 else "No Level 1 hint available",
                    level_2_hint=previous_hints[1] if previous_hints and len(previous_hints) > 1 else "No Level 2 hint available",
                    user_progress=self.format_user_progress(user_progress)
                )
            else:
                raise ValueError(f"Invalid hint level: {level}")
            
            # Generate hint with Gemini
            hint = self.generate_hint_with_gemini(prompt)
            
            # Validate hint quality
            if self.is_valid_hint(hint, level):
                # Cache the result
                self.hint_cache[cache_key] = hint
                logger.info(f"Successfully generated and cached Level {level} hint")
                return hint
            else:
                logger.warning(f"Generated hint failed validation, using fallback")
                return self.get_fallback_hint(problem, level)
                
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return self.get_fallback_hint(problem, level)
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to fit within token limits"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def format_examples(self, examples: List[Dict]) -> str:
        """Format examples for prompt"""
        if not examples:
            return "No examples provided"
        
        formatted = []
        for i, example in enumerate(examples[:2]):  # Limit to 2 examples
            if isinstance(example, dict):
                content = example.get('content', str(example))
            else:
                content = str(example)
            
            # Truncate long examples
            if len(content) > 100:
                content = content[:100] + "..."
                
            formatted.append(f"Example {i+1}: {content}")
        
        return "\n".join(formatted)
    
    def format_user_progress(self, user_progress: Dict[str, Any]) -> str:
        """Format user progress for prompt"""
        if not user_progress:
            return "No progress data available"
        
        progress_parts = []
        
        lines = user_progress.get('lines_of_code', 0)
        if lines > 0:
            progress_parts.append(f"Has written {lines} lines of code")
        
        if user_progress.get('has_function'):
            progress_parts.append("Has function definition")
        
        if user_progress.get('has_loop'):
            progress_parts.append("Has loop structure")
        
        time_spent = user_progress.get('time_spent', 0)
        if time_spent > 0:
            minutes = time_spent // 60000  # Convert ms to minutes
            progress_parts.append(f"Has spent {minutes} minutes on this problem")
        
        if not progress_parts:
            return "Just started working on the problem"
        
        return "; ".join(progress_parts)
    
    def is_valid_hint(self, hint: str, level: int) -> bool:
        """Validate hint quality"""
        if not hint or len(hint.strip()) < 15:
            return False
        
        # Check for common AI failure patterns
        failure_patterns = [
            "I cannot", "I can't", "As an AI", "I'm not able", 
            "sorry", "apologize", "I don't have", "unable to"
        ]
        
        hint_lower = hint.lower()
        for pattern in failure_patterns:
            if pattern in hint_lower:
                return False
        
        # Check for reasonable length
        if len(hint) > 500:  # Too long
            return False
            
        if len(hint) < 20:  # Too short
            return False
        
        # Level-specific validation
        if level == 1:
            # Should mention problem type or approach
            level_1_keywords = [
                "algorithm", "approach", "problem", "consider", "think", 
                "method", "technique", "strategy", "array", "string", 
                "tree", "graph", "dynamic", "hash", "sort"
            ]
            if not any(keyword in hint_lower for keyword in level_1_keywords):
                return False
        
        return True
    
    def get_fallback_hint(self, problem: Dict[str, Any], level: int) -> str:
        """Provide fallback static hints when Gemini fails"""
        
        # Classify problem type for better fallbacks
        title_lower = problem.get('title', '').lower()
        description_lower = problem.get('description', '').lower()
        
        problem_type = self.classify_problem_type(title_lower, description_lower)
        
        fallback_hints = {
            'array': {
                1: "This is an array manipulation problem. Consider what operations you need to perform on the elements and think about using hash maps or two-pointer techniques for efficiency.",
                2: "Look at the pattern in the examples. You might need to iterate through the array while tracking indices or values. Consider the time complexity - can you solve it in O(n) time?",
                3: "For implementation, consider using a hash map to store values and their indices. Iterate through the array once, and for each element, check if its complement exists in your hash map."
            },
            'string': {
                1: "This is a string processing problem. Think about character manipulation, pattern matching, or string transformation. Consider if you need to process characters individually or in groups.",
                2: "Consider using string methods, character arrays, or sliding window techniques. Pay attention to edge cases like empty strings, single characters, or special characters.",
                3: "You might need to iterate through characters using indices or convert the string to a list for easier manipulation. Consider using two pointers if you need to compare characters from different positions."
            },
            'tree': {
                1: "This is a tree problem involving traversal or manipulation. Think about whether you need depth-first search (DFS), breadth-first search (BFS), or tree modification.",
                2: "Consider recursive solutions with proper base cases. Think about what information you need to pass down (top-down) or return up (bottom-up) during traversal.",
                3: "Implement recursive functions with base cases for null nodes. For DFS, consider pre-order, in-order, or post-order traversal. For BFS, use a queue to process nodes level by level."
            },
            'graph': {
                1: "This is a graph problem involving nodes and connections. Think about graph traversal, shortest paths, or connectivity. Consider how the graph is represented.",
                2: "Consider BFS for shortest paths or level-order problems, DFS for connectivity or path-finding. You'll need to track visited nodes to avoid cycles.",
                3: "Use a visited set or array to track processed nodes. For BFS, use a queue; for DFS, use recursion or a stack. Consider the graph representation - adjacency list or matrix."
            },
            'dp': {
                1: "This looks like a dynamic programming problem with overlapping subproblems. Think about breaking the problem into smaller, similar subproblems.",
                2: "Consider what state you need to track and how previous states relate to the current one. Look for optimal substructure and overlapping subproblems.",
                3: "Define your recurrence relation and identify base cases. You can use memoization (top-down) with recursion or tabulation (bottom-up) with iteration."
            },
            'math': {
                1: "This is a mathematical problem that requires algorithmic thinking. Consider the mathematical properties and patterns in the problem.",
                2: "Think about mathematical operations, number properties, or geometric relationships. Consider edge cases like negative numbers, zero, or overflow.",
                3: "Break down the mathematical operations step by step. Consider using mathematical formulas, modular arithmetic, or iterative calculations."
            }
        }
        
        category_hints = fallback_hints.get(problem_type, {
            1: "Break down this problem into smaller steps. What is the main operation or transformation you need to perform?",
            2: "Consider the time and space complexity requirements. Can you solve it with a direct approach, or do you need optimization?",
            3: "Think about the data structures and algorithms that best fit this problem. Consider edge cases and implement step by step."
        })
        
        return category_hints.get(level, "Keep working on it! You're making good progress.")
    
    def classify_problem_type(self, title_lower: str, description_lower: str) -> str:
        """Classify problem type for better fallback hints"""
        
        # Array problems
        if any(word in title_lower for word in ['array', 'subarray', 'sum', 'sorted', 'matrix', 'rotate', 'merge']):
            return 'array'
        
        # String problems
        elif any(word in title_lower for word in ['string', 'substring', 'palindrome', 'character', 'anagram', 'pattern']):
            return 'string'
        
        # Tree problems
        elif any(word in title_lower for word in ['tree', 'binary', 'node', 'root', 'leaf', 'depth', 'height']):
            return 'tree'
        
        # Graph problems
        elif any(word in title_lower for word in ['graph', 'island', 'path', 'connected', 'route', 'network']):
            return 'graph'
        
        # Dynamic Programming
        elif any(word in description_lower for word in ['optimal', 'minimum', 'maximum', 'dynamic', 'subproblem', 'overlapping']):
            return 'dp'
        
        # Math problems
        elif any(word in title_lower for word in ['number', 'digit', 'integer', 'math', 'calculate', 'reverse', 'factorial']):
            return 'math'
        
        else:
            return 'general'
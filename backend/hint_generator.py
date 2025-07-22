class HintGenerator:
    def __init__(self):
        self.hints_database = {
            "array": {
                1: "This is an array manipulation problem. Consider what operations you need to perform on the array elements.",
                2: "Think about using nested loops or specific array methods to process elements. Consider the time complexity.",
                3: "You might need to track indices or use additional data structures like hash maps for optimization."
            },
            "string": {
                1: "This is a string processing problem. Think about character manipulation and string properties.",
                2: "Consider using string methods, character arrays, or sliding window techniques.",
                3: "You might need to handle edge cases like empty strings or special characters."
            },
            "tree": {
                1: "This is a tree traversal or tree manipulation problem. Think about recursive solutions.",
                2: "Consider depth-first search (DFS) or breadth-first search (BFS) approaches.",
                3: "Implement recursive functions with base cases for null nodes and leaf nodes."
            },
            "graph": {
                1: "This is a graph problem. Think about how nodes are connected and what traversal you need.",
                2: "Consider using BFS for shortest path or level-order problems, DFS for connectivity.",
                3: "You'll need a visited set/array and possibly a queue (BFS) or stack (DFS)."
            },
            "dp": {
                1: "This looks like a dynamic programming problem. Think about overlapping subproblems.",
                2: "Consider what state you need to track and how previous states relate to current ones.",
                3: "Try building a DP table or using memoization with recursive solutions."
            },
            "two-pointer": {
                1: "This problem can likely be solved using the two-pointer technique.",
                2: "Consider placing pointers at different positions and moving them based on conditions.",
                3: "Think about when to move the left pointer vs right pointer to optimize your search."
            }
        }
    
    def generate_hint(self, problem, level: int, user_progress=None):
        problem_type = self.classify_problem(problem)
        
        if problem_type in self.hints_database:
            hints = self.hints_database[problem_type]
            if level in hints:
                return hints[level]
        
        generic_hints = {
            1: "Break down the problem into smaller steps. What is the main operation you need to perform?",
            2: "Think about the most efficient approach. Can you optimize the time or space complexity?",
            3: "Consider edge cases and implement your solution step by step."
        }
        
        return generic_hints.get(level, "Keep working on it! You're making progress.")
    
    def classify_problem(self, problem):
        title_lower = problem.title.lower()
        description_lower = problem.description.lower()
        
        if any(word in title_lower for word in ['array', 'subarray', 'sum']):
            return 'array'
        elif any(word in title_lower for word in ['string', 'substring', 'palindrome']):
            return 'string'
        elif any(word in title_lower for word in ['tree', 'binary']):
            return 'tree'
        elif any(word in title_lower for word in ['graph', 'node', 'path']):
            return 'graph'
        elif any(word in description_lower for word in ['dynamic', 'optimal', 'minimum', 'maximum']):
            return 'dp'
        elif any(word in title_lower for word in ['two', 'pointer', 'sorted']):
            return 'two-pointer'
        else:
            return 'general'
#!/usr/bin/env python3
"""
Main entry point for running the LangGraph client examples.

This script provides a convenient way to run the LangGraph client from the project root.
"""

import sys
import os
import asyncio

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from examples.example_langgraph_usage import interactive_mode, quick_examples, compare_react_vs_stategraph

def main():
    print("🚀 LangGraph + MCP Integration Examples")
    print("Choose what to run:")
    print("1. Quick Examples")
    print("2. Interactive Mode") 
    print("3. Compare ReAct vs StateGraph")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(quick_examples())
    elif choice == "2":
        asyncio.run(interactive_mode())
    elif choice == "3":
        asyncio.run(compare_react_vs_stategraph())
    else:
        print("Invalid choice. Running quick examples...")
        asyncio.run(quick_examples())

if __name__ == "__main__":
    main()

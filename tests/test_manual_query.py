#!/usr/bin/env python3
"""Manual test script to verify query functionality with real OmniFocus.

Usage:
    python3 tests/test_manual_query.py

This will:
1. Connect to your REAL OmniFocus
2. Get all incomplete tasks
3. Filter by query "mortgage" (or whatever you specify)
4. Show results

SAFE: This only reads data, no writes.
"""

from omnifocus_mcp.omnifocus_client import OmniFocusClient

def test_query_search():
    """Test searching tasks by query."""
    print("=" * 60)
    print("Manual Query Test")
    print("=" * 60)

    # Create client (will connect to your real OmniFocus)
    client = OmniFocusClient(enable_safety_checks=False)  # Safe - read-only

    print("\n1. Getting ALL incomplete tasks...")
    try:
        all_tasks = client.get_tasks(include_completed=False)
        print(f"   ✓ Found {len(all_tasks)} incomplete tasks")

        # Show first 5 task names for verification
        print("\n   First 5 tasks:")
        for task in all_tasks[:5]:
            print(f"     - {task['name']}")
            if task.get('note'):
                note_preview = task['note'][:50] + "..." if len(task['note']) > 50 else task['note']
                print(f"       Note: {note_preview}")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return

    print("\n2. Searching for 'mortgage' in task names/notes...")
    try:
        mortgage_tasks = client.get_tasks(query="mortgage", include_completed=False)
        print(f"   ✓ Found {len(mortgage_tasks)} tasks matching 'mortgage'")

        if mortgage_tasks:
            print("\n   Matching tasks:")
            for task in mortgage_tasks:
                print(f"     - {task['name']}")
                if 'mortgage' in task.get('note', '').lower():
                    print(f"       (matched in note)")
                if task.get('projectName'):
                    print(f"       Project: {task['projectName']}")
        else:
            print("\n   No tasks found with 'mortgage' in name or note.")
            print("   Try searching for a different term:")

            # Suggest search terms from existing tasks
            all_words = set()
            for task in all_tasks[:20]:
                words = task['name'].lower().split()
                all_words.update(words[:3])  # First 3 words from each task

            print(f"   Common words in your tasks: {', '.join(sorted(list(all_words))[:10])}")

    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n3. Testing inbox_only parameter...")
    try:
        inbox_tasks = client.get_tasks(inbox_only=True, include_completed=False)
        print(f"   ✓ Found {len(inbox_tasks)} incomplete inbox tasks")

        if inbox_tasks:
            print("\n   First 3 inbox tasks:")
            for task in inbox_tasks[:3]:
                print(f"     - {task['name']}")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_query_search()

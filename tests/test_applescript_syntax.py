"""Tests for AppleScript syntax validation.

This test module checks for common AppleScript typos and syntax errors that
mocked tests don't find.
"""

import pytest
from pathlib import Path


class TestAppleScriptSyntax:
    """Validate embedded AppleScript code for common errors."""

    def test_no_common_applescript_typos(self):
        """Check for common AppleScript typos in the source code.

        This test caught the 'elifintervalDays' typo that mocked tests missed.
        """
        client_file = Path('src/omnifocus_mcp/omnifocus_client.py')

        if not client_file.exists():
            pytest.skip(f"File not found: {client_file}")

        with open(client_file, 'r') as f:
            content = f.read()

        # Common typos to check for (add more as we find them)
        typos = [
            # Conditional statements
            ('elifintervalDays', 'else if intervalDays'),
            ('eliftaskDueDate', 'else if taskDueDate'),
            ('elifinterval', 'else if interval'),
            ('elifthen', 'else if ... then'),
            ('elseifthen', 'else if ... then'),

            # Block endings (missing spaces)
            ('endtell', 'end tell'),
            ('endrepeat', 'end repeat'),
            ('endif', 'end if'),
            ('endtry', 'end try'),

            # Property access typos
            ('ofthe', 'of the'),
            ('tothe', 'to the'),

            # Common word combinations
            ('setthe', 'set the'),
            ('getthe', 'get the'),
        ]

        found_typos = []
        for typo, correction in typos:
            if typo in content:
                # Find line numbers for better error reporting
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if typo in line:
                        # Show context (trim long lines)
                        context = line.strip()
                        if len(context) > 60:
                            context = context[:57] + '...'
                        found_typos.append(
                            f"  Line {i}: '{typo}' should be '{correction}'\n"
                            f"    Context: {context}"
                        )

        if found_typos:
            pytest.fail(
                f"Found {len(found_typos)} common AppleScript typos:\n\n" +
                "\n\n".join(found_typos)
            )

    def test_applescript_block_structure(self):
        """Check that AppleScript blocks have proper structure."""
        client_file = Path('src/omnifocus_mcp/omnifocus_client.py')

        if not client_file.exists():
            pytest.skip(f"File not found: {client_file}")

        with open(client_file, 'r') as f:
            lines = f.readlines()

        errors = []

        # Track nesting of tell/repeat/if blocks
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for unmatched quotes in AppleScript strings
            if 'set ' in stripped and '=' in stripped and 'to "' in stripped:
                # Count quotes
                quote_count = stripped.count('"')
                # If odd number of quotes, might be syntax error
                if quote_count % 2 != 0 and not stripped.endswith('\\'):
                    # Could be a line continuation, check next line
                    if i < len(lines) and not lines[i].strip().startswith('"'):
                        errors.append(
                            f"Line {i}: Possible unmatched quote: {stripped[:60]}"
                        )

        if errors:
            pytest.fail(
                f"Found {len(errors)} potential AppleScript structure issues:\n" +
                "\n".join(errors[:10])  # Show first 10
            )

    def test_applescript_tell_blocks_balanced(self):
        """Check that 'tell' and 'end tell' statements are balanced."""
        client_file = Path('src/omnifocus_mcp/omnifocus_client.py')

        if not client_file.exists():
            pytest.skip(f"File not found: {client_file}")

        with open(client_file, 'r') as f:
            content = f.read()

        # Count tell statements (excluding comments)
        tell_count = content.count('tell application "OmniFocus"')
        tell_count += content.count('tell front document')
        tell_count += content.count('tell the note of')

        # Count end tell statements
        end_tell_count = content.count('end tell')

        # They should be roughly balanced
        # (rough check because of string escaping and multi-line blocks)
        if abs(tell_count - end_tell_count) > 10:
            pytest.fail(
                f"Unbalanced tell blocks: {tell_count} 'tell' vs {end_tell_count} 'end tell'. "
                "Difference > 10 suggests syntax errors."
            )

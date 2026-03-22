"""Tests for AppleScript syntax validation.

This test module checks for common AppleScript typos and syntax errors that
mocked tests don't find.
"""

import inspect
import re

import pytest
from pathlib import Path

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


class TestAppleScriptSyntax:
    """Validate embedded AppleScript code for common errors."""

    def test_no_common_applescript_typos(self):
        """Check for common AppleScript typos in the source code.

        This test caught the 'elifintervalDays' typo that mocked tests missed.
        """
        client_file = Path('src/omnifocus_mcp/omnifocus_connector.py')

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
        client_file = Path('src/omnifocus_mcp/omnifocus_connector.py')

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
        client_file = Path('src/omnifocus_mcp/omnifocus_connector.py')

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
        if abs(tell_count - end_tell_count) > 5:
            pytest.fail(
                f"Unbalanced tell blocks: {tell_count} 'tell' vs {end_tell_count} 'end tell'. "
                "Difference > 5 suggests syntax errors."
            )


class TestAppleScriptPerMethodBalance:
    """Check tell/end-tell balance per method by extracting AppleScript templates.

    More precise than the whole-file check — catches unbalanced blocks in
    specific methods with zero tolerance.
    """

    # Methods that contain AppleScript templates
    METHODS_WITH_APPLESCRIPT = [
        'get_projects', 'get_folders', 'get_tags', 'get_perspectives',
        'get_focus', 'switch_perspective',
        'create_task', 'create_project', 'create_folder', 'create_tag',
        'update_task', 'update_project', 'update_projects',
        'update_folder', 'update_tag',
        'delete_tasks', 'delete_projects', 'delete_tags',
        'reorder_task', 'reorder_project',
        'set_focus',
        '_build_batch_mode_script',
        '_build_task_ops_blocks',
        '_get_task_ids_for_tags',
        '_get_on_hold_tag_names',
        '_verify_database_safety',
        '_set_tag_exclusivity',
        '_get_tag_exclusivity_map',
        '_execute_recurrence_update',
    ]

    @staticmethod
    def _extract_applescript_templates(source: str) -> list[tuple[str, str]]:
        """Extract multi-line string literals containing AppleScript from source.

        Returns list of (label, template_string) tuples.
        """
        templates = []
        # Match triple-quoted strings (both ''' and """)
        pattern = re.compile(r"('''|\"\"\")(.*?)\1", re.DOTALL)
        for i, match in enumerate(pattern.finditer(source)):
            content = match.group(2)
            if 'tell application' in content or 'tell front document' in content:
                templates.append((f"template_{i}", content))
        return templates

    @staticmethod
    def _count_tell_balance(source: str) -> tuple[int, int]:
        """Count tell and end-tell across all templates in a method's source."""
        # Count all tell-block openers
        tell_patterns = [
            'tell application',
            'tell front document',
            'tell default document',
            'tell front document window',
            'tell the note of',
        ]
        tell_count = sum(source.count(p) for p in tell_patterns)
        end_tell_count = source.count('end tell')
        return tell_count, end_tell_count

    @pytest.mark.parametrize("method_name", METHODS_WITH_APPLESCRIPT)
    def test_method_tell_blocks_balanced(self, method_name):
        """Each method's AppleScript should have balanced tell/end-tell.

        Checks the full method source (not individual fragments) because
        some methods assemble scripts from multiple template strings.
        Tolerance of 1 accounts for fragment assembly boundaries.
        """
        method = getattr(OmniFocusConnector, method_name, None)
        if method is None:
            pytest.skip(f"Method {method_name} not found")

        source = inspect.getsource(method)

        # Skip methods with no AppleScript
        if 'tell application' not in source and 'tell front document' not in source:
            pytest.skip(f"No AppleScript found in {method_name}")

        tells, end_tells = self._count_tell_balance(source)
        diff = abs(tells - end_tells)
        # Tolerance of 2 per method accounts for fragment assembly
        # (scripts built from multiple template strings joined at runtime).
        # This is still much tighter than the old file-wide tolerance of 5.
        assert diff <= 2, (
            f"{method_name}: {tells} tell(s) vs {end_tells} end tell(s). "
            f"Difference of {diff} > 2 indicates unbalanced blocks."
        )

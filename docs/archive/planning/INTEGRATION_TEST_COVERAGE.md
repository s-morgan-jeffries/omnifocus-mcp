# Integration Test Coverage Analysis

## Currently Tested (14 tests)

### Read Operations ✅
- `get_projects()` - Basic fetch
- `get_projects(query=...)` - Search with query parameter
- `get_tasks()` - Basic fetch
- `get_tasks(query=...)` - Search with query parameter
- `get_tasks(inbox_only=True)` - Inbox filtering
- `get_tags()` - Fetch tags

### Write Operations ✅
- `add_task()` - Basic task creation
- `add_task()` - With all properties (due_date, flagged, tags)
- `create_inbox_task()` - Inbox task creation
- `complete_task()` - Mark task complete
- `update_task()` - Update task properties
- `add_tag_to_task()` - Tag assignment

### Safety/Verification ✅
- Database name verification in test mode
- Production database protection

---

## Missing Integration Tests (22 operations)

### Project Operations (4 missing)
- ❌ `create_project()` - Create new projects
- ❌ `set_project_status()` - Change project status (active/on_hold/done)
- ❌ `get_stalled_projects()` - Find inactive projects
- ❌ `delete_project()` - Delete projects

### Task Operations (7 missing)
- ❌ `get_project()` - Get single project by ID
- ❌ `get_task()` - Get single task by ID
- ❌ `get_subtasks()` - Get task children
- ❌ `delete_task()` - Delete single task
- ❌ `move_task()` - Move task to different project
- ❌ `drop_task()` - Mark task as dropped
- ❌ `set_parent_task()` - Create task hierarchy

### Batch Operations (6 missing)
- ❌ `complete_tasks()` - Complete multiple tasks
- ❌ `delete_tasks()` - Delete multiple tasks
- ❌ `delete_projects()` - Delete multiple projects
- ❌ `move_tasks()` - Move multiple tasks
- ❌ `drop_tasks()` - Drop multiple tasks
- ❌ `add_tag_to_tasks()` - Tag multiple tasks
- ❌ `remove_tag_from_tasks()` - Remove tag from multiple tasks

### Folder Operations (2 missing)
- ❌ `get_folders()` - List all folders
- ❌ `create_folder()` - Create folder hierarchy

### Review/Metadata Operations (3 missing)
- ❌ `set_review_interval()` - Set project review schedule
- ❌ `mark_project_reviewed()` - Mark project as reviewed
- ❌ `get_projects_due_for_review()` - Find projects needing review
- ❌ `set_estimated_minutes()` - Set task time estimates

### Advanced Operations (2 missing)
- ❌ `get_perspectives()` - List custom perspectives
- ❌ `switch_perspective()` - Change active perspective

### Note Operations (2 missing)
- ❌ `add_note()` - Add note to project/task
- ❌ `get_note()` - Retrieve note content

---

## Recommended Test Additions

### High Priority (Core CRUD)
1. **Project CRUD** - create_project, delete_project, set_project_status
2. **Task Management** - get_task, get_subtasks, delete_task, move_task, drop_task
3. **Batch Operations** - complete_tasks, delete_tasks (common operations)

### Medium Priority (Organization)
4. **Folders** - get_folders, create_folder
5. **Task Hierarchy** - set_parent_task, get_subtasks
6. **Notes** - add_note, get_note

### Lower Priority (Advanced Features)
7. **Review System** - set_review_interval, mark_project_reviewed, get_projects_due_for_review
8. **Time Estimation** - set_estimated_minutes
9. **Perspectives** - get_perspectives, switch_perspective (UI-focused)
10. **Batch Tag Operations** - add_tag_to_tasks, remove_tag_from_tasks

---

## Complex Scenarios Not Yet Tested

### Recurring Tasks
- ✅ Complete recurring task (tested manually, should add to suite)
- ❌ Create recurring task
- ❌ Verify next occurrence spawns correctly
- ❌ Update recurring task recurrence pattern

### Date Filtering
- ❌ `get_tasks(due_relative="this_week")`
- ❌ `get_tasks(due_relative="today")`
- ❌ `get_tasks(overdue=True)`
- ❌ `get_tasks(defer_relative="this_week")`

### Advanced Filtering
- ❌ `get_tasks(flagged_only=True)`
- ❌ `get_tasks(available_only=True)`
- ❌ `get_tasks(blocked_only=True)`
- ❌ `get_tasks(next_only=True)`
- ❌ `get_tasks(dropped_only=True)`
- ❌ `get_tasks(tag_filter=["tag1", "tag2"])`
- ❌ `get_tasks(has_estimate=True)`
- ❌ `get_tasks(max_estimated_minutes=60)`

### Sorting
- ❌ `get_tasks(sort_by="due_date", sort_order="asc")`
- ❌ `get_projects(sort_by="name", sort_order="desc")`

### Error Conditions
- ❌ Invalid project ID
- ❌ Invalid task ID
- ❌ Invalid tag name
- ❌ Invalid date format
- ❌ Invalid recurrence pattern
- ❌ Circular task parent relationships

---

## Test Coverage Statistics

- **Current Coverage**: 14 tests covering ~17% of functionality
- **Core Operations**: 50% covered (6 of 12 CRUD operations)
- **Advanced Features**: 0% covered (0 of 15 operations)
- **Batch Operations**: 0% covered (0 of 7 operations)

## Estimated Work to Achieve 80% Coverage

- **High Priority Tests**: ~15-20 tests (core CRUD + batch operations)
- **Medium Priority Tests**: ~10-15 tests (organization features)
- **Advanced Filtering Tests**: ~10-15 tests (date filters, flags, tags)
- **Error Condition Tests**: ~5-10 tests (edge cases, validation)

**Total**: ~40-60 additional tests for comprehensive coverage

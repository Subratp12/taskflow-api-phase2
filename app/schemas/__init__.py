"""TaskFlow API — Schemas Package."""

from .comment_schema import (
    CommentCreateSchema,
    CommentResponseSchema,
    CommentUpdateSchema,
    ActivityLogResponseSchema,
    comment_create_schema,
    comment_response_schema,
    comment_update_schema,
    comments_response_schema,
    activity_log_response_schema,
    activity_logs_response_schema,
)
from .project_schema import (
    AddMemberSchema,
    ProjectCreateSchema,
    ProjectResponseSchema,
    ProjectUpdateSchema,
    add_member_schema,
    project_create_schema,
    project_member_response_schema,
    project_members_response_schema,
    project_response_schema,
    project_update_schema,
    projects_list_schema,
)
from .task_schema import (
    TaskAssignPatchSchema,
    TaskCreateSchema,
    TaskResponseSchema,
    TaskStatusPatchSchema,
    TaskUpdateSchema,
    task_assign_patch_schema,
    task_create_schema,
    task_filter_schema,
    task_response_schema,
    task_status_patch_schema,
    task_update_schema,
    tasks_list_schema,
)
from .user_schema import (
    UserLoginSchema,
    UserRegistrationSchema,
    UserResponseSchema,
    UserUpdateSchema,
    user_login_schema,
    user_public_schema,
    user_registration_schema,
    user_response_schema,
    user_update_schema,
    users_response_schema,
)

__all__ = [
    # User
    'UserRegistrationSchema', 'UserLoginSchema', 'UserUpdateSchema', 'UserResponseSchema',
    'user_registration_schema', 'user_login_schema', 'user_update_schema',
    'user_response_schema', 'users_response_schema', 'user_public_schema',
    # Project
    'ProjectCreateSchema', 'ProjectUpdateSchema', 'ProjectResponseSchema', 'AddMemberSchema',
    'project_create_schema', 'project_update_schema', 'project_response_schema',
    'project_update_schema', 'add_member_schema', 'projects_list_schema',
    'project_member_response_schema', 'project_members_response_schema',
    # Task
    'TaskCreateSchema', 'TaskUpdateSchema', 'TaskStatusPatchSchema',
    'TaskAssignPatchSchema', 'TaskResponseSchema',
    'task_create_schema', 'task_update_schema', 'task_status_patch_schema',
    'task_assign_patch_schema', 'task_response_schema', 'tasks_list_schema',
    'task_filter_schema',
    # Comment & Activity
    'CommentCreateSchema', 'CommentUpdateSchema', 'CommentResponseSchema',
    'ActivityLogResponseSchema',
    'comment_create_schema', 'comment_update_schema', 'comment_response_schema',
    'comments_response_schema', 'activity_log_response_schema', 'activity_logs_response_schema',
]

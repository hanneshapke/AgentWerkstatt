# from typing import Any

# from ..tools.base import BaseTool
# from ..tools.schemas import ToolSchema, InputSchema, InputProperty


# class DelegateTool(BaseTool):
#     """A tool to delegate a task to another agent persona."""

#     def __init__(self):
#         super().__init__()
#         self.agent = None  # This will be injected by the ToolExecutor

#     def get_name(self) -> str:
#         return "delegate_task"

#     def get_description(self) -> str:
#         return (
#             "Delegates a task to a specified agent persona. Use this to leverage the "
#             "expertise of other agents to accomplish your goal."
#         )

#     def get_schema(self) -> ToolSchema:
#         return ToolSchema(
#             name=self.get_name(),
#             description=self.get_description(),
#             input_schema=InputSchema(
#                 properties={
#                     "persona_name": InputProperty(
#                         type="string",
#                         description=(
#                             "The name of the persona to delegate the task to (e.g., "
#                             "'researcher', 'coder')."
#                         ),
#                     ),
#                     "task_description": InputProperty(
#                         type="string",
#                         description="A clear and detailed description of the task for the other agent.",
#                     ),
#                 },
#                 required=["persona_name", "task_description"],
#             ),
#         )

#     def execute(self, persona_name: str, task_description: str) -> dict[str, Any]:
#         """Switches persona, executes the task, and switches back."""
#         if not self.agent:
#             return {"status": "error", "error": "Agent instance not available for delegation."}

#         original_persona = self.agent.active_persona_name
#         try:
#             self.agent.switch_persona(persona_name)
#             # We can reuse the session_id from the agent
#             result = self.agent.process_request(task_description, session_id=self.agent.session_id)
#             return {
#                 "status": "success",
#                 "persona": persona_name,
#                 "output": result,
#             }
#         except ValueError as e:
#             return {"status": "error", "error": f"Invalid persona: {str(e)}"}
#         except Exception as e:
#             return {"status": "error", "error": f"An unexpected error occurred: {str(e)}"}
#         finally:
#             if original_persona:
#                 self.agent.switch_persona(original_persona)

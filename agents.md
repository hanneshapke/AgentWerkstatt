# Supporting Multiple Agent Personas

The current agent framework is designed with a single agent persona in mind, loaded from a configuration file at startup. This document outlines the necessary changes to extend the framework to support multiple, switchable agent personas. This will enable more complex and dynamic interactions, where different specialized agents can collaborate to solve a problem.

## 1. Rationale for Change

Supporting multiple agent personas offers several advantages:

*   **Specialization**: Different agents can be experts in specific domains (e.g., a "researcher" agent for gathering information, a "writer" agent for composing text, a "coder" agent for generating code).
*   **Improved Performance**: By breaking down complex tasks and assigning them to specialized agents, the overall quality and efficiency of the system can be improved.
*   **Flexibility**: The ability to switch between personas allows the system to adapt to the user's needs and the context of the conversation.
*   **Scalability**: A multi-agent architecture is more scalable and maintainable in the long run, as new capabilities can be added by creating new agents without modifying the existing ones.

## 2. Proposed Changes

To support multiple agent personas, we need to introduce the following changes:

### 2.1. Persona Management

Instead of a single `persona` field in the `config.yaml`, we will introduce a `personas` section. This section will contain a dictionary of named personas, where each persona has its own definition file.

**Current `config.yaml`:**

```yaml
persona: agents.md
```

**Proposed `config.yaml`:**

```yaml
personas:
  default: agents.md
  researcher: personas/researcher.md
  writer: personas/writer.md
  coder: personas/coder.md
```

This change requires modifying the `AgentConfig` class in `config.py` to load and manage a dictionary of personas instead of a single string. The `default` persona will be used unless another one is specified.

### 2.2. Agent Initialization

The `Agent` class in `agent.py` will need to be updated to handle multiple personas. The agent will be initialized with a default persona, but it should be possible to switch to another persona dynamically.

The `Agent` class could be modified to have a `switch_persona(persona_name)` method. This method would update the agent's internal state, including the persona used by the LLM.

### 2.3. Hand-over Between Agents

The core of the multi-agent system is the ability for agents to hand over control to one another. We can achieve this by introducing a special tool or mechanism that allows an agent to delegate a task to another agent.

We can introduce a `delegate` tool that all agents have access to. This tool would take two arguments:

*   `persona_name`: The name of the persona to delegate the task to.
*   `task_description`: A description of the task to be performed.

When an agent uses the `delegate` tool, the framework will:

1.  Save the current conversation context.
2.  Switch to the specified persona.
3.  Execute the task using the new persona.
4.  Return the result to the original agent.

The `ToolExecutor` in `services/tool_executor.py` would need to be aware of this special `delegate` tool and handle the persona switching logic.

### 2.4. Conversation Flow

The `ConversationHandler` in `services/conversation_handler.py` will need to be updated to manage conversations that involve multiple personas. The conversation history should clearly indicate which persona was active at each step.

This could be achieved by adding a `persona` field to each message in the conversation history.

## 3. Example Workflow

Here's an example of how a multi-agent conversation could work:

1.  **User**: "Research the latest advancements in AI and then write a blog post about it."
2.  **Default Agent (using `agents.md`)**: "I can do that. I will start by researching the topic."
3.  **Default Agent (internally)**: Uses the `delegate` tool to hand over the research task to the `researcher` agent.
    *   `delegate(persona_name="researcher", task_description="Research the latest advancements in AI.")`
4.  **Researcher Agent (using `personas/researcher.md`)**: Performs the research using its specialized tools (e.g., web search).
5.  **Researcher Agent**: Returns the research findings to the default agent.
6.  **Default Agent**: Receives the research findings.
7.  **Default Agent (internally)**: Uses the `delegate` tool to hand over the writing task to the `writer` agent.
    *   `delegate(persona_name="writer", task_description="Write a blog post based on the following research: [research findings]")`
8.  **Writer Agent (using `personas/writer.md`)**: Writes the blog post.
9.  **Writer Agent**: Returns the blog post to the default agent.
10. **Default Agent**: Presents the final blog post to the user.

## 4. Implementation Steps

1.  **Update `config.py`**: Modify `AgentConfig` to support the `personas` dictionary.
2.  **Create `delegate` tool**: Implement the `delegate` tool and integrate it with the `ToolExecutor`.
3.  **Update `agent.py`**: Add the `switch_persona` method to the `Agent` class.
4.  **Update `conversation_handler.py`**: Enhance the conversation history to include persona information.
5.  **Create new persona files**: Create the `personas/researcher.md`, `personas/writer.md`, and `personas/coder.md` files with appropriate content.
6.  **Update documentation**: Update the project documentation to reflect the new multi-agent capabilities.
7.  **Add tests**: Create new unit and integration tests to cover the multi-agent functionality.

By following these steps, we can transform the agent framework from a single-persona system to a powerful multi-agent platform.
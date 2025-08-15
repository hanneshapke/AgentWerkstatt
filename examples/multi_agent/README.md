# Multi-Agent Example

This directory contains a self-contained example of the multi-agent capabilities of the AgentWerkstatt framework.

## Files

-   `config.yaml`: The configuration file that defines two personas:
    -   `planner`: The default agent that receives the request, plans the steps, and delegates tasks.
    -   `joke_writer`: A specialist agent whose only job is to write jokes.
-   `personas/`: This directory contains the markdown files for the personas.
-   `../../tools`: The `tools_dir` is configured to point to the project's root `tools` directory to ensure it can find the `delegate.py` tool.

## How to Run

1.  **Navigate to the project root directory.**

2.  **Run the CLI with the example's configuration:**

    ```bash
    python -m agentwerkstatt.cli --config examples/multi_agent/config.yaml
    ```

3.  **Give the agent a request that requires delegation.** For example:

    > "Tell me a joke about cats."

## Expected Flow

1.  The `planner` agent will receive your request.
2.  It will determine that writing a joke is a specialist task.
3.  It will use the `delegate_task` tool to pass the request "write a joke about cats" to the `joke_writer` persona.
4.  The `joke_writer` will execute the task and return a joke.
5.  The `planner` will receive the result and present it to you.

You will see the persona switching in the CLI output, indicated by `[planner]` and `[joke_writer]` prefixes.

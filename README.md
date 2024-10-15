# AI Agent State Library

# AI Agent State Library

## What is it?

The AI Agent State Library is a sophisticated software toolkit designed to manage the complex behavior and decision-making processes of artificial intelligence agents. At its core, it implements the concept of finite state machines, a computational model used to design systems with a finite number of states and transitions between those states.

Key features of the library include:

1. **State Machine Creation**: It allows developers to define and create intricate state machines that model the behavior of AI agents.

2. **Flexible State Definition**: States can be customized with associated data and metadata, allowing for rich context within each state.

3. **Dynamic Transitions**: The library supports the creation of transitions between states, which can be conditional and trigger specific actions.

4. **Persistence**: Integration with ChromaDB enables efficient storage and retrieval of state machines, allowing for continuity across sessions or distributed systems.

5. **Visualization**: The library includes tools to visualize state machines, aiding in debugging and understanding complex agent behaviors.

6. **OpenAI Integration**: It leverages the OpenAI API for dynamic decision-making, allowing for more intelligent and adaptive state transitions.

## When is it useful?

The AI Agent State Library proves particularly valuable in scenarios such as:

- **Conversational AI**: Managing the flow and context of conversations, ensuring coherent and contextually appropriate responses.

- **Business Process Automation**: Modeling and executing complex workflows that involve decision points and varied paths based on different conditions.

- **Multi-Agent Systems**: Coordinating the behavior and interactions of multiple AI agents in a complex environment.

The library's flexibility and extensibility make it adaptable to a wide range of AI applications where managing complex state and behavior is crucial. Its integration with modern tools like ChromaDB for persistence and OpenAI for decision-making enhances its utility in creating sophisticated, adaptive AI systems.

By providing a structured way to design, implement, and manage AI agent behavior, the AI Agent State Library helps developers create more reliable, understandable, and maintainable AI systems, reducing the complexity often associated with developing intelligent agents.

## Features

- Create and manage complex state machines for AI agents
- Define custom states with associated data and metadata
- Create transitions between states with optional conditions and actions
- Persist and retrieve state machines using ChromaDB
- Visualize state machines for easy understanding and debugging
- Integration with OpenAI's API for dynamic decision-making

## Installation

To install the AI Agent State Library, use pip:

```bash
pip install ai-agent-state
```

Make sure you have the following dependencies installed:

- Python 3.7+
- ChromaDB
- OpenAI
- python-dotenv
- graphviz (optional, for visualization)

## Quick Start

Here's a simple example to get you started with the AI Agent State Library:

```python
import uuid
from ai_agent_state import State, StateData, StateMachine, Transition, ChromaStateManager

# Define states
states = [
    State(id=str(uuid.uuid4()), name='initialize', data=StateData(data={'message': 'Initializing AI agent...'})),
    State(id=str(uuid.uuid4()), name='process', data=StateData(data={'message': 'Processing task...'})),
    State(id=str(uuid.uuid4()), name='idle', data=StateData(data={'message': 'Waiting for next task...'})),
]

# Create the state machine
state_machine = StateMachine(name='SimpleAIAgent', initial_state=states[0])

# Add states to the state machine
for state in states:
    state_machine.add_state(state)

# Add transitions
state_machine.add_transition(Transition(from_state='initialize', to_state='process'))
state_machine.add_transition(Transition(from_state='process', to_state='idle'))
state_machine.add_transition(Transition(from_state='idle', to_state='process'))

# Use the state machine
state_machine.trigger_transition("Start processing")
print(f"Current State: {state_machine.current_state.name}")
state_machine.trigger_transition("Finish processing")
print(f"Current State: {state_machine.current_state.name}")

# Save the state machine
chroma_manager = ChromaStateManager(persist_directory="chroma_db")
chroma_manager.save_state_machine(state_machine)
```

## Documentation

For detailed documentation on classes and methods, please refer to the [full documentation](link-to-your-documentation).

## Advanced Usage

The AI Agent State Library supports advanced features such as:

- Custom transition conditions and actions
- Integration with language models for dynamic decision-making
- Searching for similar states using vector embeddings
- Visualizing complex state machines

For examples of advanced usage, check out the [examples directory](link-to-examples-directory) in the repository.

## Contributing

We welcome contributions to the AI Agent State Library! Please read our [contributing guidelines](link-to-contributing-guidelines) for more information on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](link-to-license-file) file for details.



## Classes

### StateData
Represents the data and metadata associated with a state.

#### Methods:
- `to_dict()`: Converts the StateData to a dictionary.
- `from_dict(data)`: Creates a StateData object from a dictionary.
- `update_metadata(llm_response, **kwargs)`: Updates the metadata with new information.

### State
Represents a single state in the state machine.

#### Attributes:
- `id`: Unique identifier for the state.
- `name`: Name of the state.
- `data`: StateData object containing the state's data and metadata.

#### Methods:
- `to_dict()`: Converts the State to a dictionary.
- `from_dict(data)`: Creates a State object from a dictionary.

### Transition
Represents a transition between states.

#### Attributes:
- `from_state`: Name of the source state.
- `to_state`: Name of the destination state.
- `condition`: Optional function to determine if the transition should occur.
- `action`: Optional function to execute during the transition.

### StateMachine
Manages the states and transitions of an AI agent.

#### Methods:
- `add_state(state)`: Adds a new state to the machine.
- `add_transition(transition)`: Adds a new transition to the machine.
- `trigger_transition(user_input)`: Processes user input and determines the next state.
- `move_to_previous_state()`: Moves the state machine to the previous state.
- `visualize(filename)`: Generates a visual representation of the state machine.

### ChromaStateManager
Manages the persistence and retrieval of state machines using ChromaDB.

#### Methods:
- `save_state_machine(state_machine)`: Saves a state machine to the database.
- `load_state_machine(state_machine_id)`: Loads a state machine from the database.
- `search_similar_states(query, top_k)`: Searches for similar states based on a query.

## Example Use Case

Here's an example of how to use this library to create an AI agent that manages tasks:

```python
import uuid
from ai_agent_state import State, StateData, StateMachine, Transition, ChromaStateManager

# Define states
states = [
    State(id=str(uuid.uuid4()), name='initialize', data=StateData(data={'message': 'Initializing AI agent...'})),
    State(id=str(uuid.uuid4()), name='select_task', data=StateData(data={'message': 'Selecting next task...'})),
    State(id=str(uuid.uuid4()), name='execute_task', data=StateData(data={'message': 'Executing task...'})),
    State(id=str(uuid.uuid4()), name='review_outcome', data=StateData(data={'message': 'Reviewing task outcome...'})),
    State(id=str(uuid.uuid4()), name='idle', data=StateData(data={'message': 'All tasks complete. Waiting for new tasks...'})),
]

# Create the state machine
state_machine = StateMachine(name='AITaskManager', initial_state=states[0])

# Add states to the state machine
for state in states:
    state_machine.add_state(state)

# Add transitions
state_machine.add_transition(Transition(from_state='initialize', to_state='select_task'))
state_machine.add_transition(Transition(from_state='select_task', to_state='execute_task'))
state_machine.add_transition(Transition(from_state='execute_task', to_state='review_outcome'))
state_machine.add_transition(Transition(from_state='review_outcome', to_state='select_task'))
state_machine.add_transition(Transition(from_state='review_outcome', to_state='idle'))

# Save the state machine to ChromaDB
chroma_manager = ChromaStateManager(persist_directory="chroma_db")
chroma_manager.save_state_machine(state_machine)

# Simulate AI agent operations
tasks = ["Analyze data", "Generate report", "Optimize algorithm"]

for task in tasks:
    state_machine.trigger_transition(f"New task: {task}")
    while state_machine.current_state.name != 'idle':
        print(f"Current State: {state_machine.current_state.name}")
        print(f"Action: {state_machine.current_state.data.data['message']}")
        state_machine.trigger_transition("Continue")

print("All tasks completed. AI agent is idle.")

# Visualize the state machine
state_machine.visualize("ai_task_manager")
```

This example creates a simple AI agent that can manage tasks using the state machine. It demonstrates how to define states, add transitions, persist the state machine, and simulate its operation.

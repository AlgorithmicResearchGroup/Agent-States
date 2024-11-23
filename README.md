# AI Agent State Library


## What is it?

The AI Agent State Library is a library designed to manage the state and decision-making processes of AI agents. At its core, it implements the concept of finite state machines, a computational model used to design systems with a finite number of states and transitions between those states.

Key features of the library include:

1. **State Machine Creation**: It allows developers to define and create intricate state machines that model the behavior of AI agents.

2. **Flexible State Definition**: States can be customized with associated data and metadata, allowing for rich context within each state.

3. **Dynamic Transitions**: The library supports the creation of transitions between states, which can be conditional and trigger specific actions.

4. **State Transition Guards**: Implement conditions that must be met for transitions to occur, providing more control over state changes.

5. **Persistence**: Integration with ChromaDB enables efficient storage and retrieval of state machines, allowing for continuity across sessions or distributed systems.

6. **Visualization**: The library includes tools to visualize state machines, aiding in debugging and understanding complex agent behaviors.

7. **OpenAI Integration**: It leverages the OpenAI API for dynamic decision-making, allowing for more intelligent and adaptive state transitions.

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
- Implement state transition guards for controlled state changes
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

Here's a simple example to get you started with the AI Agent State Library. This example shows how to create a state machine and specify the OpenAI model to be used:

```python
import uuid
from ai_agent_state import State, StateData, StateMachine, Transition

# Define states
states = [
    State(
        id=str(uuid.uuid4()),
        name='initialize',
        data=StateData(data={'message': 'Initializing AI agent...'})
    ),
    State(
        id=str(uuid.uuid4()),
        name='process',
        data=StateData(data={'message': 'Processing task...'})
    ),
    State(
        id=str(uuid.uuid4()),
        name='idle',
        data=StateData(data={'message': 'Waiting for next task...'})
    ),
]

# Create the state machine and specify the model name
state_machine = StateMachine(
    name='SimpleAIAgent',
    initial_state=states[0],
    model_name='gpt-3.5-turbo'  # Replace with your desired model
)

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

# Save the state machine (optional)
from ai_agent_state import ChromaStateManager
chroma_manager = ChromaStateManager(persist_directory="chroma_db")
chroma_manager.save_state_machine(state_machine)
```

## Documentation

For detailed documentation on classes and methods, please refer to the [full documentation](link-to-your-documentation).

## Advanced Usage

The AI Agent State Library supports advanced features such as:

- Custom transition conditions and actions
- State transition guards for controlled state changes
- Integration with language models for dynamic decision-making
- Searching for similar states using vector embeddings
- Visualizing complex state machines

For examples of advanced usage, check out the [examples directory](/examples) in the repository.

## Example Use Case

Here's an example of how to use this library to create an AI agent that manages customer support interactions. This example includes passing in the model during the state machine creation:

```python
import os
import uuid
from dotenv import load_dotenv
from typing import Any, Dict
import openai
from openai import OpenAI
import os

api_key = os.getenv('OPENAI_API_KEY')

from ai_agent_state.state import (
    Metadata,
    StateData,
    State,
    Transition,
    StateMachine,
)

# Load environment variables (e.g., OpenAI API key)
load_dotenv()

# Factory functions to simplify state and transition creation
def create_state(name: str, data: Dict[str, Any]) -> State:
    return State(
        id=str(uuid.uuid4()),
        name=name,
        data=StateData(data=data)
    )

def create_transition(from_state: str, to_state: str, condition=None) -> Transition:
    return Transition(from_state=from_state, to_state=to_state, condition=condition)

# Define condition functions
def is_order_tracking(user_input: str, state_machine: StateMachine) -> bool:
    return 'track' in user_input.lower() or 'order' in user_input.lower()

def is_returns_and_refunds(user_input: str, state_machine: StateMachine) -> bool:
    return 'return' in user_input.lower() or 'refund' in user_input.lower()

def is_product_inquiry(user_input: str, state_machine: StateMachine) -> bool:
    return 'product' in user_input.lower() or 'inquiry' in user_input.lower() or 'question' in user_input.lower()

def is_account_management(user_input: str, state_machine: StateMachine) -> bool:
    return 'account' in user_input.lower() or 'profile' in user_input.lower()

def has_order_number(user_input: str, state_machine: StateMachine) -> bool:
    return any(char.isdigit() for char in user_input)

def is_exit_command(user_input: str, state_machine: StateMachine) -> bool:
    return user_input.lower() in ['exit', 'quit', 'goodbye']

# Define states
welcome_state = create_state('Welcome', {
    'message': 'Welcome to E-Shop! How can I assist you today?'
})

main_menu_state = create_state('MainMenu', {
    'message': 'Please choose an option: Order Tracking, Returns and Refunds, Product Inquiry, Account Management, or type "exit" to quit.'
})

order_tracking_state = create_state('OrderTracking', {
    'message': 'Sure, I can help with order tracking.'
})

collect_order_number_state = create_state('CollectOrderNumber', {
    'message': 'Please provide your order number.'
})

provide_order_status_state = create_state('ProvideOrderStatus', {
    'task': 'Providing order status...'
})

returns_refunds_state = create_state('ReturnsAndRefunds', {
    'message': 'I can assist you with returns and refunds.'
})

product_inquiry_state = create_state('ProductInquiry', {
    'message': 'I can help answer your product questions.'
})

account_management_state = create_state('AccountManagement', {
    'message': 'I can assist you with managing your account.'
})

goodbye_state = create_state('Goodbye', {
    'message': 'Thank you for visiting E-Shop! Have a great day!'
})

# Create the state machine with a specified model client
# Assume `model_client` is passed or created elsewhere in your application
model_client = openai.OpenAI(api_key=api_key)
state_machine = StateMachine(
    name='CustomerSupportAssistant',
    initial_state=welcome_state,
    model_client=model_client,  # Pass the model client here
    model_name='gpt-4o'  # Optional: specify a model name if needed
)

# Add states to the state machine
state_machine.add_state(main_menu_state)
state_machine.add_state(order_tracking_state)
state_machine.add_state(collect_order_number_state)
state_machine.add_state(provide_order_status_state)
state_machine.add_state(returns_refunds_state)
state_machine.add_state(product_inquiry_state)
state_machine.add_state(account_management_state)
state_machine.add_state(goodbye_state)

# Define transitions with condition functions
transitions = [
    create_transition('Welcome', 'MainMenu'),
    create_transition('MainMenu', 'OrderTracking', condition=is_order_tracking),
    create_transition('OrderTracking', 'CollectOrderNumber'),
    create_transition('CollectOrderNumber', 'ProvideOrderStatus', condition=has_order_number),
    create_transition('ProvideOrderStatus', 'MainMenu'),
    create_transition('MainMenu', 'ReturnsAndRefunds', condition=is_returns_and_refunds),
    create_transition('MainMenu', 'ProductInquiry', condition=is_product_inquiry),
    create_transition('MainMenu', 'AccountManagement', condition=is_account_management),
    create_transition('MainMenu', 'Goodbye', condition=is_exit_command),
    create_transition('ReturnsAndRefunds', 'MainMenu'),
    create_transition('ProductInquiry', 'MainMenu'),
    create_transition('AccountManagement', 'MainMenu'),
]

# Add transitions to the state machine
for transition in transitions:
    state_machine.add_transition(transition)

# Implement action functions
def fetch_order_status(order_number: str) -> str:
    # Simulate fetching order status from a database
    return f"Order {order_number} is currently in transit and will be delivered in 2 days."

def handle_returns_and_refunds():
    return "I've initiated the return process for you. Please check your email for further instructions."

def answer_product_inquiry():
    return "The product you asked about is in stock and available in various sizes."

def assist_account_management():
    return "I've updated your account preferences as requested."

def main():
    print(f"Current State: {state_machine.current_state.name}")
    print(state_machine.current_state.data.data['message'])

    while True:
        user_input = input("You: ")

        if not user_input.strip():
            continue  # Skip empty input

        # Before triggering transition, print current state
        print(f"\n[Before Transition] Current State: {state_machine.current_state.name}")

        # Check if the user wants to exit
        if is_exit_command(user_input, state_machine):
            # Transition to 'Goodbye' state
            state_machine.current_state = goodbye_state
            state_machine.state_history.append(state_machine.current_state.name)
            print(state_machine.current_state.data.data['message'])
            break

        state_machine.trigger_transition(user_input)

        # After triggering transition, print new state
        print(f"[After Transition] Current State: {state_machine.current_state.name}")
        print(f"State History: {' -> '.join(state_machine.state_history)}")

        # Perform any actions associated with the current state
        if state_machine.current_state.name == 'OrderTracking':
            print(state_machine.current_state.data.data['message'])
        elif state_machine.current_state.name == 'CollectOrderNumber':
            print(state_machine.current_state.data.data['message'])
        elif state_machine.current_state.name == 'ProvideOrderStatus':
            # Extract order number from user input or previous input
            order_number = ''.join(filter(str.isdigit, user_input))
            if not order_number:
                # Attempt to retrieve from metadata
                order_number = state_machine.current_state.data.metadata.custom_data.get('order_number', 'Unknown')
            status_message = fetch_order_status(order_number)
            print(f"Action: {status_message}")
        elif state_machine.current_state.name == 'ReturnsAndRefunds':
            result_message = handle_returns_and_refunds()
            print(f"Action: {result_message}")
        elif state_machine.current_state.name == 'ProductInquiry':
            result_message = answer_product_inquiry()
            print(f"Action: {result_message}")
        elif state_machine.current_state.name == 'AccountManagement':
            result_message = assist_account_management()
            print(f"Action: {result_message}")

        # Provide the assistant's response if there is a message
        if 'message' in state_machine.current_state.data.data:
            print(f"Assistant: {state_machine.current_state.data.data['message']}")

    # Optionally, after exiting, print the final state history
    print("\nFinal State History:")
    print(" -> ".join(state_machine.state_history))

if __name__ == '__main__':
    main()
```

**Explanation of the Example:**

- **State Definitions:**
  - We define several states representing different stages of the customer support interaction, such as `Welcome`, `MainMenu`, `OrderTracking`, `ProvideOrderStatus`, etc.

- **State Machine Initialization:**
  - We create a `StateMachine` instance, specifying the initial state and the OpenAI model to use.

- **Adding States and Transitions:**
  - All states and transitions are added to the state machine. Transitions define how the state machine moves from one state to another based on the conversation flow.

- **Action Functions:**
  - Functions like `fetch_order_status`, `handle_returns_and_refunds`, etc., simulate backend operations that would occur in a real-world scenario.

- **Main Conversation Loop:**
  - The `main` function runs an interactive loop where the user can input messages, and the assistant responds accordingly.
  - The assistant uses the OpenAI model specified to process messages and determine state transitions.

- **State Management:**
  - The state machine keeps track of the current state and moves to the next state based on user input and OpenAI's decision-making.
  - Actions associated with each state are performed when the state is active.

**Sample Interaction:**

```plaintext
Current State: Welcome
Welcome to E-Shop! How can I assist you today?
You: I'd like to track my order.

[Before Transition] Current State: Welcome
Assistant Response: Sure, I can help you with order tracking. Please provide your order number.
[After Transition] Current State: CollectOrderNumber
State History: Welcome -> CollectOrderNumber
You: My order number is 123456.

[Before Transition] Current State: CollectOrderNumber
Assistant Response: Thank you! Retrieving the status of your order now.
[After Transition] Current State: ProvideOrderStatus
State History: Welcome -> CollectOrderNumber -> ProvideOrderStatus
Action: Order 123456 is currently in transit and will be delivered in 2 days.
You: Great, thanks!

[Before Transition] Current State: ProvideOrderStatus
Assistant Response: You're welcome! Is there anything else I can assist you with?
[After Transition] Current State: MainMenu
State History: Welcome -> CollectOrderNumber -> ProvideOrderStatus -> MainMenu
You: No, that's all.

[Before Transition] Current State: MainMenu
Assistant Response: Thank you for visiting E-Shop! Have a great day!
[After Transition] Current State: Goodbye
State History: Welcome -> CollectOrderNumber -> ProvideOrderStatus -> MainMenu -> Goodbye

Final State History:
Welcome -> CollectOrderNumber -> ProvideOrderStatus -> MainMenu -> Goodbye
```

**Note:**

- In a real implementation, the assistant's responses and state transitions are determined by the OpenAI model based on your inputs.
- Ensure that you have set the `OPENAI_API_KEY` in your environment variables or appropriately in your code.
- Replace `'gpt-3.5-turbo'` with your desired OpenAI model.
- The action functions simulate backend processes and should be replaced with actual logic in a production environment.

## Contributing

We welcome contributions to the AI Agent State Library! Please read our [contributing guidelines](link-to-contributing-guidelines) for more information on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



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


**Note:**

- In a real implementation, the assistant's responses and state transitions are determined by the OpenAI model based on your inputs.
- Ensure that you have set the `OPENAI_API_KEY` in your environment variables or appropriately in your code.
- Replace `'gpt-3.5-turbo'` with your desired OpenAI model.
- The action functions simulate backend processes and should be replaced with actual logic in a production environment.

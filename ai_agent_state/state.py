import time
import random
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
import uuid
from datetime import datetime
import threading
import os
from dotenv import load_dotenv
# Import for ChromaDB
import chromadb
from chromadb.utils import embedding_functions
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()

@dataclass
class Metadata:
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    llm_response: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    llm_prompt: Optional[str] = None
    llm_response_time: Optional[float] = None
    llm_tokens_used: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        return cls(**data)

@dataclass
class StateData:
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {"data": self.data, "metadata": self.metadata.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateData':
        return cls(data=data["data"], metadata=Metadata.from_dict(data["metadata"]))

    def update_metadata(self, llm_response: Optional[str] = None, **kwargs) -> None:
        self.metadata.updated_at = datetime.now().isoformat()
        if llm_response:
            self.metadata.llm_response = llm_response
        self.metadata.custom_data.update(kwargs)

@dataclass
class State:
    id: str
    name: str
    data: StateData

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "data": self.data.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'State':
        return cls(id=data["id"], name=data["name"], data=StateData.from_dict(data["data"]))

@dataclass
class Transition:
    from_state: str
    to_state: str
    condition: Optional[Callable[[Any, 'StateMachine'], bool]] = None
    action: Optional[Callable[['StateMachine'], None]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "condition": self.condition.__name__ if self.condition else None,
            "action": self.action.__name__ if self.action else None
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        function_registry: Optional[Dict[str, Callable]] = None
    ) -> 'Transition':
        if function_registry is None:
            function_registry = {}
        condition = function_registry.get(data["condition"])
        action = function_registry.get(data["action"])
        return cls(
            from_state=data["from_state"],
            to_state=data["to_state"],
            condition=condition,
            action=action
        )
        
class SetNextState:
    def __init__(self, next_state: str):
        self.next_state = next_state

    @staticmethod
    def model_json_schema():
        return {
            "type": "object",
            "properties": {
                "next_state": {"type": "string", "description": "The name of the next state."}
            },
            "required": ["next_state"]
        }

class StateMachine:
    def __init__(self, name: str, initial_state: State, model_name: Optional[str] = None):
        self.lock = threading.Lock()
        self.id = str(uuid.uuid4())
        self.name = name
        self.current_state = initial_state
        self.states = {initial_state.name: initial_state}
        self.transitions: List[Transition] = []
        self.children: Dict[str, 'StateMachine'] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.state_history: List[str] = [initial_state.name]  # New: Track state history
        self.model_name = model_name or os.getenv('OPENAI_MODEL', 'gpt-4o')  # Default model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "current_state": self.current_state.name,
            "states": {name: state.to_dict() for name, state in self.states.items()},
            "transitions": [t.to_dict() for t in self.transitions],
            "children": {name: child.to_dict() for name, child in self.children.items()},
            "conversation_history": self.conversation_history[-10:]  # Only store last 10 turns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateMachine':
        initial_state = State.from_dict(data["states"][data["current_state"]])
        sm = cls(data["name"], initial_state)
        sm.id = data["id"]
        sm.states = {name: State.from_dict(state_data) for name, state_data in data["states"].items()}
        sm.transitions = [Transition.from_dict(t) for t in data["transitions"]]
        sm.children = {name: StateMachine.from_dict(child_data) for name, child_data in data["children"].items()}
        sm.conversation_history = data.get("conversation_history", [])
        return sm

    def add_state(self, state: State) -> None:
        with self.lock:
            self.states[state.name] = state

    def add_transition(self, transition: Transition) -> None:
        with self.lock:
            self.transitions.append(transition)
            # Add reverse transition to allow backtracking
            reverse_transition = Transition(
                from_state=transition.to_state,
                to_state=transition.from_state
            )
            self.transitions.append(reverse_transition)

    def generate_messages(self, user_input: str) -> List[Dict[str, Any]]:
        messages = []

        system_message = {
            "role": "system",
            "content": (
                f"You are an assistant that manages a state machine for a conversation. "
                f"Available states are: {', '.join(self.states.keys())}. "
                "After responding to the user, you must decide the next state by calling the 'set_next_state' function "
                "with the parameter 'next_state' set to one of the available states. "
                "Respond to the user appropriately before calling the function."
            )
        }
        messages.append(system_message)

        for turn in self.conversation_history[-5:]:  # Only use last 5 turns
            if 'user_input' in turn:
                messages.append({"role": "user", "content": turn['user_input']})
            if 'assistant_response' in turn:
                messages.append({"role": "assistant", "content": turn['assistant_response']})
            if 'function_call' in turn:
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": turn['function_call']
                })
            if 'function_response' in turn:
                messages.append({
                    "role": "function",
                    "name": turn['function_name'],
                    "content": turn['function_response']
                })

        if user_input:
            messages.append({"role": "user", "content": user_input})

        return messages

    def move_to_previous_state(self) -> None:
        with self.lock:
            if len(self.state_history) > 1:
                self.state_history.pop()  # Remove current state
                previous_state_name = self.state_history[-1]
                self.current_state = self.states[previous_state_name]
                print(f"Moved back to state: {previous_state_name}")
            else:
                print("Cannot move back. Already at the initial state.")

    def trigger_transition(self, user_input: str) -> None:
        with self.lock:
            messages = self.generate_messages(user_input)

            # Update the function that the assistant can call
            functions = [
                {
                    "name": "set_next_state",
                    "description": "Sets the next state of the state machine.",
                    "parameters": SetNextState.model_json_schema(),
                },
                {
                    "name": "move_to_previous_state",
                    "description": "Moves the state machine to the previous state.",
                    "parameters": {"type": "object", "properties": {}}
                }
            ]

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    functions=functions,
                    function_call="auto",  # Let the assistant decide whether to call the function
                )

                response_message = response.choices[0].message

                if response_message.function_call:
                    function_name = response_message.function_call.name
                    arguments = json.loads(response_message.function_call.arguments)

                    if function_name == "set_next_state":
                        next_state_name = arguments.get("next_state")
                        if next_state_name and next_state_name in self.states:
                            self.current_state = self.states[next_state_name]
                            self.state_history.append(next_state_name)  # Add to history
                            self.current_state.data.update_metadata(
                                llm_response=json.dumps(response_message.model_dump()),
                                llm_prompt=json.dumps(messages)
                            )
                            function_response = f"State changed to {next_state_name}"

                            # Append the function call and response to conversation history
                            self.conversation_history.append({
                                "user_input": user_input,
                                "function_call": response_message.function_call.model_dump(),
                                "function_response": function_response,
                                "function_name": function_name
                            })

                            # Include the function response in messages
                            new_messages = messages + [{
                                "role": "function",
                                "name": function_name,
                                "content": function_response
                            }]

                            # Call the model again to get the assistant's final response
                            second_response = client.chat.completions.create(
                                model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
                                messages=new_messages
                            )

                            second_response_message = second_response.choices[0].message
                            assistant_response = second_response_message.content.strip()

                            # Append the assistant's final response to conversation history
                            self.conversation_history.append({
                                "assistant_response": assistant_response
                            })

                            #print("Assistant Response:", assistant_response)
                        else:
                            raise ValueError(f"Invalid next state: {next_state_name}")
                    elif function_name == "move_to_previous_state":
                        self.move_to_previous_state()
                        function_response = f"Moved back to state: {self.current_state.name}"
                        # ... update conversation history and get final response ...
                    else:
                        raise ValueError(f"Unknown function: {function_name}")
                else:
                    # The assistant didn't call any function
                    assistant_response = response_message.content.strip()
                    self.conversation_history.append({
                        "user_input": user_input,
                        "assistant_response": assistant_response
                    })
                    #print("Assistant Response:", assistant_response)

            except Exception as e:
                print(f"Error in trigger_transition: {e}")
                raise 
                # Handle the error appropriately, e.g., set to a default state

    def visualize(self, filename: str) -> None:
        try:
            from graphviz import Digraph
        except ImportError:
            print("graphviz is not installed. Please install it to use the visualize method.")
            return

        dot = Digraph(name=self.name)
        for state in self.states.values():
            dot.node(state.name)
        for transition in self.transitions:
            dot.edge(transition.from_state, transition.to_state)
        dot.render(filename)

    def find_valid_transitions(self, user_input: str) -> List[Transition]:
        valid_transitions = []
        for transition in self.transitions:
            if transition.from_state == self.current_state.name:
                if transition.condition:
                    # Pass necessary context or data to the condition function
                    if transition.condition(user_input, self):
                        valid_transitions.append(transition)
                else:
                    valid_transitions.append(transition)
        return valid_transitions

class ChromaStateManager:
    def __init__(self, persist_directory: str, embedding_function=None):
        self.client = chromadb.PersistentClient(path=persist_directory)
        if embedding_function is None:
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.embedding_function = embedding_function
        self.collection = self.client.get_or_create_collection(
            name="state_machines",
            embedding_function=self.embedding_function
        )

    def save_state_machine(self, state_machine: StateMachine) -> None:
        documents = []
        metadatas = []
        ids = []

        for state in state_machine.states.values():
            state_text = f"{state.name}: {json.dumps(state.data.data)}"
            documents.append(state_text)
            metadatas.append({
                "type": "state_data",
                "state_machine_id": state_machine.id,
                "state_name": state.name,
                "state_data": json.dumps(state.data.to_dict())
            })
            ids.append(state.id)

        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        state_machine_data = state_machine.to_dict()
        self.collection.upsert(
            documents=[json.dumps(state_machine_data)],
            metadatas=[{"type": "state_machine_structure"}],
            ids=[state_machine.id]
        )

    def load_state_machine(self, state_machine_id: str) -> Optional[StateMachine]:
        try:
            results = self.collection.get(
                where={"type": "state_machine_structure"},
                ids=[state_machine_id]
            )
            if results['documents']:
                return StateMachine.from_dict(json.loads(results['documents'][0]))
        except Exception as e:
            print(f"Error loading state machine: {e}")
        return None

    def search_similar_states(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"type": "state_data"}
        )

        similar_states = []
        for i, (id, distance, metadata) in enumerate(zip(results['ids'][0], results['distances'][0], results['metadatas'][0])):
            similarity = 1 - distance  # Adjust based on ChromaDB's metric
            similar_states.append({
                'state_id': id,
                'state_machine_id': metadata['state_machine_id'],
                'state_name': metadata['state_name'],
                'similarity': similarity,
                'state_data': json.loads(metadata['state_data'])
            })

        return similar_states

# Example usage
if __name__ == "__main__":
    # Load API key from environment variable
    # Define initial state
    # Load API key from environment variable
    load_dotenv()

    # Define states
    welcome_state = State(
        id=str(uuid.uuid4()),
        name='Welcome',
        data=StateData(data={'message': 'Welcome to E-Shop! How can I assist you today?'})
    )

    main_menu_state = State(
        id=str(uuid.uuid4()),
        name='MainMenu',
        data=StateData(data={'message': 'Please choose an option: Order Tracking, Returns and Refunds, Product Inquiry, Account Management, or type "exit" to quit.'})
    )

    order_tracking_state = State(
        id=str(uuid.uuid4()),
        name='OrderTracking',
        data=StateData(data={'task': 'Assisting with order tracking...'})
    )

    collect_order_number_state = State(
        id=str(uuid.uuid4()),
        name='CollectOrderNumber',
        data=StateData(data={'message': 'Please provide your order number.'})
    )

    provide_order_status_state = State(
        id=str(uuid.uuid4()),
        name='ProvideOrderStatus',
        data=StateData(data={'task': 'Providing order status...'})
    )

    returns_refunds_state = State(
        id=str(uuid.uuid4()),
        name='ReturnsAndRefunds',
        data=StateData(data={'task': 'Assisting with returns and refunds...'})
    )

    product_inquiry_state = State(
        id=str(uuid.uuid4()),
        name='ProductInquiry',
        data=StateData(data={'task': 'Answering product inquiries...'})
    )

    account_management_state = State(
        id=str(uuid.uuid4()),
        name='AccountManagement',
        data=StateData(data={'task': 'Assisting with account management...'})
    )

    goodbye_state = State(
        id=str(uuid.uuid4()),
        name='Goodbye',
        data=StateData(data={'message': 'Thank you for visiting E-Shop! Have a great day!'})
    )

    # Create the state machine with a specified model (optional)
    state_machine = StateMachine(
        name='CustomerSupportAssistant',
        initial_state=welcome_state,
        model_name='gpt-4o'  # or any model you prefer
    )


    state_machine.add_state(main_menu_state)
    state_machine.add_state(order_tracking_state)
    state_machine.add_state(collect_order_number_state)
    state_machine.add_state(provide_order_status_state)
    state_machine.add_state(returns_refunds_state)
    state_machine.add_state(product_inquiry_state)
    state_machine.add_state(account_management_state)
    state_machine.add_state(goodbye_state)

        # Condition function to check if the user input requests order tracking
    def is_order_tracking(user_input: str, state_machine: StateMachine) -> bool:
        return 'track' in user_input.lower() or 'order' in user_input.lower()

    # Condition function to check if the user provided an order number
    def has_order_number(user_input: str, state_machine: StateMachine) -> bool:
        return any(char.isdigit() for char in user_input)

    # Condition function for exiting
    def is_exit_command(user_input: str, state_machine: StateMachine) -> bool:
        return user_input.lower() in ['exit', 'quit', 'goodbye']

    # Define transitions with conditions
    transitions = [
        Transition(from_state='Welcome', to_state='MainMenu'),
        Transition(from_state='MainMenu', to_state='OrderTracking', condition=is_order_tracking),
        Transition(from_state='OrderTracking', to_state='CollectOrderNumber'),
        Transition(from_state='CollectOrderNumber', to_state='ProvideOrderStatus', condition=has_order_number),
        Transition(from_state='ProvideOrderStatus', to_state='MainMenu'),
        Transition(from_state='MainMenu', to_state='Goodbye', condition=is_exit_command),
        # ... other transitions ...
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
        # state_machine.state_history.append(state_machine.current_state.name)

        while True:
            user_input = input("You: ")

            if not user_input.strip():
                continue  # Skip empty input

            # Before triggering transition, print current state
            print(f"\n[Before Transition] Current State: {state_machine.current_state.name}")

            # Exit the loop if the user wants to quit
            if user_input.lower() in ['exit', 'quit', 'goodbye']:
                state_machine.current_state = goodbye_state
                print(state_machine.current_state.data.data['message'])
                break

            state_machine.trigger_transition(user_input)

            # After triggering transition, print new state
            print(f"[After Transition] Current State: {state_machine.current_state.name}")

            # Update state history
            state_machine.state_history.append(state_machine.current_state.name)
            print(f"State History: {' -> '.join(state_machine.state_history)}")

            # After the transition, print the assistant's response
            if state_machine.conversation_history:
                last_turn = state_machine.conversation_history[-1]
                assistant_response = last_turn.get('assistant_response', '')
                if assistant_response:
                    print(f"Assistant: {assistant_response}")

            # Perform any actions associated with the current state
            if state_machine.current_state.name == 'ProvideOrderStatus':
                # Assume we stored the order_number in metadata
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
            elif state_machine.current_state.name == 'Goodbye':
                print(state_machine.current_state.data.data['message'])
                break

        # Optionally, after exiting, print the final state history
        print("\nFinal State History:")
        print(" -> ".join(state_machine.state_history))

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

# Import for OpenAI's API
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
    condition: Optional[Callable[[Any], bool]] = None
    action: Optional[Callable[[Any], None]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "condition": self.condition.__name__ if self.condition else None,
            "action": self.action.__name__ if self.action else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transition':
        condition = globals().get(data["condition"])
        action = globals().get(data["action"])
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
    def __init__(self, name: str, initial_state: State):
        self.lock = threading.Lock()
        self.id = str(uuid.uuid4())
        self.name = name
        self.current_state = initial_state
        self.states = {initial_state.name: initial_state}
        self.transitions: List[Transition] = []
        self.children: Dict[str, 'StateMachine'] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.state_history: List[str] = [initial_state.name]  # New: Track state history

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
                    model=os.getenv('OPENAI_MODEL', 'gpt-4'),
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
                                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                                messages=new_messages
                            )

                            second_response_message = second_response.choices[0].message
                            assistant_response = second_response_message.content.strip()

                            # Append the assistant's final response to conversation history
                            self.conversation_history.append({
                                "assistant_response": assistant_response
                            })

                            print("Assistant Response:", assistant_response)
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
                    print("Assistant Response:", assistant_response)

            except Exception as e:
                print(f"Error in trigger_transition: {e}")
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
    states = [
        State(id=str(uuid.uuid4()), name='initialize', data=StateData(data={'message': 'Initializing AI agent...'})),
        State(id=str(uuid.uuid4()), name='select_task', data=StateData(data={'message': 'Selecting next task...'})),
        State(id=str(uuid.uuid4()), name='gather_info', data=StateData(data={'message': 'Gathering information for task...'})),
        State(id=str(uuid.uuid4()), name='analyze_data', data=StateData(data={'message': 'Analyzing collected data...'})),
        State(id=str(uuid.uuid4()), name='execute_task', data=StateData(data={'message': 'Executing task...'})),
        State(id=str(uuid.uuid4()), name='review_outcome', data=StateData(data={'message': 'Reviewing task outcome...'})),
        State(id=str(uuid.uuid4()), name='update_task_list', data=StateData(data={'message': 'Updating task list...'})),
        State(id=str(uuid.uuid4()), name='idle', data=StateData(data={'message': 'All tasks complete. Waiting for new tasks...'})),
    ]

    # Create the state machine
    state_machine = StateMachine(name='AITaskManager', initial_state=states[0])

    # Add states to the state machine
    for state in states:
        state_machine.add_state(state)

    # Add transitions
    state_machine.add_transition(Transition(from_state='initialize', to_state='select_task'))
    state_machine.add_transition(Transition(from_state='select_task', to_state='gather_info'))
    state_machine.add_transition(Transition(from_state='gather_info', to_state='analyze_data'))
    state_machine.add_transition(Transition(from_state='analyze_data', to_state='execute_task'))
    state_machine.add_transition(Transition(from_state='execute_task', to_state='review_outcome'))
    state_machine.add_transition(Transition(from_state='review_outcome', to_state='update_task_list'))
    state_machine.add_transition(Transition(from_state='update_task_list', to_state='select_task'))
    state_machine.add_transition(Transition(from_state='update_task_list', to_state='idle'))

    # Save the state machine to ChromaDB
    chroma_manager = ChromaStateManager(persist_directory="chroma_db")
    chroma_manager.save_state_machine(state_machine)

    # Load the state machine from ChromaDB
    loaded_state_machine = chroma_manager.load_state_machine(state_machine.id)

    # Simulate AI agent operations
    print("Simulating AI Agent Task Management")
    print("===================================")

    # Define a list of tasks for the AI agent to complete
    tasks = [
        "Analyze market trends for Q3",
        "Optimize database queries for improved performance",
        "Generate monthly financial report",
        "Update customer segmentation model",
        "Conduct security audit of cloud infrastructure"
    ]

    def simulate_task_progress():
        progress = random.choice(["completed", "needs_more_info", "encountered_issue"])
        if progress == "needs_more_info":
            return "Task requires additional information. Returning to information gathering."
        elif progress == "encountered_issue":
            return "Encountered an issue during task execution. Reviewing and adjusting approach."
        else:
            return "Task completed successfully."

    task_index = 0
    while tasks:
        current_state = loaded_state_machine.current_state
        print(f"\nCurrent State: {current_state.name}")
        print(f"Action: {current_state.data.data['message']}")
        
        # Simulate some processing time
        time.sleep(1)
        
        if current_state.name == 'select_task':
            print(f"Selected Task: {tasks[task_index]}")
        elif current_state.name == 'execute_task':
            progress_result = simulate_task_progress()
            print(f"Task Progress: {progress_result}")
        elif current_state.name == 'update_task_list':
            if "completed successfully" in progress_result:
                completed_task = tasks.pop(task_index)
                print(f"Completed and removed task: {completed_task}")
                if tasks:
                    task_index = task_index % len(tasks)
                else:
                    print("All tasks completed!")
                    break  # Exit the loop when all tasks are completed
            else:
                task_index = (task_index + 1) % len(tasks)
        
        # Determine next state based on current state and task progress
        next_state = current_state.name
        if current_state.name == 'update_task_list':
            next_state = 'idle' if not tasks else 'select_task'
        elif current_state.name == 'review_outcome':
            next_state = 'update_task_list'
        elif current_state.name != 'idle':
            state_index = [s.name for s in states].index(current_state.name)
            next_state = states[(state_index + 1) % len(states)].name
        
        # Trigger state transition
        loaded_state_machine.trigger_transition(f"Moving to {next_state} state")
        
        # Simulate some more processing time
        time.sleep(1)

    # After the loop, ensure we're in the 'idle' state
    if loaded_state_machine.current_state.name != 'idle':
        loaded_state_machine.trigger_transition("Moving to idle state")

    print("\nAll tasks completed. State machine is now idle.")

    # Optional: Visualize the state machine
    loaded_state_machine.visualize("ai_task_manager")

    print("\nSimulation complete. All tasks finished. State machine visualization saved as 'ai_task_manager.pdf'")

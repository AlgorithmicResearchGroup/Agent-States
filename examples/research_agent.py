import os
import uuid
from dotenv import load_dotenv
from typing import Any, Dict

from ai_agent_state.state import (
    Metadata,
    StateData,
    State,
    Transition,
    StateMachine,
)

# Load environment variables (e.g., API keys)
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

# Define condition functions based on artifacts
def is_hypothesis_ready() -> bool:
    return os.path.exists('hypothesis.txt')  # Check if hypothesis document exists

def is_background_research_done() -> bool:
    return os.path.exists('background_research.pdf')  # Check if research document exists

def is_coding_complete() -> bool:
    return os.path.exists('model.py') and os.path.getsize('model.py') > 0  # Check if Python file exists and is not empty

def is_experiment_ready() -> bool:
    return os.path.exists('experiment_results.csv')  # Check if experiment results file exists

def is_results_analyzed() -> bool:
    return os.path.exists('analysis_report.docx')  # Check if analysis report exists

def is_exit_command() -> bool:
    return False  # This example does not use an exit command

# Define states
hypothesis_state = create_state('Hypothesis', {
    'message': 'Formulate your hypothesis for the research.'
})

background_research_state = create_state('BackgroundResearch', {
    'message': 'Conduct background research to support your hypothesis.'
})

coding_state = create_state('Coding', {
    'message': 'Start coding the model and prepare the dataset.'
})

experiment_state = create_state('Experiment', {
    'message': 'Run experiments to test your hypothesis.'
})

results_analysis_state = create_state('ResultsAnalysis', {
    'message': 'Analyze the results of your experiments.'
})

conclusion_state = create_state('Conclusion', {
    'message': 'Draw conclusions from your research findings.'
})

goodbye_state = create_state('Goodbye', {
    'message': 'Thank you for using the ML Research Assistant. Goodbye!'
})

# Create the state machine
state_machine = StateMachine(
    name='MLResearchAssistant',
    initial_state=hypothesis_state,
    model_name='gpt-4o'  # Replace with your desired model
)

# Add states to the state machine
state_machine.add_state(background_research_state)
state_machine.add_state(coding_state)
state_machine.add_state(experiment_state)
state_machine.add_state(results_analysis_state)
state_machine.add_state(conclusion_state)
state_machine.add_state(goodbye_state)

# Define transitions with condition functions
transitions = [
    create_transition('Hypothesis', 'BackgroundResearch', condition=is_hypothesis_ready),
    create_transition('BackgroundResearch', 'Coding', condition=is_background_research_done),
    create_transition('Coding', 'Experiment', condition=is_coding_complete),
    create_transition('Experiment', 'ResultsAnalysis', condition=is_experiment_ready),
    create_transition('ResultsAnalysis', 'Conclusion', condition=is_results_analyzed),
    create_transition('Conclusion', 'Goodbye', condition=is_exit_command),
]

# Add transitions to the state machine
for transition in transitions:
    state_machine.add_transition(transition)

def main():
    print(f"Current State: {state_machine.current_state.name}")
    print(state_machine.current_state.data.data['message'])

    while True:
        # Check for state transitions based on artifacts
        for transition in transitions:
            if transition.condition and transition.condition():
                state_machine.current_state = next(
                    state for state in state_machine.states if state.name == transition.to_state
                )
                state_machine.state_history.append(state_machine.current_state.name)
                break

        # Print current state and message
        print(f"[Current State] {state_machine.current_state.name}")
        print(f"Assistant: {state_machine.current_state.data.data['message']}")

        # Exit if in the Goodbye state
        if state_machine.current_state.name == 'Goodbye':
            break

    # Optionally, after exiting, print the final state history
    print("\nFinal State History:")
    print(" -> ".join(state_machine.state_history))

if __name__ == '__main__':
    main()
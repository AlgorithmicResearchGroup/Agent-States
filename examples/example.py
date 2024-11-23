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
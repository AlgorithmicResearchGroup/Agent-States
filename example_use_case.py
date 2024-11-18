import os
import uuid
from dotenv import load_dotenv
from typing import Any, Dict
import openai

from ai_agent_state.state import (
    Metadata,
    StateData,
    State,
    Transition,
    StateMachine,
) 

# Factory functions to simplify state and transition creation
def create_state(name: str, data: Dict[str, Any]) -> State:
    return State(
        id=str(uuid.uuid4()),
        name=name,
        data=StateData(data=data)
    )

def create_transition(from_state: str, to_state: str) -> Transition:
    return Transition(from_state=from_state, to_state=to_state)

# Define states
welcome_state = create_state('Welcome', {
    'message': 'Welcome to E-Shop! How can I assist you today?'
})

main_menu_state = create_state('MainMenu', {
    'message': 'Please choose an option: Order Tracking, Returns and Refunds, Product Inquiry, Account Management, or type "exit" to quit.'
})

order_tracking_state = create_state('OrderTracking', {
    'task': 'Assisting with order tracking...'
})

collect_order_number_state = create_state('CollectOrderNumber', {
    'message': 'Please provide your order number.'
})

provide_order_status_state = create_state('ProvideOrderStatus', {
    'task': 'Providing order status...'
})

returns_refunds_state = create_state('ReturnsAndRefunds', {
    'task': 'Assisting with returns and refunds...'
})

product_inquiry_state = create_state('ProductInquiry', {
    'task': 'Answering product inquiries...'
})

account_management_state = create_state('AccountManagement', {
    'task': 'Assisting with account management...'
})

goodbye_state = create_state('Goodbye', {
    'message': 'Thank you for visiting E-Shop! Have a great day!'
})

# Create the state machine
state_machine = StateMachine(
    name='CustomerSupportAssistant',
    initial_state=welcome_state,
    model_name='gpt-4o'  # Replace with your desired model
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


# Define transitions
transitions = [
    create_transition('Welcome', 'MainMenu'),
    create_transition('MainMenu', 'OrderTracking'),
    create_transition('OrderTracking', 'CollectOrderNumber'),
    create_transition('CollectOrderNumber', 'ProvideOrderStatus'),
    create_transition('ProvideOrderStatus', 'MainMenu'),
    create_transition('MainMenu', 'ReturnsAndRefunds'),
    create_transition('MainMenu', 'ProductInquiry'),
    create_transition('MainMenu', 'AccountManagement'),
    create_transition('MainMenu', 'Goodbye'),
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
    #state_machine.state_history.append(state_machine.current_state.name)

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

if __name__ == '__main__':
    main()
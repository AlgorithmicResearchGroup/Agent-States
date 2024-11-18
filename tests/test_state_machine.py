import unittest
import uuid
from datetime import datetime
from ai_agent_state.state import (
    Metadata,
    StateData,
    State,
    Transition,
    StateMachine,
    SetNextState,
    ChromaStateManager
) 
from unittest.mock import Mock
from unittest.mock import patch
import json

class TestMetadata(unittest.TestCase):
    def test_metadata_creation(self):
        metadata = Metadata()
        self.assertIsNotNone(metadata.created_at)
        self.assertIsNotNone(metadata.updated_at)

    def test_metadata_to_dict(self):
        metadata = Metadata()
        metadata_dict = metadata.to_dict()
        self.assertIn('created_at', metadata_dict)
        self.assertIn('updated_at', metadata_dict)

    def test_metadata_from_dict(self):
        metadata = Metadata()
        metadata_dict = metadata.to_dict()
        new_metadata = Metadata.from_dict(metadata_dict)
        self.assertEqual(metadata.created_at, new_metadata.created_at) 

class TestStateData(unittest.TestCase):
    def test_state_data_creation(self):
        state_data = StateData(data={'key': 'value'})
        self.assertEqual(state_data.data, {'key': 'value'})

    def test_state_data_update_metadata(self):
        state_data = StateData()
        state_data.update_metadata(llm_response='Test response')
        self.assertEqual(state_data.metadata.llm_response, 'Test response') 

class TestState(unittest.TestCase):
    def test_state_creation(self):
        state_data = StateData()
        state = State(id=str(uuid.uuid4()), name='test_state', data=state_data)
        self.assertEqual(state.name, 'test_state')

    def test_state_to_dict_and_from_dict(self):
        state_data = StateData(data={'key': 'value'})
        state = State(id=str(uuid.uuid4()), name='test_state', data=state_data)
        state_dict = state.to_dict()
        new_state = State.from_dict(state_dict)
        self.assertEqual(state.id, new_state.id)
        self.assertEqual(state.name, new_state.name)
        self.assertEqual(state.data.data, new_state.data.data) 

def sample_condition(data):
    return True

def sample_action(data):
    pass

class TestTransition(unittest.TestCase):
    def test_transition_creation(self):
        transition = Transition(
            from_state='state1',
            to_state='state2',
            condition=sample_condition,
            action=sample_action
        )
        self.assertEqual(transition.from_state, 'state1')
        self.assertEqual(transition.to_state, 'state2')
        self.assertEqual(transition.condition, sample_condition)
        self.assertEqual(transition.action, sample_action)

    def test_transition_to_dict_and_from_dict(self):
        transition = Transition(
            from_state='state1',
            to_state='state2',
            condition=sample_condition,
            action=sample_action
        )
        transition_dict = transition.to_dict()

        # Create a function registry for testing
        function_registry = {
            'sample_condition': sample_condition,
            'sample_action': sample_action
        }

        new_transition = Transition.from_dict(transition_dict, function_registry=function_registry)
        self.assertEqual(new_transition.from_state, 'state1')
        self.assertEqual(new_transition.to_state, 'state2')
        self.assertEqual(new_transition.condition, sample_condition)
        self.assertEqual(new_transition.action, sample_action) 

class TestChromaStateManager(unittest.TestCase):
    def setUp(self):
        # Mock the ChromaDB client and collection
        self.mock_collection = Mock()
        self.mock_client = Mock()
        self.mock_client.get_or_create_collection.return_value = self.mock_collection

        # Patch the chromadb.PersistentClient to return the mock client
        self.patcher = patch('chromadb.PersistentClient', return_value=self.mock_client)
        self.patcher.start()

        self.chroma_manager = ChromaStateManager(persist_directory='test_dir')

    def tearDown(self):
        self.patcher.stop()

    def test_save_state_machine(self):
        state_machine = StateMachine(name='TestStateMachine', initial_state=State(id='1', name='state1', data=StateData()))
        self.chroma_manager.save_state_machine(state_machine)
        # Verify that upsert was called
        self.assertTrue(self.mock_collection.upsert.called)

    def test_load_state_machine(self):
        # Set up the mock to return a predefined document
        state_machine_data = {
            'id': '1',
            'name': 'TestStateMachine',
            'current_state': 'state1',
            'states': {
                'state1': {'id': '1', 'name': 'state1', 'data': {'data': {}, 'metadata': {}}}
            },
            'transitions': [],
            'children': {},
            'conversation_history': []
        }
        self.mock_collection.get.return_value = {
            'documents': [json.dumps(state_machine_data)]
        }

        loaded_state_machine = self.chroma_manager.load_state_machine('1')
        self.assertIsNotNone(loaded_state_machine)
        self.assertEqual(loaded_state_machine.name, 'TestStateMachine') 
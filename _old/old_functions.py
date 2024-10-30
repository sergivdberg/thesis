from collections import defaultdict
from qiskit import QuantumCircuit
from QuantumCircuitCustom import QuantumcircuitCustom
from collections import defaultdict

# Function to remove non-unitary gates manually
def remove_non_unitary_gates(circuit):
    instructions_to_keep = []
    non_unitary_gates = ['reset', 'initialize', 'measure']  
    removed_gates = []  

    for index, instruction in enumerate(circuit.data):
        if instruction.operation.name in non_unitary_gates:
            removed_gates.append((index, instruction))  
        else:
            instructions_to_keep.append(instruction)

    circuit.data = instructions_to_keep
    return circuit, removed_gates


# Function to add back the removed non-unitary gates
def add_non_unitary_gates(circuit, removed_gates):
    # Sort removed_gates by the original index to insert them in the correct order
    removed_gates.sort(key=lambda x: x[0])

    # Insert gates back at the correct original positions
    for index, instruction in removed_gates:
        circuit.data.insert(index, instruction) 

    return circuit

def qubit_criticality_v1(circuit):
    
    number_of_qubits = circuit.num_qubits
    
    qubit_scores = defaultdict(float)

    # Gate weights for criticality
    gate_weights = {
        'rx': 1,
        'ry': 1,
        'rz': 1,
        'h': 1,
        'cx': 2,
        'cz': 2,
        'ccx': 3,
        'swap': 2,
        'measure': 1.5,
        'entangle': 3,
        'initialize': 1
    }

    operation_list = []

    # Collect operations and qubits they act on
    for instruction in circuit.data:
        operation_name = instruction.operation.name
        qubit_indices = tuple(qubit._index for qubit in instruction.qubits)
        operation_list.append((operation_name, qubit_indices)) 

    # Loop through operation_list and update qubit_scores based on gate weights
    for operation_name, qubit_indices in operation_list:
        weight = gate_weights.get(operation_name, 1) 
        
        # Assign points to all qubits involved in the operation
        for qubit in qubit_indices:
            qubit_scores[qubit] += weight  # Add the weight to the respective qubit's score

    max_score = max(qubit_scores.values())
    for qubit in qubit_scores:
        qubit_scores[qubit] /= max_score

    return qubit_scores



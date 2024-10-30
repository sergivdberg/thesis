from collections import defaultdict
from qiskit import QuantumCircuit
from QuantumCircuitCustom import QuantumcircuitCustom
from collections import defaultdict

def circuit_criticality_v1(circuit):
    
    number_of_qubits = circuit.num_qubits
    
    qubit_scores = defaultdict(float)

    # Gate weights for criticality
    gate_weights = {
        'rx': 1,
        'ry': 1,
        'rz': 1,
        'h': 1,
        'initialize': 1,
        'measure': 1.5,
        'cx': 2,
        'cz': 2,
        'swap': 2,
        'ccx': 3,
        'entangle': 3
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






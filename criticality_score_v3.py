from criticality_score_v2 import circuit_criticality_v2
from criticality_score_v1 import circuit_criticality_v1
import pydot
from qiskit.visualization import dag_drawer
from qiskit.converters import circuit_to_dag
from QuantumCircuitCustom import QuantumcircuitCustom

def circuit_criticality_v3(circuit):
    from collections import defaultdict

    number_of_qubits = circuit.num_qubits
    qubit_scores = defaultdict(float)

    # Updated gate weights
    gate_weights = {
        'rx': 1,
        'ry': 1,
        'rz': 1,
        'h': 1,
        'initialize': 1,
        'measure': 1,
        'cx': 1,
        'cz': 1,
        'crx': 1,
        'swap': 1,
        'ccx': 1,
        'entangle': 1
    }

    operation_list = []

    # Collect operations and qubits they act on
    for instruction in circuit.data:
        operation_name = instruction.operation.name
        qubit_indices = tuple(qubit._index for qubit in instruction.qubits)
        operation_list.append((operation_name, qubit_indices))

    total_operations = len(operation_list)

    # Analyze error propagation to get influence scores
    influence_scores = analyze_error_propagation(circuit)

    # Loop through operation_list and update qubit_scores based on gate weights and temporal weighting
    for idx, (operation_name, qubit_indices) in enumerate(operation_list):
        base_weight = gate_weights.get(operation_name, 1)
        # Temporal weighting: operations earlier in the circuit have higher weights
        temporal_weight = (total_operations - idx) / total_operations
        weighted_score = base_weight * temporal_weight

        if operation_name in ['cx', 'cz', 'crx', 'ccx']:
            # Control and target qubits
            control_qubit = qubit_indices[0]
            target_qubits = qubit_indices[1:]
            # Assign higher weight to control qubit
            qubit_scores[control_qubit] += weighted_score * 1.5  # Control qubit weight
            for target_qubit in target_qubits:
                qubit_scores[target_qubit] += weighted_score  # Target qubit weight
        elif operation_name == 'measure':
            # Measurement operation
            for qubit in qubit_indices:
                qubit_scores[qubit] += weighted_score * 1.2  # Slightly higher weight
        else:
            # Single-qubit gates or other operations
            for qubit in qubit_indices:
                qubit_scores[qubit] += weighted_score

    # Combine with influence scores
    # You can adjust the combination method (e.g., weighted sum, multiplication)
    for qubit in qubit_scores:
        qubit_scores[qubit] *= (1 + influence_scores.get(qubit, 0))

    # Normalize scores
    max_score = max(qubit_scores.values())
    for qubit in qubit_scores:
        qubit_scores[qubit] /= max_score

    return qubit_scores

from qiskit.converters import circuit_to_dag
from collections import defaultdict, deque 

def analyze_error_propagation(circuit):
    dag = circuit_to_dag(circuit)
    qubit_indices = [qubit._index for qubit in circuit.qubits]
    num_qubits = len(qubit_indices)
    influence_scores = {qubit: 0 for qubit in qubit_indices}

    # Build a mapping from qubits to the operations they are involved in
    qubit_operations = defaultdict(list)
    for node in dag.topological_op_nodes():
        for qubit in node.qargs:
            qubit_operations[qubit._index].append(node)

    # For each qubit do BFS to find reachable qubits
    for qubit in qubit_indices:
        visited_qubits = set()
        queue = deque()
        queue.append((qubit, 0))  # (current_qubit, depth)
        visited_qubits.add(qubit)

        while queue:
            current_qubit, depth = queue.popleft()

            # Increase influence score 
            influence_scores[qubit] += 1 / (1 + depth)

            # Look at operations involving current_qubit
            for node in qubit_operations[current_qubit]:
                # Check if the node is an entangling gate
                if node.name in ['cx', 'cz', 'crx', 'ccx', 'swap', 'entangle']:
                    # Find qubits involved in this gate
                    qubits_involved = [qarg._index for qarg in node.qargs]

                    if node.name in ['cx', 'cz', 'crx', 'ccx']:
                        # For controlled gates, identify control and target qubits
                        num_ctrl_qubits = node.op.num_ctrl_qubits
                        control_qubits = [qarg._index for qarg in node.qargs[:num_ctrl_qubits]]
                        target_qubits = [qarg._index for qarg in node.qargs[num_ctrl_qubits:]]

                        if current_qubit in control_qubits:
                            # Errors on control qubit can propagate to target qubits
                            for target_qubit in target_qubits:
                                if target_qubit not in visited_qubits:
                                    visited_qubits.add(target_qubit)
                                    queue.append((target_qubit, depth + 1))
                        elif current_qubit in target_qubits:
                            # Errors on target qubit do not propagate to control qubits
                            pass  # Do not enqueue control qubits
                    elif node.name == 'swap':
                        # For swap gates, errors propagate both ways
                        other_qubit = [q for q in qubits_involved if q != current_qubit][0]
                        if other_qubit not in visited_qubits:
                            visited_qubits.add(other_qubit)
                            queue.append((other_qubit, depth + 1))
                    elif node.name == 'entangle':
                        # Assuming 'entangle' is symmetric
                        for q in qubits_involved:
                            if q != current_qubit and q not in visited_qubits:
                                visited_qubits.add(q)
                                queue.append((q, depth + 1))
                else:
                    # For other gates, errors do not propagate to other qubits
                    pass
        # After processing all reachable qubits from 'qubit', influence_scores[qubit] is updated

    # Normalize influence scores
    max_score = max(influence_scores.values())
    if max_score > 0:
        for qubit in influence_scores:
            influence_scores[qubit] /= max_score

    return influence_scores

from qiskit import QuantumCircuit
# Setup
number_of_qubits = 10
qc_old = QuantumcircuitCustom(number_of_qubits, 3)
# Initialization
qc_old.initialize(0, qubits=[0,1,2,3,4,5,6,7,8,9])
qc_old.h(2)
qc_old.entangle(0,5)
qc_old.swap(0,1)
qc_old.swap(5,6)
qc_old.entangle(0,5)

# CZ gates and measure
qc_old.cz(0,2)
qc_old.swap(0,1)
qc_old.cz(0,2)
qc_old.swap(0,1)
qc_old.swap(0,2)
qc_old.h(0)
qc_old.measure(0,0)
qc_old.swap(0,2)

# CX gates on node 1
qc_old.cx(0,4)
qc_old.swap(0,1)
qc_old.cx(0,3)
qc_old.measure(0,1)
qc_old.swap(0,1)
qc_old.measure(0,1)

# CX gates on node 2
qc_old.cx(5,9)
qc_old.swap(5,6)
qc_old.cx(5,8)
qc_old.measure(5,2)
qc_old.swap(5,6)
qc_old.measure(5,2)

#Sample test circuit
def create_test_circuit():
    qc = QuantumCircuit(5)

    qc.h(0)  
    qc.cx(0, 1)  
    qc.cz(1, 2)  
    qc.swap(2, 3) 
    # qc.crx(1.5, 3, 4)
    qc.measure_all() 

    return qc

# Save the DAG as a .png image
def save_dag_to_image(circuit, filename="99_Qiskit_results_dag.png"):
    # Convert the circuit to a DAG
    dag = circuit_to_dag(circuit)
    
    # Use dag_drawer to generate the DAG as an image
    dag_image = dag_drawer(dag, filename=None)  # Generates a PIL Image object
    
    # Save the image directly to a file
    dag_image.save(filename)

# Display scores
def display_criticality_scores(circuit):
    score_v1 = circuit_criticality_v1(circuit)
    score_v2 = circuit_criticality_v2(circuit)
    score_v3 = circuit_criticality_v3(circuit)

    print(f"{'Qubit':<6}{'V1 Score':<15}{'V2 Score':<15}{'V3 Score':<15}")
    print("-" * 45)
    for qubit in sorted(score_v1.keys()):
        v1 = score_v1.get(qubit, 0)
        v2 = score_v2.get(qubit, 0)
        v3 = score_v3.get(qubit, 0)
        print(f"{qubit:<6}{v1:<15.4f}{v2:<15.4f}{v3:<15.4f}")

# Main
if __name__ == "__main__":
    test_circuit = qc_old
    print("Test Circuit:")
    print(test_circuit)

    # Display criticality scores side-by-side
    display_criticality_scores(test_circuit)

    # Save DAG as an image
    save_dag_to_image(test_circuit)
    print("\nDAG saved as an image in '99_Qiskit_results_dag.png'")


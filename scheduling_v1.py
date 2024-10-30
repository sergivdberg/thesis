from criticality_score_v3 import total_circuit_criticality
from qiskit.converters import circuit_to_dag
import qiskit as qk
from qiskit.transpiler import InstructionDurations, TranspilerError

def assign_operation_priorities(dag, circuit_criticality):
    node_priorities = {}
    for node in dag.topological_op_nodes():
        qubits = [qubit._index for qubit in node.qargs]
        priority = max(circuit_criticality.get(q,0) for q in qubits)
        node_priorities[node] = priority
    return node_priorities

# Priority-based scheduling
# Schedules operations whose dependencies have been satisfied
# Selects the next operation to schedule bassed on the highest priority

def priority_based_scheduler(dag, node_priorities):
    from qiskit.dagcircuit import DAGCircuit, DAGOpNode, DAGInNode  # Import DAGOpNode and DAGInNode classes
    scheduled_dag = DAGCircuit()

    # Add quantum registers
    for qreg in dag.qregs.values():
        scheduled_dag.add_qreg(qreg)

    # Add classical registers
    for creg in dag.cregs.values():
        scheduled_dag.add_creg(creg)

    # Initialize unscheduled nodes and ready nodes (nodes with no predecessors or only input nodes)
    unscheduled_nodes = set(dag.topological_op_nodes())

    # Mark nodes ready if all their predecessors are input nodes (DAGInNode)
    ready_nodes = set(node for node in unscheduled_nodes if all(isinstance(pred, DAGInNode) for pred in dag.predecessors(node)))

    scheduled_nodes = set()

    print(f"Initial ready nodes: {ready_nodes}")

    while unscheduled_nodes:
        if not ready_nodes:
            print("No nodes available to schedule! Debugging information:")
            print(f"Remaining unscheduled nodes: {unscheduled_nodes}")
            for node in unscheduled_nodes:
                print(f"Node: {node}")
                print(f"Predecessors: {list(dag.predecessors(node))}")
            raise Exception('No available nodes to schedule')

        # Pick ready node with the highest priority
        next_node = max(ready_nodes, key=lambda node: node_priorities.get(node, 0))
        ready_nodes.remove(next_node)
        unscheduled_nodes.remove(next_node)
        scheduled_nodes.add(next_node)

        # Schedule the node
        scheduled_dag.apply_operation_back(next_node.op, next_node.qargs, next_node.cargs)

        # Update ready nodes: successors whose predecessors are all scheduled
        for successor in dag.successors(next_node):
            if not isinstance(successor, DAGOpNode):
                continue
            if all(pred in scheduled_nodes or isinstance(pred, DAGInNode) for pred in dag.predecessors(successor) if isinstance(pred, DAGOpNode)):
                ready_nodes.add(successor)

        print(f"Ready nodes after scheduling {next_node}: {ready_nodes}")

    return scheduled_dag

# Add default duration handling for any missing durations
def add_missing_durations(gate_durations, quantum_circuit):
    # Set default durations (in ns)
    default_single_qubit_duration = 50
    default_multi_qubit_duration = 200

    # Copy existing gate durations
    updated_durations = gate_durations.duration_by_name.copy()

    # Add missing durations for gates in the circuit
    for instruction in quantum_circuit.data:
        op_name = instruction[0].name
        qargs = tuple(qubit._index for qubit in instruction[1])
        
        # Check if this instruction has a duration or if it's None
        try:
            duration = gate_durations.get(op_name, qargs, 'ns')
            if duration is None or (isinstance(duration, tuple) and duration[0] is None):
                # Use default duration based on the gate type
                duration = default_multi_qubit_duration if len(qargs) > 1 else default_single_qubit_duration
                updated_durations[(op_name, qargs)] = (duration, 'ns')
        except qk.transpiler.TranspilerError:
            # Assign default duration in case of an error
            duration = default_multi_qubit_duration if len(qargs) > 1 else default_single_qubit_duration
            updated_durations[(op_name, qargs)] = (duration, 'ns')

    # Re-create InstructionDurations ensuring no `None` durations
    updated_durations_list = []
    for item in updated_durations.items():
        if isinstance(item[1], tuple) and len(item[1]) == 2:
            inst_name, (duration, unit) = item
            if duration is None:
                duration = default_multi_qubit_duration  # Set a fallback duration if None
            updated_durations_list.append((inst_name, None, duration, unit))
        else:
            # Original structure for cases like ('cx', (duration, unit))
            (inst_name, qubits), value = item
            updated_durations_list.append((inst_name, qubits, *value))

    return InstructionDurations(updated_durations_list)





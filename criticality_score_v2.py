def circuit_criticality_v2(circuit):
    from collections import defaultdict

    number_of_qubits = circuit.num_qubits
    qubit_scores = defaultdict(float)

    # Updated gate weights
    gate_weights = {
        'rx': 1,
        'ry': 1,
        'rz': 1,
        'h': 1,
        'initialize': 0.5,
        'measure': 2,
        'cx': 3,
        'cz': 3,
        'crx': 3,
        'swap': 1.5,
        'ccx': 4,
        'entangle': 4
    }

    operation_list = []

    # Collect operations and qubits they act on
    for instruction in circuit.data:
        operation_name = instruction.operation.name
        qubit_indices = tuple(qubit._index for qubit in instruction.qubits)
        operation_list.append((operation_name, qubit_indices))

    total_operations = len(operation_list)

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
            qubit_scores[control_qubit] += weighted_score * 1.5 
            for target_qubit in target_qubits:
                qubit_scores[target_qubit] += weighted_score 
        elif operation_name == 'measure':
            # Measurement operation
            for qubit in qubit_indices:
                qubit_scores[qubit] += weighted_score * 1.2  
        else:
            # Single-qubit gates or other operations
            for qubit in qubit_indices:
                qubit_scores[qubit] += weighted_score

    # Normalize scores
    if qubit_scores:
        max_score = max(qubit_scores.values())
        for qubit in qubit_scores:
            qubit_scores[qubit] /= max_score
    else:
        max_score = 1  # Avoid division by zero if qubit_scores is empty

    return qubit_scores

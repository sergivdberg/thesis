from qiskit import QuantumCircuit
import qiskit as qk
import numpy as np

def QASMtoBackend(circuit):
    number_of_qubits = circuit.num_qubits
    number_of_nodes = circuit.number_of_nodes
    number_of_qubits_per_node = int(number_of_qubits / number_of_nodes)
    result = f"version 1.0\n\nqubits {number_of_qubits}\n\n"
    print(f'The number of qubits in transpiler are {number_of_qubits} with number of nodes being {number_of_nodes}')

    # Dictionary to store notes for instructions using the instruction index
    instruction_notes = {}

    for idx, instruction in enumerate(circuit.data):
        gate = instruction.operation

        # Convert the gate to mutable directly
        gate = gate.to_mutable()

        # Add notes to the gate if not already present
        if "notes" not in dir(gate):
            gate.notes = {}

        # Store the notes in a separate dictionary using the index
        instruction_notes[idx] = gate.notes

        print(f"The notes are {gate.notes}")

        gate_name = gate.name

        if gate_name == "cx":
            result += f"QgateEZ q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} 0  1.57\n"
            result += f"QgateCC q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1} 0 3.14\n"

        elif gate_name == "crx":
            print(f'Qubit index is {instruction.qubits[0]._index} with number per node {number_of_qubits_per_node} resulting in index {instruction.qubits[0]._index % number_of_qubits_per_node}')
            result += f"QgateCC q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1} {abs(np.sign(gate.params[0]) * 1.57 - 1.57)} {abs(gate.params[0])}\n"

        elif gate_name == "swap":
            result += f"full_swap q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1}\n"

        elif gate_name == "ry":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"QgateE q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {np.sign(gate.params[0]) * 1.57} {abs(gate.params[0])}\n"
            else:
                preserved_parameter = instruction_notes[idx].get("preserved", 0)
                result += f"QgateUC q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[0]._index % number_of_qubits_per_node - 1} {np.sign(gate.params[0]) * 1.57} {abs(gate.params[0])} {preserved_parameter}\n"

        elif gate_name == "rx":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"QgateE q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {abs(np.sign(gate.params[0]) * 1.57 - 1.57)} {abs(gate.params[0])}\n"
            else:
                preserved_parameter = instruction_notes[idx].get("preserved", 0)
                result += f"QgateUC q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[0]._index % number_of_qubits_per_node - 1} {abs(np.sign(gate.params[0]) * 1.57 - 1.57)} {gate.params[0]} {preserved_parameter}\n"

        elif gate_name == "rz":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"QgateEZ q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} 0 {abs(gate.params[0])}\n"
            else:
                result += f"QgateCZ q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[0]._index % number_of_qubits_per_node - 1} {gate.params[0]}\n"

        elif gate_name == "entangle":
            result += f"NVentangle q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} q{int(np.floor(instruction.qubits[1]._index / number_of_qubits_per_node))}\n"

        elif gate_name == "SwapCE":
            result += f"SwapCE q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1} {instruction_notes[idx].get('basis', '')}\n"

        elif gate_name == "SwapEC":
            result += f"SwapEC q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1} {instruction_notes[idx].get('basis', '')}\n"

        elif gate_name == "measure":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"measure q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"
            else:
                result += f"swapce q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} z {instruction.qubits[1]._index % number_of_qubits_per_node - 1}\n"
                result += f"measure q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"

        elif gate_name == "reset":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"Initialize q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"
            else:
                result += f"Initialize q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"
                result += f"swapec q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1}\n"

        elif gate_name == "initialize":
            if (instruction.qubits[0]._index % number_of_qubits_per_node == 0):
                result += f"Initialize q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"
            else:
                result += f"Initialize q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))}\n"
                result += f"swapec q{int(np.floor(instruction.qubits[0]._index / number_of_qubits_per_node))} {instruction.qubits[1]._index % number_of_qubits_per_node - 1}\n"

        elif gate_name == "while_loop":
            pass

        else:
            raise Exception(f"Unknown gate! namely {gate_name}. Add me to the match case")

    return result

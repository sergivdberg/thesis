# Import necessary modules
from qiskit import QuantumCircuit
import qiskit as qk
from qiskit.compiler import transpile, assemble, schedule, sequence
from qasm_transpiler import QASMtoBackend
# from qiskit import QISKIT_settings
from transpiler_pass import FirstPass, TrackingPassPreserve, CXCarbonFix
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import (
    BasisTranslator,
    CommutativeCancellation,
    Optimize1qGatesDecomposition,
    SetLayout,
    TrivialLayout
)
from qiskit.circuit.library import XGate, HGate, CRXGate, RZGate, StatePreparation
import numpy as np
from QuantumCircuitCustom import QuantumcircuitCustom
from qiskit.circuit.equivalence import EquivalenceLibrary
from qiskit.circuit.library.standard_gates.equivalence_library import StandardEquivalenceLibrary
from qiskit.transpiler import CouplingMap
from qiskit.circuit.library import Initialize
import os
from criticality_score_v1 import qubit_criticality

# For circuit visualization
from qiskit.visualization import circuit_drawer

number_of_qubits = 10
qc_old = QuantumcircuitCustom(number_of_qubits, 3)

number_of_nodes = 2
qc_old.number_of_nodes = number_of_nodes
number_of_qubits_per_node = int(number_of_qubits / number_of_nodes)

### Start of quantum algorithm ###

# Initialization
qc_old.initialize(0, qubits=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
qc_old.h(2)
qc_old.entangle(0, 5)
qc_old.swap(0, 1)
qc_old.swap(5, 6)
qc_old.entangle(0, 5)

# CZ gates and measure
qc_old.cz(0, 2)
qc_old.swap(0, 1)
qc_old.cz(0, 2)
qc_old.swap(0, 1)
qc_old.swap(0, 2)
qc_old.h(0)
qc_old.measure(0, 0)
qc_old.swap(0, 2)

# CX gates on node 1
qc_old.cx(0, 4)
qc_old.swap(0, 1)
qc_old.cx(0, 3)
qc_old.measure(0, 1)
qc_old.swap(0, 1)
qc_old.measure(0, 1)

# CX gates on node 2
qc_old.cx(5, 9)
qc_old.swap(5, 6)
qc_old.cx(5, 8)
qc_old.measure(5, 2)
qc_old.swap(5, 6)
qc_old.measure(5, 2)

# Calculate criticality scores before transpilation
score = qubit_criticality(qc_old)
print("Criticality scores before transpilation:")
print(score)

### End of quantum algorithm ###

# Save the original circuit diagram
qc_old_fig = circuit_drawer(qc_old, output='mpl', fold=-1)
qc_old_fig.savefig('qc_old.png')
print("Original circuit saved as 'qc_old.png'")

# Continue with transpilation passes
basis_gates = [
    'rx', 'ry', 'rz', 'crx', 'swap', 'entangle',
    'SwapEC', 'SwapCE', 'initialize', 'reset'
]

# Coupling map setup
couplinglist = []
for i in [0, 5]:
    for j in range(i + 1, i + 5):
        couplinglist.append([i, j])

print(f"The coupling list is {couplinglist}")
print('Before layout:')
print(qc_old.draw())

coupling_map = CouplingMap(couplinglist=couplinglist)

# Apply TrivialLayout
pm = PassManager([TrivialLayout(coupling_map=coupling_map)])
qc_after_layout = pm.run(qc_old)
print('After layout:')
print(qc_after_layout.draw())

# Apply CXCarbonFix
pm = PassManager([CXCarbonFix(number_of_qubits_per_node=number_of_qubits_per_node)])
qc_after_carbon_fix = pm.run(qc_after_layout)
print('After Carbon Fix:')
print(qc_after_carbon_fix.draw())

# Apply CommutativeCancellation
pm = PassManager([CommutativeCancellation(basis_gates=basis_gates)])
qc_after_comm_cancellation = pm.run(qc_after_carbon_fix)
print('After Commutative Cancellation:')
print(qc_after_comm_cancellation.draw())

# Apply BasisTranslator
pm = PassManager([BasisTranslator(
    equivalence_library=StandardEquivalenceLibrary,
    target_basis=basis_gates
)])
qc_after_basis_translator = pm.run(qc_after_comm_cancellation)
print('After Basis Translator:')
print(qc_after_basis_translator.draw())

# Apply Optimize1qGatesDecomposition
pm = PassManager([Optimize1qGatesDecomposition(basis=basis_gates)])
qc_after_optimize_gates = pm.run(qc_after_basis_translator)
print('After Optimize 1q Gates Decomposition:')
print(qc_after_optimize_gates.draw())

# Apply TrackingPassPreserve
pm = PassManager([TrackingPassPreserve(number_of_qubits_per_node=number_of_qubits_per_node)])
qc = pm.run(qc_after_optimize_gates)
# print('After Tracking Pass Preserve:')
# print(qc.draw(justify='none'))  # 'none' to keep the sequence

qc.number_of_nodes = number_of_nodes

# Save the transpiled circuit diagram
qc_transpiled_fig = circuit_drawer(qc, output='mpl', fold=-1)
qc_transpiled_fig.savefig('qc_transpiled.png')
print("Transpiled circuit saved as 'qc_transpiled.png'")

# Save the final result
result = QASMtoBackend(qc)
filename = "old.json"
directory = "./99 Qiskit results/"

if not os.path.exists(directory):
    os.makedirs(directory)

with open(f"{directory}{filename}", 'w') as file:
    file.write(result)

print(f"File saved as {directory}{filename}")

# Calculate criticality scores after transpilation
score = qubit_criticality(qc)
print("Criticality scores after transpilation:")
print(score)


# Iterate over the instructions in the transpiled circuit
print("\nInstructions in the transpiled circuit:")
for idx, instruction in enumerate(qc.data):
    operation_name = instruction.operation.name
    qubits_involved = [qubit._index for qubit in instruction.qubits]
    clbits_involved = [clbit._index for clbit in instruction.clbits]
    print(f"{idx}: Operation: {operation_name}, Qubits: {qubits_involved}, Clbits: {clbits_involved}")
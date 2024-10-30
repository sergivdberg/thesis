import numpy as np
import os
import qiskit as qk
import matplotlib.pyplot as plt

# Qiskit modules
from qiskit import QuantumCircuit
from qiskit.compiler import transpile, assemble
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.transpiler.passes import (
    BasisTranslator, CommutativeCancellation, Optimize1qGatesDecomposition,
    RemoveResetInZeroState, ALAPScheduleAnalysis
)
from qiskit.circuit.library.standard_gates.equivalence_library import StandardEquivalenceLibrary

from qiskit.transpiler import TransformationPass
from qiskit.transpiler.layout import Layout
from qiskit.transpiler import InstructionDurations
from qiskit.visualization.timeline import draw as timeline_drawer
from qiskit.converters import circuit_to_dag, dag_to_circuit

# Custom modules
from qasm_transpiler import QASMtoBackend
from transpiler_pass import CXCarbonFix, TrackingPassPreserve, NoiseAwareLayout
from quantum_circuit_custom import QuantumcircuitCustom

# Importing criticality functions from v2 and v3

from criticality_score_v1 import circuit_criticality_v1
from criticality_score_v2 import circuit_criticality_v2
from criticality_score_v3 import circuit_criticality_v3, analyze_error_propagation, create_test_circuit
from scheduling_v1 import assign_operation_priorities, priority_based_scheduler, add_missing_durations

# For circuit visualization
from qiskit.visualization import circuit_drawer

# For handling default dicts
from collections import defaultdict

# Noise data
qubit_noise_data = {
    0: {'T1': 50e-6, 'T2': 70e-6, 'gate_error': 0.01, 'readout_error': 0.02},
    1: {'T1': 45e-6, 'T2': 65e-6, 'gate_error': 0.015, 'readout_error': 0.025},
    2: {'T1': 55e-6, 'T2': 75e-6, 'gate_error': 0.009, 'readout_error': 0.018},
    3: {'T1': 48e-6, 'T2': 68e-6, 'gate_error': 0.012, 'readout_error': 0.022},
    4: {'T1': 52e-6, 'T2': 72e-6, 'gate_error': 0.011, 'readout_error': 0.021},
    5: {'T1': 47e-6, 'T2': 67e-6, 'gate_error': 0.013, 'readout_error': 0.023},
    6: {'T1': 53e-6, 'T2': 73e-6, 'gate_error': 0.010, 'readout_error': 0.019},
    7: {'T1': 49e-6, 'T2': 69e-6, 'gate_error': 0.014, 'readout_error': 0.024},
    8: {'T1': 51e-6, 'T2': 71e-6, 'gate_error': 0.011, 'readout_error': 0.020},
    9: {'T1': 46e-6, 'T2': 66e-6, 'gate_error': 0.016, 'readout_error': 0.026},
}

# Define durations
instruction_durations = [
    ('rx', None, 50, 'ns'),
    ('ry', None, 50, 'ns'),
    ('rz', None, 0, 'ns'), 
    ('h', None, 50, 'ns'),
    ('cx', None, 200, 'ns'),
    ('cz', None, 200, 'ns'),
    ('crx', None, 200, 'ns'),  
    ('swap', None, 300, 'ns'),
    ('ccx', None, 400, 'ns'),
    ('entangle', None, 500, 'ns'),
    ('measure', None, 1000, 'ns'),
    ('measure_all', None, 1000, 'ns'),
    ('initialize', None, 1000, 'ns')
]

gate_durations = InstructionDurations(instruction_durations)


# Setup
number_of_qubits = 10
qc_old = QuantumcircuitCustom(number_of_qubits, 3)

number_of_nodes = 2
qc_old.number_of_nodes = number_of_nodes
number_of_qubits_per_node = int(number_of_qubits / number_of_nodes)

### Start of quantum algorithm ###

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

### End of quantum algorithm ###

# Coupling map setup
couplinglist = []
for i in [0, 5]:
    for j in range(i + 1, i + 5):
        couplinglist.append([i, j])

print(f"The coupling list is {couplinglist}")

coupling_map = CouplingMap(couplinglist=couplinglist)

# Build basis gates
basis_gates = ['rx', 'ry', 'rz', 'crx', 'swap', 'entangle', 'SwapEC', 'SwapCE', 'initialize', 'reset']

# Calculate criticality scores before transpilation using v2
old_scores_v2 = circuit_criticality_v2(qc_old)

# Calculate total criticality scores before transpilation using v3
old_scores_v3 = circuit_criticality_v3(qc_old)

# Single PassManager with all passes
pm = PassManager([
    # Noise-aware layout
    NoiseAwareLayout(
        noise_data=qubit_noise_data,
        coupling_map=coupling_map,
        qubit_criticality=old_scores_v3  # Using v3 scores for layout
    ),
    # Custom pass to fix CX gates
    CXCarbonFix(number_of_qubits_per_node=number_of_qubits_per_node),
    # Commutative cancellation to simplify the circuit
    CommutativeCancellation(),
    # Translate to the desired basis gates
    BasisTranslator(equivalence_library=StandardEquivalenceLibrary, target_basis=basis_gates),
    # Optimize single-qubit gates
    Optimize1qGatesDecomposition(basis=basis_gates),
    # Tracking pass to preserve qubit mapping
    TrackingPassPreserve(number_of_qubits_per_node=number_of_qubits_per_node),
    # Remove redundant resets (optional)
    RemoveResetInZeroState()
])

# Run the transpiler with the single pass manager
qc_transpiled = pm.run(qc_old)

# Access the layout from the property set of the pass manager
layout = pm.property_set['layout']

# Save the initial circuit diagram
qc_old_fig = circuit_drawer(qc_old, output='mpl', fold=-1)

file_name= 'qc_old.png'
directory = "./99 Qiskit results/"

# Ensure directory exists
if not os.path.exists(directory):
    os.makedirs(directory)

# Save the figure using the correct method
qc_old_fig.savefig(f"{directory}{file_name}")

# Save the transpiled circuit diagram
qc_transpiled_fig = circuit_drawer(qc_transpiled, output='mpl', fold=-1)

file_name= 'qc_transpiled.png'

# Save the figure using the correct method
qc_transpiled_fig.savefig(f"{directory}{file_name}")

print("\nOriginal circuit saved as 'qc_old.png'")
print("Transpiled circuit saved as 'qc_transpiled.png'")

# Create initial mapping from physical qubits to logical qubits
current_mapping = {v: k._index for k, v in layout.get_virtual_bits().items()}

# Calculate criticality scores after transpilation using v2
new_scores_v2 = circuit_criticality_v2(qc_old)

# Calculate total criticality scores after transpilation using v3
new_scores_v3 = circuit_criticality_v3(qc_old)

# # Print the comparison of criticality scores for logical qubits
# print("\nComparison of criticality scores for logical qubits:")
# print("Logical Qubit\tV2 Score\tV3 Score")
# for lq_index in sorted(old_scores_v2.keys()):
#     score_v2 = new_scores_v2.get(lq_index, 0)
#     score_v3 = new_scores_v3.get(lq_index, 0)
#     print(f"{lq_index}\t\t{score_v2:.2f}\t\t{score_v3:.2f}")

# # Final qubit mapping after criticality-aware transpilation
# print("\nFinal qubit mapping after criticality-aware transpilation:")
# for lq in qc_old.qubits:
#     pq = layout[lq]
#     lq_index = lq._index
#     lq_criticality = old_scores_v3.get(lq_index, 0)
#     pq_gate_error = qubit_noise_data[pq]['gate_error']
#     print(f"Logical qubit {lq_index} (criticality {lq_criticality:.2f}) mapped to physical qubit {pq} with gate error {pq_gate_error}")

qc_new = create_test_circuit()

gate_durations = add_missing_durations(gate_durations, qc_new)
print("Final gate durations after filling missing values:")
for duration in gate_durations.duration_by_name.items():
    print(duration)

pm_default_schedule = PassManager([
    ALAPScheduleAnalysis(durations=gate_durations)
])

qc_scheduled_default = pm_default_schedule.run(qc_new)

criticality_scores = circuit_criticality_v3(qc_new)

dag = circuit_to_dag(qc_new)

node_priorities = assign_operation_priorities(dag, criticality_scores)

scheduled_dag_criticality = priority_based_scheduler(dag, node_priorities)
qc_scheduled_criticality = dag_to_circuit(scheduled_dag_criticality)

# Reinitialize gate_durations with fallback values explicitly included
fallback_durations = [
    ('rx', None, 50, 'ns'), ('ry', None, 50, 'ns'), ('rz', None, 0, 'ns'),
    ('h', None, 50, 'ns'), ('cx', None, 200, 'ns'), ('cz', None, 200, 'ns'),
    ('crx', None, 50, 'ns'), ('swap', None, 300, 'ns'), ('ccx', None, 400, 'ns'),
    ('entangle', None, 500, 'ns'), ('measure', None, 1000, 'ns'),
    ('initialize', None, 1000, 'ns'), ('barrier', None, 0, 'ns')
]

gate_durations = InstructionDurations(fallback_durations)

# Re-schedule the circuit with the updated durations
pm_default_schedule = PassManager([ALAPScheduleAnalysis(durations=gate_durations)])
qc_scheduled_default = pm_default_schedule.run(qc_new)

# Verify all operations have durations before drawing
for op in qc_scheduled_default.data:
    if not hasattr(op.operation, 'duration') or op.operation.duration is None:
        print(f"{op.operation.name} still has no duration; check duration assignment.")
    else:
        print(f"{op.operation.name} duration: {op.operation.duration} ns")

try:
    timeline_default_fig = timeline_drawer(qc_scheduled_default)
    timeline_default_fig.show()
except TypeError as e:
    print("Error generating timeline:", e)

# Display the timelines side by side
from PIL import Image

# Open the images
img_default = Image.open(f"{directory}timeline_default.png")
img_criticality = Image.open(f"{directory}timeline_criticality.png")

# Determine the size of the combined image
widths = img_default.width + img_criticality.width
heights = max(img_default.height, img_criticality.height)

# Create a new image with the combined size
combined_image = Image.new('RGB', (widths, heights))

# Paste the images side by side
combined_image.paste(img_default, (0, 0))
combined_image.paste(img_criticality, (img_default.width, 0))

# Save and display the combined image
combined_image.save(f"{directory}timelines_side_by_side.png")
combined_image.show()

                                            
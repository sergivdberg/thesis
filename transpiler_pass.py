from qiskit.dagcircuit import DAGCircuit
from qiskit.circuit import QuantumCircuit, QuantumRegister, Gate, ClassicalRegister
from qiskit.circuit.library import CXGate, ECRGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.quantum_info import Operator, pauli_basis
from qiskit.circuit.library import XGate, HGate, CRXGate, RZGate

import numpy as np
 
from typing import Iterable, Optional
from qiskit.transpiler.layout import Layout


### a pass that does not do anything. This is an example of how you could change some things using a pass.
class FirstPass(TransformationPass):
    """Change Hadamard operations."""
    def __init__(
        self,
    ):
        super().__init__()
    def run(
        self,
        dag: DAGCircuit,
    ) -> DAGCircuit:
        # print(f'dag nodes are {dag.op_nodes()}')
        for node in dag.op_nodes():
            mini_dag = DAGCircuit()
            register = QuantumRegister(node.op.num_qubits)
            mini_dag.add_qreg(register)
            if node.op.name == 'h':
                operation = node.op.to_mutable()
                operation.name = 'x'
                operation.notes = 'hello'
                mini_dag.apply_operation_back(operation, qargs = [register[0]])
            else:
                mini_dag.apply_operation_back(node.op, qargs = [register[0],register[1]])
            dag.substitute_node_with_dag(node, mini_dag)
        return dag


class CXCarbonFix(TransformationPass):
    """Change CX operations from carbon to electron. CX gates from a carbon to an electron are not possible, so they need to be decomposed in a special manner"""
    def __init__(
        self,
        number_of_qubits_per_node
    ):
        super().__init__()
        self.number_of_qubits_per_node = number_of_qubits_per_node
    def run(
        self,
        dag: DAGCircuit,
    ) -> DAGCircuit:
        for node in dag.op_nodes():
            mini_dag = DAGCircuit()
            register = QuantumRegister(node.op.num_qubits)
            mini_dag.add_qreg(register)
            if node.op.num_qubits > 1 and (node.op.name != 'entangle' and node.op.name != 'initialize' and  node.op.name != 'swap') :

                if node.qargs[1]._index % self.number_of_qubits_per_node == 0:
                    operation = node.op.to_mutable()
                    mini_dag.apply_operation_back(HGate(), qargs = [register[1]])
                    mini_dag.apply_operation_back(HGate(), qargs = [register[0]])
                    operation = RZGate(phi = np.pi/2)
                    mini_dag.apply_operation_back(operation, qargs = [register[1]])
                    operation = CRXGate(theta = np.pi)
                    mini_dag.apply_operation_back(operation, qargs = [register[1],register[0]])

                    mini_dag.apply_operation_back(HGate(), qargs = [register[1]])
                    mini_dag.apply_operation_back(HGate(), qargs = [register[0]])
                else:
                    mini_dag.apply_operation_back(node.op, qargs = [register[0],register[1]])
                    
            elif node.op.num_qubits > 1:
                mini_dag.apply_operation_back(node.op, qargs = [register[0],register[1]])
                return dag
                # continue
            else:
                mini_dag.apply_operation_back(node.op, qargs = [register[0]])
            dag.substitute_node_with_dag(node, mini_dag)
 
        return dag

###
class TrackingPassPreserve(TransformationPass):
    """Tracking pass, it tracks the state of the electron and typecasts qubits. These typecasts are needed in order to decompose
        instructions accordingly. (instruction decompositions are dependent on the type of qubit)"""
 
    def __init__(
        self,
        number_of_qubits_per_node
    ):
        super().__init__()
        self.number_of_qubits_per_node = number_of_qubits_per_node
    def run(
        self,
        dag: DAGCircuit,
    ) -> DAGCircuit:
        number_of_qubits_per_node = self.number_of_qubits_per_node
        electron_state_important = 0
        electron_state_counter = 0
        
        NV_nodes_electron_importance = {('NVnode'+str(x)):0 for x in range(4)} #fix 4 to later be number of nodes
        counter = 0
        mini_dag = DAGCircuit()
        mini_dag = dag.copy_empty_like()

        for node in dag.op_nodes():
            qubit_type = 'carbon' if (node.qargs[0]._index % number_of_qubits_per_node != 0 or node.op.num_qubits > 1) else 'electron'
            operation = node.op.to_mutable()
            if "notes" in dir(operation):
                pass
            else:
                operation.notes = {}
            if qubit_type == 'electron':
                if operation.name == 'measure':

                    NV_nodes_electron_importance['NVnode'+str(int(np.floor(node.qargs[0]._index/number_of_qubits_per_node)))] = 0

                else:
                    NV_nodes_electron_importance['NVnode'+str(int(np.floor(node.qargs[0]._index/number_of_qubits_per_node)))] = 1
                
            else:
                if operation.name == 'measure' or operation.name == 'initialise':
                    pass
                else:
                    if NV_nodes_electron_importance['NVnode'+str(int(np.floor(node.qargs[0]._index/number_of_qubits_per_node)))] == 0:
                        if counter > 3:
                            operation.notes['preserved'] = 1
                        else:
                            operation.notes['preserved'] = 0
                        operation.notes['NVnode'+str(int(np.floor(node.qargs[0]._index/number_of_qubits_per_node)))] = 0

                    else:
                        operation.notes['preserved'] = 1
                        operation.notes['NVnode'+str(int(np.floor(node.qargs[0]._index/number_of_qubits_per_node)))] = 1
                    
            counter +=1

            mini_dag.apply_operation_back(operation, qargs = node.qargs, cargs = node.cargs)
        return mini_dag

## work in progress ##
class GateCommutation(TransformationPass):
    """Do gate commutation on when swaps are happening"""
 
    def __init__(
        self,
        number_of_qubits_per_node
    ):
        super().__init__()
        self.number_of_qubits_per_node = number_of_qubits_per_node
    def run(
        self,
        dag: DAGCircuit,
    ) -> DAGCircuit:
        # if node.op.name == 'swap':
        # mini_dag = DAGCircuit()
        mini_dag = dag.copy_empty_like()
        node_list = dag.op_nodes()
        for node_iter, node in enumerate(node_list):
            if node.op.name == 'swap':
                pass

            operation = node.op.to_mutable()

            mini_dag.apply_operation_back(operation, qargs = node.qargs, cargs = node.cargs)

        return mini_dag
    
class NoiseAwareLayout(TransformationPass):
    def __init__(self, noise_data, coupling_map, qubit_criticality):
        super().__init__()
        self.noise_data = noise_data
        self.coupling_map = coupling_map
        self.qubit_criticality = qubit_criticality

    def run(self, dag):
        logical_qubits = dag.qubits
        physical_qubits = list(self.noise_data.keys())

        # Create a cost matrix based on criticality and gate errors
        cost_matrix = []
        for lq in logical_qubits:
            lq_index = lq._index
            lq_criticality = self.qubit_criticality.get(lq_index, 0)
            costs = []
            for pq in physical_qubits:
                pq_gate_error = self.noise_data[pq]['gate_error']
                cost = lq_criticality * pq_gate_error
                costs.append(cost)
            cost_matrix.append(costs)

        # Use the Hungarian algorithm to find the optimal assignment
        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        mapping = {logical_qubits[row]: physical_qubits[col] for row, col in zip(row_ind, col_ind)}

        # Create the layout
        layout = Layout(mapping)
        self.property_set['layout'] = layout

        return dag

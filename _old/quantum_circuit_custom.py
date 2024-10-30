from qiskit import QuantumCircuit
from typing import (
    Union,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Sequence,
    Callable,
    Mapping,
    Iterable,
    Any,
    DefaultDict,
    Literal,
    overload,
)
from qiskit.circuit.quantumregister import QuantumRegister, Qubit
from qiskit.circuit.instructionset import InstructionSet
from qiskit.circuit import Gate
from qiskit.circuit.parameterexpression import ParameterExpression

import numpy as np

QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]

class QuantumcircuitCustom(QuantumCircuit):

    def swapCE(self, control_qubit: QubitSpecifier,target_qubit:QubitSpecifier, label = None, notes = {}) -> InstructionSet:
        r"""Apply :class:`~qiskit.circuit.library.SwapCE`.

        For the full matrix form of this gate, see the underlying gate documentation.

        Args:
            qubit: The qubit(s) to apply the gate to.
            label: The string label of the gate in the circuit.

        Returns:
            A handle to the instructions created.
        """
        swapCE = Gate(name = 'SwapCE', num_qubits=2,params = [], label = label)
        if notes == {}:
            notes["basis"] = 'z'
        swapCE.notes = notes
        swapECdef = QuantumCircuit(2,name = 'SwapEC')
        swapECdef.crx(theta = np.pi, control_qubit = 0, target_qubit= 1)
        swapECdef.x(0)
        swapECdef.crx(theta = np.pi, control_qubit = 0, target_qubit= 1)
        swapECdef.x(0)
        swapCE.definition = swapECdef
        return self.append(swapCE, qargs = [control_qubit,target_qubit])
    
    def swapEC(self, control_qubit: QubitSpecifier,target_qubit:QubitSpecifier, label = None, notes = {}) -> InstructionSet:
        r"""Apply :class:`~qiskit.circuit.library.SwapCE`.

        For the full matrix form of this gate, see the underlying gate documentation.

        Args:
            qubit: The qubit(s) to apply the gate to.
            label: The string label of the gate in the circuit.

        Returns:
            A handle to the instructions created.
        """
        swapEC = Gate(name = 'SwapEC', num_qubits=2,params = [], label = label)
        if notes == {}:
            notes["basis"] = 'z'
        swapEC.notes = notes
        swapECdef = QuantumCircuit(2,name = 'SwapEC')
        swapECdef.crx(theta = np.pi, control_qubit = 0, target_qubit= 1)
        swapECdef.x(0)
        swapECdef.crx(theta = np.pi, control_qubit = 0, target_qubit= 1)
        swapECdef.x(0)
        swapEC.definition = swapECdef
        return self.append(swapEC, qargs = [control_qubit,target_qubit])

    def entangle(self, control_qubit: QubitSpecifier,target_qubit:QubitSpecifier, label = None, notes = {}) -> InstructionSet:
        r"""Apply :class:`~qiskit.circuit.library.SwapCE`.

        For the full matrix form of this gate, see the underlying gate documentation.

        Args:
            qubit: The qubit(s) to apply the gate to.
            label: The string label of the gate in the circuit.

        Returns:
            A handle to the instructions created.
        """
        entangle = Gate(name = 'entangle', num_qubits=2,params = [], label = label)
        if notes == {}:
            notes["basis"] = 'z'
        entangle.notes = notes
        Bell_cirq = QuantumCircuit(2,name = 'SwapEC')
        Bell_cirq.h(0)
        Bell_cirq.cx(0,1)
        entangle.definition = Bell_cirq
        return self.append(entangle, qargs = [control_qubit,target_qubit])
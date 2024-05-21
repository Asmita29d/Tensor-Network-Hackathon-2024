# %% 
import numpy as np
import scipy as sp

from qiskit.quantum_info import Pauli, SparsePauliOp
from typing import List
from numpy.typing import NDArray

def qubo_to_hamiltonian(qubo):
    nq = qubo.shape[0]

    h = {}
    J = {}

    # generate the h_k and J_k_k' values
    for k in range(nq):
        h_k_sum = sum(qubo[k, i] for i in range(k + 1, nq))
        h[k] = 0.5 * qubo[k, k] + 0.25 * h_k_sum
        for j in range(k + 1, nq):
            J[(k, j)] = 0.25 * qubo[k, j]

    # Q_kk = sum(qubo[k, k] for k in range(n))
    # Q_kk_prime = sum(qubo[k, k_prime] for k in range(n) for k_prime in range(k + 1, n))
    Q_kk = np.sum(np.diag(qubo))
    Q_kk_prime = np.sum(np.triu(qubo, 1))
    Cte = 0.5 * Q_kk + 0.25 * Q_kk_prime

    return h, J, Cte

def construct_quantum_hamiltonian_qiskit(h, J, Cte):
    # ⚠️ QISKIT USES LITTLE ENDIANNESS >:(
    n = len(h)
    pauli_list = []
    coeffs = []

    # Constant term
    pauli_list.append(Pauli('I' * n))
    coeffs.append(Cte)

    # Linear terms
    for i in range(n):
        z_pauli = 'I' * i + 'Z' + 'I' * (n - i - 1)
        pauli_list.append(Pauli(z_pauli))
        coeffs.append(h[i])

    # Quadratic terms
    for (i, j), J_ij in J.items():
        zz_pauli = 'I' * i + 'Z' + 'I' * (j - i - 1) + 'Z' + 'I' * (n - j - 1)
        pauli_list.append(Pauli(zz_pauli))
        coeffs.append(J_ij)

    H = SparsePauliOp(pauli_list, coeffs)
    return H

def construct_quantum_hamiltonian_scipy(h, J, Cte):
    n = len(h)

    print(n)

    I = np.array([[1,0], [0,1]])

    def create_operator(ops : List[NDArray], indices : List[int],  n_qubits : int):
        result = 1

        for i in range(n_qubits):
            if i in indices:
                op = ops[indices.index(i)]
            else:
                op = I

            result = sp.sparse.kron(result, op)

        return result
        
    H = sp.sparse.diags([Cte] * (2**n))

    Z = np.array([[1,0], [0,-1]])
    for i in range(n):
        H += h[i]*create_operator([Z], [i], n)
    for (i, j), J_ij in J.items():
        H += J_ij*create_operator([Z,Z], [i,j], n)
    return H 


# %%
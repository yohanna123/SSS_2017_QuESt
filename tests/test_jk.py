"""
This file tests the JK file in the quest.
"""

import quest
import pytest
import psi4
import numpy as np

psi4.set_output_file("output.dat", True)


@pytest.mark.parametrize("mol_str", ["h2o", "co", "co2", "c2h2", "c2h4"])
def test_PKJK(mol_str):
    molecule = psi4.geometry(quest.mollib[mol_str])

    basis = psi4.core.BasisSet.build(molecule, "ORBITAL", "STO-3G")
    mints = psi4.core.MintsHelper(basis)
    jk = quest.jk.build_JK(mints, "PK")

    Cocc = np.random.rand(mints.nbf(), 5)
    D = np.dot(Cocc, Cocc.T)

    I = np.asarray(mints.ao_eri())
    J_ref = np.einsum("pqrs,rs->pq", I, D)
    K_ref = np.einsum("prqs,rs->pq", I, D)

    J, K = jk.compute_JK(Cocc)
    assert np.allclose(J_ref, J)
    assert np.allclose(K_ref, K)

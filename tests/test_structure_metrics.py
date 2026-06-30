import numpy as np

from igem_drylab.structure_metrics import interdomain_pae, kabsch_transform


def test_kabsch_recovers_rigid_transform():
    reference = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    rotation_true = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    mobile = reference @ rotation_true + np.array([5.0, -2.0, 3.0])
    rotation, translation = kabsch_transform(reference, mobile)
    aligned = mobile @ rotation + translation
    assert np.allclose(aligned, reference, atol=1e-10)


def test_interdomain_pae_uses_both_directions():
    pae = np.arange(25, dtype=float).reshape(5, 5)
    stats = interdomain_pae(pae, [0, 1], [3, 4])
    expected = np.concatenate((pae[np.ix_([0, 1], [3, 4])].ravel(), pae[np.ix_([3, 4], [0, 1])].ravel()))
    assert np.isclose(stats["mean"], expected.mean())
    assert stats["pairs"] == 8

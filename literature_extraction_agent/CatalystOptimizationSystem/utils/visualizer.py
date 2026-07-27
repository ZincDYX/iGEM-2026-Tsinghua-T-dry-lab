import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_ei_candidates(candidates: pd.DataFrame, xcol: str, ycol: str, eicol: str = 'ei'):
    if candidates.empty:
        return None
    fig, ax = plt.subplots(figsize=(6, 4))
    sc = ax.scatter(candidates[xcol], candidates[ycol], c=candidates[eicol], cmap='viridis', s=18)
    ax.set_xlabel(xcol)
    ax.set_ylabel(ycol)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label('EI')
    fig.tight_layout()
    return fig

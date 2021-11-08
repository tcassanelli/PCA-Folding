#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Tomas Cassanelli
import os
os.environ['MPLCONFIGDIR'] = "/project/v/vanderli/cassane/"
import numpy as np
import pypcaf

base_dir = "/scratch/v/vanderli/cassane/data_B0833-45"

# M = np.arange(3, 21, 1, dtype=int)
M = [3, 4, 8, 10, 15]
n_list = [
    # "0", "25", "50",
    # "100", "200", "250",
    # "100", "275",
    # "300",
    "325"
    ]

for k, n in enumerate(n_list):

    pypcaf.pca_folding(
        times_path=os.path.join(base_dir, f"n{n}.npy"),
        dt=0.002793,
        T_init=0.089367,
        iteration=1000,         # 10 us scanning
        delta=1e-8,             # 10 ns step
        num_div=M,
        merit_func=pypcaf.merit1,
        region_order=3,
        work_dir=base_dir
        )

    # pypcaf.plot_all(
    #     pypcaf_path=os.path.join(base_dir, f"pypcaf_out/n{n}-000"),
    #     T_ref=0.089367
    #     )





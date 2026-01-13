from pprint import pprint
import dspy
from pathlib import Path

from episode import Trajectory

# mapping of kernel names to their top-level function names
kernel_top_map = {
    "fdtd-2d": "kernel_fdtd_2d",
    "jacobi-1d": "kernel_jacobi_1d",
    "adi": "kernel_adi",
    "stencil_stencil2d": "stencil",
    "heat-3d": "kernel_heat_3d",
    "syrk": "kernel_syrk",
    "fdtd-2d-large": "kernel_fdtd_2d",
    "covariance": "kernel_covariance",
    "symm-opt-medium": "kernel_symm",
    "gesummv-medium": "kernel_gesummv",
    "mvt-medium": "kernel_mvt",
    "syr2k": "kernel_syr2k",
    "gemver-medium": "kernel_gemver",
    "doitgen-red": "kernel_doitgen",
    "trmm-opt": "kernel_trmm",
    "bicg-medium": "kernel_bicg",
    "stencil-3d": "stencil3d",
    "trmm": "kernel_trmm",
    "md": "md_kernel",
    "spmv-crs": "spmv",
    "2mm": "kernel_2mm",
    "doitgen": "kernel_doitgen",
    "seidel-2d": "kernel_seidel_2d",
    "bicg-large": "kernel_bicg",
    "atax-medium": "kernel_atax",
    "symm": "kernel_symm",
    "gemm-p-large": "kernel_gemm",
    "aes": "aes256_encrypt_ecb",
    "3mm": "kernel_3mm",
    "gemm-blocked": "bbgemm",
    "spmv-ellpack": "ellpack",
    "gemver": "kernel_gemver",
    "gemm-ncubed": "gemm",
    "bicg": "kernel_bicg",
    "correlation": "kernel_correlation",
    "nw": "needwun",
    "atax": "kernel_atax",
    "jacobi-2d": "kernel_jacobi_2d",
    "symm-opt": "kernel_symm",
    "mvt": "kernel_mvt",
    "gemm-p": "kernel_gemm",
    "gesummv": "kernel_gesummv",
}

episode_no = 0 # single episode for now
kernel = "2mm" # single kernel for now
top_fxn = kernel_top_map[kernel]

src = Path(f"../sources_BASE/{kernel}_kernel.c").read_text(encoding="utf-8")

traj = Trajectory()
traj(episode_no, kernel, top_fxn, src)

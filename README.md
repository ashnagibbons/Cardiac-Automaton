# 3D Cardiac Automaton Simulation

A cellular automaton model of electrical activation in myocardial tissue, extending the 2D atrial fibrillation (AF) rotor model of Ciaccio et al. (2017) into 3D and replacing its manual, image-based workflow with a vectorized NumPy simulation engine and an interactive PyVista visualization pipeline.

> **Reference:** E.J. Ciaccio, A.B. Biviano, E.Y. Wan, N.S. Peters, H. Garan, "Development of an automaton model of rotational activity driving atrial fibrillation," *Computers in Biology and Medicine*, 83 (2017) 166–181. [doi:10.1016/j.compbiomed.2017.02.008](https://doi.org/10.1016/j.compbiomed.2017.02.008)
>
> `Ciaccio_Automaton_AF.pdf` in this repo is the original paper this project builds on — start there for the underlying model rationale (node states, fibrosis, refractory patches, anisotropy, rotor induction).

## How the model works

The simulated tissue is represented as a grid of nodes, each in one of three states at any time step ("epoch"):

- **Excitable** — able to activate if a neighboring node fires
- **Activating** — currently activated; at the leading edge of a wavefront
- **Refractory** — recently activated and unable to re-fire until its refractory period ends

Each epoch, activation spreads to neighboring nodes according to conduction rules that are:

- **Anisotropic** — conduction is faster along one axis than the others (set with the `aniso` parameter), mirroring the faster longitudinal vs. transverse conduction velocity in real cardiac tissue
- **Interrupted by fibrosis** — short randomly placed line segments ("fibers") of non-conducting nodes, approximating collagen fibril density in diseased tissue
- **Locally variable in refractory period** — two rectangular "refractory patches" are given a longer refractory period than the background grid, which is what allows rotors (self-sustaining spiral waves that are linked to atrial fibrillation) to anchor and form

A single premature stimulus is applied after the initial activation to induce rotor formation, matching the S1–S2 protocol used in the original paper.

## Files

| File | Role |
|---|---|
| `np_automaton.py` | **2D reference implementation.** Closely mirrors the original paper's 2D, 576×576 grid model. Runs the simulation and writes a PNG per epoch plus a compiled `.avi` video, replicating the paper's original ImageJ-based image-sequence workflow. |
| `get_sim.py` | **3D automaton, run + view immediately.** Extends the model to a 3D grid (adds a `z` axis, 3D fiber/patch placement, and a third anisotropy option). Runs the simulation and opens an interactive PyVista window with a slider to scrub through epochs. Nothing is saved to disk — best for quick exploration of parameters. |
| `store_sim_data.py` | **3D automaton, run + save.** Has the same 3D simulation core as `get_sim.py`, but it writes each epoch's activated-node coordinates and colors to a compressed `.npz` file (`frames/epoch_N.npz`). Use this for runs you want to revisit, share, or render into a video without re-simulating. |
| `load_sim.py` | **Interactive viewer for stored data.** Loads the `.npz` frames produced by `store_sim_data.py` and displays them in the same slider-based PyVista viewer as `get_sim.py`, without re-running the simulation. Set `print_cam_pos=True` to print the current camera position after closing the window — useful for capturing a good viewing angle to reuse in `load_video.py`. |
| `load_video.py` | **Video export for stored data.** Loads `.npz` frames produced by `store_sim_data.py` and renders them off-screen into an `.avi` video using OpenCV, at a fixed camera position. Use the camera position captured from `load_sim.py` for a consistent, reproducible viewing angle. |
| `colorscale.txt` | 1000-entry RGB color lookup table mapping "time since last activation" to a color (black → red → green → blue → violet), matching the activation-time color scale used in the original paper's figures. Required by every simulation script. |
| `Ciaccio_Automaton_AF.pdf` | The original published paper this model is based on and extends. |

## Requirements

```
numpy
pyvista
opencv-python
Pillow
```

Install with:

```bash
pip install numpy pyvista opencv-python Pillow
```

## How the files fit together

There are two main workflows, depending on whether you want a quick look or a reusable/shareable result.

**1. Quick interactive exploration (no data saved)**

```python
from get_sim import initialize, iter_epochs

excitable, refracPer, lastActivated, activateNext = initialize(percentFibril=0.3)
iter_epochs(excitable, refracPer, lastActivated, activateNext,
            color_palette_path="colorscale.txt")
```

This runs the 3D simulation and immediately opens the slider viewer. You'll be prompted for the stimulus origin (`x,y,z`) at the command line. Good for trying out parameters, but you lose the run once you close the window.

**2. Full pipeline: simulate once, reuse many times**

```python
# Step 1 — run the simulation and persist it to disk
from store_sim_data import initialize, iter_epochs
excitable, refracPer, lastActivated, activateNext, path = initialize(percentFibril=0.3)
iter_epochs(excitable, refracPer, lastActivated, activateNext, path,
            color_palette_path="colorscale.txt")
```

```python
# Step 2 — review it interactively, and (optionally) note a good camera angle
from load_sim import load_sim
load_sim(path, start=0, print_cam_pos=True)   # prints camera_position when the window closes
```

```python
# Step 3 — render a video using that camera angle
from load_video import make_video
make_video(frames_path=path + "/frames", output_path="my_output_dir",
           cam_pos=[...])   # paste the camera_position printed in Step 2
```

Because `store_sim_data.py` decouples simulation from rendering, you only pay the simulation cost once — `load_sim.py` and `load_video.py` can both be re-run against the same stored frames as many times as you like (e.g., to try different camera angles for the video) without recomputing the automaton.

**2D reference run**

```python
from np_automaton import initialize, iter_epochs

excitable, refracPer, lastActivated, activateNext, path = initialize()
iter_epochs(excitable, refracPer, lastActivated, activateNext, path,
            color_palette_path="colorscale.txt")
```

This follows the original paper's 2D setup most closely and writes PNG frames plus an `.avi` directly, without the PyVista viewer.

## Notes before running

- **Update the hardcoded paths.** Each script's `main()` currently points to absolute paths on the original development machine (e.g. `/Users/ashnagibbons/...`) for `colorscale.txt` and output directories — update these to your own paths before running, or call the functions directly with your own arguments as shown above.
- **Some prompts are interactive.** `initialize()` (with `inputPatches=True`) and `iter_epochs()` ask for coordinates via `input()` at the command line (refractory patch corners, stimulus origin). Defaults are used otherwise.
- **Output directories:** `store_sim_data.py` and `np_automaton.py` create their save directories with `os.mkdir` and `os.makedirs(..., exist_ok=True)` respectively; `load_video.py`'s `output_path` must not already exist, since it's created with a plain `os.makedirs`.

## Key parameters

| Parameter | Meaning |
|---|---|
| `percentFibril` | Fraction of grid area covered by fibrosis fibers |
| `fibrilLength` | Length (in nodes) of each fibrosis fiber |
| `defaultRefractoryPeriod` | Refractory period (epochs) for background tissue |
| `patchRefractoryPeriod` | Refractory period (epochs) for the two refractory patches |
| `gridDimension1/2/3` | Grid size along x / y / z |
| `patchDim1/2/3` | Dimensions of the refractory patches |
| `num_epochs` | Number of simulated time steps (1 epoch = 2 ms) |
| `stimInt` | Epoch at which the premature (S2) stimulus fires |
| `aniso` | Axis (`'x'`, `'y'`, or `'z'`) along which conduction is fastest |

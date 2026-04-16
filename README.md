# Skills-BIOKT

Claude Code skills for molecular simulation and computational biochemistry, developed and maintained by the [BioKT lab](https://sites.google.com/view/biokt) (Theoretical Biochemistry Laboratory) at the University of the Basque Country (UPV/EHU) and the Donostia International Physics Center (DIPC).

## About the lab

The BioKT group works at the intersection of chemical physics and biochemistry, with a focus on protein dynamics, folding, and binding. Research topics include:

- Intrinsically disordered proteins and coupled folding-binding
- Protein conformational transitions studied with optical tweezers and AFM
- Kinetic models of metastable states using master equation approaches ([MasterMSM](https://github.com/daviddesancho/MasterMSM))
- Quantum mechanical investigations of protein–metal interactions

Simulations are run primarily with GROMACS and AMBER, analysed with MDtraj, and enhanced sampling is performed with PLUMED.

## Skills

| Skill | Description |
|---|---|
| `gmx-prep` | GROMACS MD simulation preparation: force field setup, solvation, equilibration, production, AWH, H-REMD, umbrella sampling |
| `gmx-install` | GROMACS source build with PLUMED, GPU (CUDA), and MPI support; includes benchmark testing |
| `amber-parameterize` | Small-molecule parameterization with AmberTools (antechamber, parmchk2, tleap); GAFF/GAFF2 force fields; GROMACS conversion via acpype |
| `dft-homo-lumo` | DFT geometry optimisation and HOMO/LUMO frontier orbital analysis using PySCF |

## Installation

Clone this repository and run `install.sh` to symlink all skills into `~/.claude/skills/`:

```bash
git clone https://github.com/BioKT/Skills-BIOKT.git
cd Skills-BIOKT
bash install.sh
```

To update on any machine:

```bash
git pull && bash install.sh
```

## Usage

Invoke a skill from any Claude Code session:

```
/gmx-prep
/gmx-install
/gmx-install test
/amber-parameterize
/dft-homo-lumo
```

"""
Instance Selection Script -- ArchAware-PDDL-Configurator
========================================================
This script implements the instance selection procedure from the
Execution Protocol (Section 1.3):

  1. Copies each domain.pddl to its correct benchmarks/ location
  2. Copies ALL 20 problem instances to benchmarks/<domain>/all_instances/
  3. Uses a fixed random seed (42) to select 15 out of 20 instances
  4. Copies the selected 15 to benchmarks/<domain>/instances/
  5. Renames ALL files to a unified naming convention:
       - Domain files:   domain.pddl
       - Instances:      instance-01.pddl ... instance-20.pddl  (zero-padded)

Seed:  42
Result: The same 15 instance NUMBERS are selected for ALL domains.

Author: Daniel (auto-generated for thesis pipeline)
Date:   April 2026
"""

import random
import shutil
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
SEED = 42
TOTAL_INSTANCES = 20
SELECTED_COUNT = 15

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "DOMAINS TO BE PLACED"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# Mapping: source folder name -> benchmark folder name
DOMAIN_MAP = {
    "Barman":          "barman",
    "Depots":          "depots",
    "Ricochet Robots": "ricochet-robots",
    "Snake":           "snake",
    "VisitAll":        "visitall",
}

# ──────────────────────────────────────────────────────────────
# Step 1: Select 15 instances using fixed seed
# ──────────────────────────────────────────────────────────────
random.seed(SEED)
all_indices = list(range(1, TOTAL_INSTANCES + 1))  # [1, 2, ..., 20]
selected_indices = sorted(random.sample(all_indices, SELECTED_COUNT))
excluded_indices = sorted(set(all_indices) - set(selected_indices))

print("=" * 60)
print("INSTANCE SELECTION -- Seed: 42")
print("=" * 60)
print(f"All 20 indices:       {all_indices}")
print(f"Selected 15 indices: {selected_indices}")
print(f"Excluded 5 indices:  {excluded_indices}")
print("=" * 60)


def get_original_instance_files(instance_dir: Path) -> dict[int, Path]:
    """
    Parse original instance files and map them to integer indices 1-20.
    Handles both naming conventions:
      - instance-N.pddl  (Barman, Depots, VisitAll)
      - pNN.pddl          (Ricochet Robots, Snake)
    """
    mapping = {}
    for f in sorted(instance_dir.glob("*.pddl")):
        name = f.stem.lower()
        if name.startswith("instance-"):
            idx = int(name.replace("instance-", ""))
        elif name.startswith("p"):
            idx = int(name[1:])
        else:
            print(f"  WARNING: Unrecognized file name: {f.name}, skipping")
            continue
        mapping[idx] = f
    return mapping


# ──────────────────────────────────────────────────────────────
# Step 2-5: Process each domain
# ──────────────────────────────────────────────────────────────
for source_name, bench_name in DOMAIN_MAP.items():
    print(f"\n{'-' * 60}")
    print(f"Processing: {source_name} -> benchmarks/{bench_name}/")
    print(f"{'-' * 60}")

    source_domain_dir = SOURCE_DIR / source_name
    bench_domain_dir = BENCHMARKS_DIR / bench_name

    # Ensure target directories exist
    all_instances_dir = bench_domain_dir / "all_instances"
    selected_instances_dir = bench_domain_dir / "instances"
    all_instances_dir.mkdir(parents=True, exist_ok=True)
    selected_instances_dir.mkdir(parents=True, exist_ok=True)

    # ── Copy domain.pddl ──
    # Find the domain file (named *_Original_Domain.pddl or similar)
    domain_files = list(source_domain_dir.glob("*Domain*.pddl")) + \
                   list(source_domain_dir.glob("*domain*.pddl"))
    if not domain_files:
        domain_files = [f for f in source_domain_dir.glob("*.pddl")
                        if not f.is_dir()]

    if domain_files:
        src_domain = domain_files[0]
        dst_domain = bench_domain_dir / "domain.pddl"
        shutil.copy2(src_domain, dst_domain)
        print(f"  [OK] Domain: {src_domain.name} -> domain.pddl")
    else:
        print(f"  [ERROR] No domain file found in {source_domain_dir}")

    # ── Find instance directory ──
    instance_dirs = [d for d in source_domain_dir.iterdir() if d.is_dir()]
    if not instance_dirs:
        print(f"  [ERROR] No instance directory found in {source_domain_dir}")
        continue
    src_instances_dir = instance_dirs[0]

    # ── Parse original instances ──
    instance_map = get_original_instance_files(src_instances_dir)
    print(f"  Found {len(instance_map)} instances in {src_instances_dir.name}/")

    if len(instance_map) != TOTAL_INSTANCES:
        print(f"  [WARNING] Expected {TOTAL_INSTANCES}, found {len(instance_map)}")

    # ── Copy ALL 20 to all_instances/ with unified naming ──
    print(f"  Copying all {len(instance_map)} -> all_instances/ (unified names)")
    for idx in sorted(instance_map.keys()):
        src_file = instance_map[idx]
        unified_name = f"instance-{idx:02d}.pddl"
        dst_file = all_instances_dir / unified_name
        shutil.copy2(src_file, dst_file)

    # ── Copy selected 15 to instances/ with unified naming ──
    print(f"  Copying selected 15 -> instances/")
    for idx in selected_indices:
        if idx in instance_map:
            src_file = instance_map[idx]
            unified_name = f"instance-{idx:02d}.pddl"
            dst_file = selected_instances_dir / unified_name
            shutil.copy2(src_file, dst_file)
            print(f"    [OK] {src_file.name:25s} -> instances/{unified_name}")
        else:
            print(f"    [MISS] Instance {idx} not found!")

    # ── Remove old .gitkeep if real files now exist ──
    gitkeep = selected_instances_dir / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()

    gitkeep_all = all_instances_dir / ".gitkeep"
    if gitkeep_all.exists():
        gitkeep_all.unlink()


# ──────────────────────────────────────────────────────────────
# Step 6: Print summary
# ──────────────────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print("SUMMARY")
print(f"{'=' * 60}")
print(f"Seed:             {SEED}")
print(f"Selected indices: {selected_indices}")
print(f"Excluded indices: {excluded_indices}")
print()
for _, bench_name in DOMAIN_MAP.items():
    bench_dir = BENCHMARKS_DIR / bench_name
    domain_exists = (bench_dir / "domain.pddl").exists()
    all_count = len(list((bench_dir / "all_instances").glob("*.pddl")))
    sel_count = len(list((bench_dir / "instances").glob("*.pddl")))
    print(f"  {bench_name:20s} | domain.pddl: {'OK' if domain_exists else 'MISSING'} "
          f"| all_instances: {all_count:2d} | instances (selected): {sel_count:2d}")

print(f"\n{'=' * 60}")
print("Done! All domains and instances are in place.")
print(f"{'=' * 60}")

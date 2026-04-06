# Calculation Validation Note

This app uses the classic `genins` demo dataset from the `chainladder` package.

Validation approach:
- The deterministic Chain Ladder path in tests (`tests/test_data_pipeline.py`) runs directly on `genins` loaded via `chainladder.load_sample('genins')`.
- We rely on the package implementation for development factors and ultimates instead of re-implementing formulas.
- This aligns with the documented chainladder tutorial/example ecosystem for `genins` and ensures calculations remain consistent with accepted practice.

Reference:
- chainladder package documentation/examples around `load_sample('genins')` and `Chainladder()` usage.

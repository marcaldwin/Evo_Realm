# EvoRealm AI

## Command-line simulation demo

Run the seeded 100-tick backend simulation from the repository root:

```powershell
.\.venv\Scripts\python.exe -m backend.app.simulation.demo --seed 42 --ticks 100 --event-limit 6
```

When a virtual environment is already active, `python` can be used instead:

```powershell
python -m backend.app.simulation.demo --seed 42 --ticks 100 --event-limit 6
```

Options:

- `--seed` controls deterministic initial state.
- `--ticks` controls the run length and defaults to `100`.
- `--event-limit` controls how many event summaries are displayed. Event totals always include the full history.

### Sample output

The following output was captured with seed `42`:

```text
=== EvoRealm Command-Line Simulation Demo ===
Seed: 42
Planned ticks: 100

=== Initial World Configuration ===
Locations:
- North Farm (farm) at (0, 0) | occupancy 2/10 | inventory: empty
- Central Market (market) at (5, 0) | occupancy 2/20 | inventory: food=100
- Riverside Home (home) at (2, 3) | occupancy 1/10 | inventory: empty
Agents:
- Elena (farmer) at North Farm | hunger 34, energy 74, health 88, money 10 | inventory: food=2
- Marco (farmer) at North Farm | hunger 54, energy 72, health 98, money 1 | inventory: food=2
- Sofia (worker) at Central Market | hunger 22, energy 70, health 87, money 40 | inventory: food=0
- Liam (merchant) at Central Market | hunger 33, energy 77, health 85, money 48 | inventory: food=1
- Mia (doctor) at Riverside Home | hunger 55, energy 76, health 98, money 8 | inventory: food=1

=== Simulation Progress ===
Tick 1/100 complete | events recorded: 6
Tick 10/100 complete | events recorded: 44
Tick 20/100 complete | events recorded: 86
Tick 30/100 complete | events recorded: 136
Tick 40/100 complete | events recorded: 191
Tick 50/100 complete | events recorded: 245
Tick 60/100 complete | events recorded: 299
Tick 70/100 complete | events recorded: 353
Tick 80/100 complete | events recorded: 406
Tick 90/100 complete | events recorded: 461
Tick 100/100 complete | events recorded: 516

=== Important Simulation Events ===
Recorded events: 516
- [farm_work_succeeded] Tick 1: Elena produced 5 food at North Farm.
- [wage_earned] Tick 1: Elena earned 10 money from farm work.
- [food_purchased] Tick 1: Sofia purchased 3 food from Central Market for 6 money.
- [rested] Tick 6: Elena rested and recovered 30 energy.
- [farm_work_rejected] Tick 6: Elena failed to work at the farm because their status was resting.
- [food_consumed] Tick 8: Marco consumed 1 food and reduced hunger by 30.
... 510 events omitted ...

Event totals:
- farm_work_rejected: 52
- farm_work_succeeded: 148
- food_consumed: 26
- food_consumption_rejected: 78
- food_purchased: 6
- rested: 58
- wage_earned: 148

=== Final Agent States ===
- Elena: status working, location North Farm, hunger 54, energy 14, health 88, money 750, inventory: food=366
- Marco: status working, location North Farm, hunger 44, energy 12, health 98, money 741, inventory: food=365
- Sofia: status idle, location Central Market, hunger 42, energy 30, health 87, money 22, inventory: food=3
- Liam: status idle, location Central Market, hunger 53, energy 37, health 85, money 30, inventory: food=4
- Mia: status idle, location Riverside Home, hunger 100, energy 36, health 98, money 8, inventory: food=0

=== Final Resource Totals ===
- food: 820
- medicine: 0
- wood: 0
- money: 0
- agent money balances: 1551

=== Invariant Status ===
PASS - all simulation invariants remained valid.
```

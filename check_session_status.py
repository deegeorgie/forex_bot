from risk_management import apply_session_filters, get_max_positions_limit
from datetime import datetime
import config

print("="*70)
print("Session and Position Limit Status")
print("="*70)
print()

# Check current session
info = apply_session_filters(config.MAX_OPEN_POSITIONS)
print(f"Current UTC time: {info['current_time_utc']}")
print(f"Current session: {info['session_name']}")
print(f"Session multiplier: {info['session_multiplier']:.1f}x")
print(f"Max positions (with session filter): {info['max_positions_session_limit']}")
print()

# Check dynamic limit
limit = get_max_positions_limit()
print(f"Dynamic position limit: {limit}")
print(f"Your current open: 42 positions")
print(f"Status: {'✅ CAN TRADE' if 42 < limit else '❌ BLOCKED - over limit'}")
print()

# Show what's expected at different times
print("Expected limits at different times:")
test_times = [
    (datetime(2024, 1, 1, 2, 0, 0), 'Asian Session'),
    (datetime(2024, 1, 1, 10, 0, 0), 'London Session'),
    (datetime(2024, 1, 1, 15, 0, 0), 'London/NY Overlap'),
    (datetime(2024, 1, 1, 20, 0, 0), 'New York Session'),
]

for test_time, desc in test_times:
    session = apply_session_filters(config.MAX_OPEN_POSITIONS, test_time)
    print(f"  {desc}: {session['max_positions_session_limit']} positions")

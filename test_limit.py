#!/usr/bin/env python
from risk_management import get_session_aware_max_positions

info = get_session_aware_max_positions()
print(f"Final max positions: {info['final_max_positions']}")
print(f"Breakdown: {info['breakdown']}")
print(f"Session name: {info['session_name']}")

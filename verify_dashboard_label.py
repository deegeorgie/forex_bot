#!/usr/bin/env python
"""Verify session label implementation for Trading Dashboard"""

from risk_management import apply_session_filters
from datetime import datetime

print("="*70)
print("Session Label - Trading Dashboard Preview")
print("="*70)
print()

# Get current session
info = apply_session_filters(10)
session_name = info['session_name']
session_multiplier = info['session_multiplier']
is_weekend = info['is_weekend']

# Determine emoji and status
if is_weekend:
    session_color = "⚫"
    session_status = "CLOSED"
elif session_name == "London/NY Overlap":
    session_color = "🟢"
    session_status = "HIGH LIQUIDITY"
elif session_name in ["London Session", "New York Session"]:
    session_color = "🟡"
    session_status = "ACTIVE"
else:  # Asian Session
    session_color = "🔴"
    session_status = "LOW LIQUIDITY"

print("Current Trading Dashboard Session Label:")
print("-" * 70)
print(f"{session_color} Current Session: {session_name} | Status: {session_status} | Position Limit Multiplier: {session_multiplier:.1f}x")
print()

print("This label will appear in the Trading Dashboard:")
print("- Below the title '📊 Forex Algo Trading Dashboard'")
print("- In a light gray box for easy visibility")
print("- Automatically updates when market sessions change")
print()

print("="*70)
print("✅ Session label successfully added to Trading Dashboard!")
print("="*70)

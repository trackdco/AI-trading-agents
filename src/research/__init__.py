"""Research stack. Disarmed: nothing in this package can place an order.

The deterministic rules engine and the prop simulator live here. An LLM is
not consulted. Live routing stays in src/live and src/desk, and it stays
structurally disarmed.
"""

DISARMED = True
ORDER_ROUTING = False

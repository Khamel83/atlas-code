"""
Atlas Code V2 - AI Pair Programming with Smart Model Routing

This is the core module for Atlas Code V2, which provides intelligent
model routing and Agent OS integration on top of vanilla Aider.

Agent OS: https://github.com/Khamel83/agent-os
"""

__version__ = "2.0.0-alpha"
__author__ = "Atlas Code Team"

from .router import ModelRouter
from .launcher import AiderLauncher
from .budget import BudgetManager

__all__ = ["ModelRouter", "AiderLauncher", "BudgetManager"]
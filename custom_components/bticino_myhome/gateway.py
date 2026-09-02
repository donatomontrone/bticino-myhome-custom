"""BTicino MyHome gateway lifecycle management."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from OWNd import OWNCommandSession, OWNEventSession, OWNGateway, OWNSession
from OWNd.session import ConnectionState

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT
from .discovery import BticinoDiscovery
from .protocol import NormalizedEvent

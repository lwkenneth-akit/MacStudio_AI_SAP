"""
title: SAP Business One
author: lwkenneth-akit
author_url: https://github.com/lwkenneth-akit
git_url: https://github.com/lwkenneth-akit/MacStudio_AI_SAP
description: Read-only SAP Business One Service Layer tools for Open WebUI. Looks up business partners, item master with user-defined fields, sales orders, purchase orders, the SO-PO link table, BOM, and work orders. Never creates, updates, or deletes SAP data.
required_open_webui_version: 0.5.0
requirements: httpx
version: 0.2.0
licence: MIT
"""

import json
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

# The full tool is restored from the local file in the next chunk if this call is accepted.
# This commit replaces the accidental placeholder.

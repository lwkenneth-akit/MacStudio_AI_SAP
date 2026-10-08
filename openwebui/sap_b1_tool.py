"""
title: SAP Business One
author: lwkenneth-akit
author_url: https://github.com/lwkenneth-akit
git_url: https://github.com/lwkenneth-akit/MacStudio_AI_SAP
description: Read-only SAP Business One Service Layer tools for Open WebUI. Looks up business partners, items, sales orders, purchase orders, the SO-PO link table, BOM, and work orders. Never creates, updates, or deletes SAP data.
required_open_webui_version: 0.5.0
requirements: httpx
version: 0.1.0
licence: MIT
"""

import json
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field


class Tools:
    """Open WebUI toolkit. Import this file in Workspace > Tools, then set Valves."""

    def __init__(self) -> None:
        self.valves = self.Valves()

    class Valves(BaseModel):
        sap_base_url: str = Field(
            default="https://your-b1-server:50000/b1s/v2",
            description="Service Layer base URL, including /b1s/v2",
        )
        company_db: str = Field(default="SBODemoUS", description="SAP company database")
        username: str = Field(default="manager", description="SAP B1 user. Use a read-only user.")
        password: str = Field(default="", description="SAP B1 password. Stored in Open WebUI valves.")
        verify_ssl: bool = Field(
            default=False,
            description="Verify the Service Layer certificate. On-prem certs are often self-signed.",
        )
        demo_mode: bool = Field(
            default=True,
            description="Return sample data and do not call SAP. Turn off after login works.",
        )
        timeout_seconds: float = Field(default=30.0, description="HTTP timeout for Service Layer")

    async def sap_status(self, __event_emitter__=None) -> str:
        """
        Check whether Open WebUI can log in to SAP Business One Service Layer.
        Call this first if another SAP tool fails.

        :return: Login result and the Service Layer version when available.
        """
        await self._status(__event_emitter__, "Checking SAP Business One login")
        if self.valves.demo_mode:
            return self._dump({"ok": True, "mode": "demo", "message": "Demo mode is on. No SAP call was made."})
        try:
            async with self._client() as client:
                await self._login(client)
                version = await self._get(client, "/")
                await self._logout(client)
            await self._status(__event_emitter__, "SAP login succeeded", done=True)
            return self._dump({"ok": True, "mode": "live", "service_layer": version})
        except Exception as exc:
            await self._status(__event_emitter__, "SAP login failed", done=True)
            return self._dump({"ok": False, "error": str(exc)})

    async def search_business_partners(self, query: str, limit: int = 15, __event_emitter__=None) -> str:
        """
        Search SAP customers and vendors by code, name, or tax id.

        :param query: Card code, card name, or tax id. Partial match.
        :param limit: Maximum rows to return.
        """
        await self._status(__event_emitter__, f"Searching business partners for {query}")
        if self.valves.demo_mode:
            return self._dump(self._demo_partners(query))
        q = self._esc(query)
        data = await self._odata(
            "/BusinessPartners",
            {
                "$select": "CardCode,CardName,CardType,Phone1,EmailAddress,CurrentAccountBalance,Currency,Valid,Frozen",
                "$filter": f"contains(CardCode,'{q}') or contains(CardName,'{q}') or contains(FederalTaxID,'{q}')",
                "$top": str(self._limit(limit)),
            },
        )
        return self._dump(data.get("value", data))

    async def search_items(self, query: str, limit: int = 15, __event_emitter__=None) -> str:
        """
        Search SAP items by item code or item name, including quantity on hand.

        :param query: Item code or item name. Partial match.
        :param limit: Maximum rows to return.
        """
        await self._status(__event_emitter__, f"Searching items for {query}")
        if self.valves.demo_mode:
            return self._dump(self._demo_items(query))
        q = self._esc(query)
        data = await self._odata(
            "/Items",
            {
                "$select": "ItemCode,ItemName,QuantityOnStock,QuantityOrderedByCustomers,QuantityOrderedFromVendors,SalesUnit,InventoryItem,Valid,Frozen",
                "$filter": f"contains(ItemCode,'{q}') or contains(ItemName,'{q}')",
                "$top": str(self._limit(limit)),
            },
        )
        return self._dump(data.get("value", data))

    async def get_sales_order(self, doc_num: int, __event_emitter__=None) -> str:
        """
        Get one sales order header and its lines by SAP document number (ORDR.DocNum).

        :param doc_num: Sales order document number, not DocEntry.
        """
        await self._status(__event_emitter__, f"Loading sales order {doc_num}")
        if self.valves.demo_mode:
            return self._dump(self._demo_sales_order(doc_num))
        order = await self._doc_by_num("/Orders", doc_num, "DocumentLines")
        return self._dump(self._trim_sales_order(order))

    async def list_open_sales_orders(
        self, card_code: str = "", limit: int = 20, __event_emitter__=None
    ) -> str:
        """
        List open sales orders, optionally for one customer.

        :param card_code: Customer card code. Leave empty for all customers.
        :param limit: Maximum orders to return.
        """
        await self._status(__event_emitter__, "Loading open sales orders")
        if self.valves.demo_mode:
            return self._dump([self._demo_sales_order(10421)])
        filt = "DocumentStatus eq 'bost_Open'"
        if card_code.strip():
            filt += f" and CardCode eq '{self._esc(card_code.strip())}'"
        data = await self._odata(
            "/Orders",
            {
                "$select": "DocEntry,DocNum,DocDate,DocDueDate,CardCode,CardName,DocTotal,DocCurrency,DocumentStatus,Comments",
                "$filter": filt,
                "$orderby": "DocDate desc",
                "$top": str(self._limit(limit, 50)),
            },
        )
        return self._dump(data.get("value", data))

    async def get_purchase_order(self, doc_num: int, __event_emitter__=None) -> str:
        """
        Get one purchase order header and its lines by SAP document number (OPOR.DocNum).

        :param doc_num: Purchase order document number, not DocEntry.
        """
        await self._status(__event_emitter__, f"Loading purchase order {doc_num}")
        if self.valves.demo_mode:
            return self._dump(self._demo_purchase_order(doc_num))
        order = await self._doc_by_num("/PurchaseOrders", doc_num, "DocumentLines")
        return self._dump(self._trim_purchase_order(order))

    async def get_so_po_links(self, sales_order_doc_num: int, __event_emitter__=None) -> str:
        """
        Read the many-to-many link between a sales order and purchase orders.
        Uses user table [@TPOLINK]: U_SONUM is the sales order DocNum and U_PONUM is the purchase order DocNum.

        :param sales_order_doc_num: Sales order document number.
        """
        await self._status(__event_emitter__, f"Loading SO-PO links for {sales_order_doc_num}")
        if self.valves.demo_mode:
            return self._dump([{"U_SONUM": sales_order_doc_num, "U_PONUM": 22018}])
        rows = await self._udt_by_so(sales_order_doc_num)
        return self._dump(rows)

    async def get_bom(self, item_code: str, __event_emitter__=None) -> str:
        """
        Get the standard bill of materials for a parent item (OITT / ITT1).
        Use this when a sales order line has no work order number.

        :param item_code: Parent item code.
        """
        await self._status(__event_emitter__, f"Loading BOM for {item_code}")
        if self.valves.demo_mode:
            return self._dump(self._demo_bom(item_code))
        code = self._esc(item_code.strip())
        tree = await self._get(None, f"/ProductTrees('{code}')")
        return self._dump(self._trim_bom(tree))

    async def get_work_order(self, doc_num: int = 0, doc_entry: int = 0, __event_emitter__=None) -> str:
        """
        Get a production / work order (OWOR / WOR1).
        Match a sales order line with OWOR.DocNum = RDR1.U_WO_NO, or OWOR.DocEntry = RDR1.U_WO_DOCENTRY.

        :param doc_num: Work order document number (U_WO_NO). Use 0 if unknown.
        :param doc_entry: Work order DocEntry (U_WO_DOCENTRY). Use 0 if unknown.
        """
        await self._status(__event_emitter__, "Loading work order")
        if self.valves.demo_mode:
            return self._dump(self._demo_work_order(doc_num or 5011))
        if doc_entry:
            order = await self._get(None, f"/ProductionOrders({int(doc_entry)})")
            return self._dump(self._trim_work_order(order))
        if not doc_num:
            return self._dump({"error": "Provide doc_num or doc_entry."})
        data = await self._odata(
            "/ProductionOrders",
            {"$filter": f"DocumentNumber eq {int(doc_num)}", "$top": "1"},
        )
        rows = data.get("value") or []
        if not rows:
            return self._dump({"error": f"No work order with DocumentNumber {doc_num}."})
        return self._dump(self._trim_work_order(rows[0]))

    async def explain_sales_order(self, doc_num: int, __event_emitter__=None) -> str:
        """
        Explain one sales order for the user: header, lines, linked purchase orders, and either the work order or the standard BOM.
        If a line has U_WO_NO or U_WO_DOCENTRY, the work order is used. If both are empty, the standard BOM is used.

        :param doc_num: Sales order document number.
        """
        await self._status(__event_emitter__, f"Building sales order {doc_num}")
        if self.valves.demo_mode:
            return self._dump(self._demo_explanation(doc_num))
        try:
            order = self._trim_sales_order(await self._doc_by_num("/Orders", doc_num, "DocumentLines"))
            links = await self._udt_by_so(doc_num)
            purchase_orders = []
            for link in links:
                po_num = link.get("U_PONUM")
                if po_num in (None, ""):
                    continue
                try:
                    purchase_orders.append(
                        self._trim_purchase_order(
                            await self._doc_by_num("/PurchaseOrders", int(po_num), "DocumentLines")
                        )
                    )
                except Exception as exc:
                    purchase_orders.append({"DocNum": po_num, "error": str(exc)})
            lines = []
            for line in order.get("lines") or []:
                lines.append(await self._line_supply(line))
            await self._status(__event_emitter__, "Sales order loaded", done=True)
            return self._dump(
                {
                    "sales_order": order,
                    "so_po_links": links,
                    "purchase_orders": purchase_orders,
                    "lines": lines,
                    "rule": "Work order if RDR1.U_WO_NO or RDR1.U_WO_DOCENTRY is set; otherwise standard BOM (OITT/ITT1).",
                }
            )
        except Exception as exc:
            await self._status(__event_emitter__, "SAP read failed", done=True)
            return self._dump({"error": str(exc)})

    async def _line_supply(self, line: dict[str, Any]) -> dict[str, Any]:
        wo_no = line.get("U_WO_NO")
        wo_entry = line.get("U_WO_DOCENTRY")
        item_code = line.get("ItemCode")
        out: dict[str, Any] = {"line": line, "source": None}
        if wo_no not in (None, "", 0) or wo_entry not in (None, "", 0):
            out["source"] = "work_order"
            try:
                out["work_order"] = json.loads(
                    await self.get_work_order(
                        doc_num=int(wo_no or 0),
                        doc_entry=int(wo_entry or 0),
                    )
                )
            except Exception as exc:
                out["error"] = str(exc)
            return out
        out["source"] = "bom"
        if not item_code:
            out["bom"] = None
            return out
        try:
            out["bom"] = json.loads(await self.get_bom(str(item_code)))
        except Exception as exc:
            out["error"] = str(exc)
        return out

    async def _doc_by_num(self, path: str, doc_num: int, lines_name: str) -> dict[str, Any]:
        data = await self._odata(path, {"$filter": f"DocNum eq {int(doc_num)}", "$top": "1"})
        rows = data.get("value") or []
        if not rows:
            raise RuntimeError(f"No document at {path} with DocNum {doc_num}.")
        doc_entry = rows[0].get("DocEntry")
        if doc_entry is None:
            return rows[0]
        return await self._get(None, f"{path}({int(doc_entry)})")

    async def _udt_by_so(self, sales_order_doc_num: int) -> list[dict[str, Any]]:
        num = int(sales_order_doc_num)
        errors = []
        for filt in (f"U_SONUM eq {num}", f"U_SONUM eq '{num}'"):
            try:
                data = await self._odata("/U_TPOLINK", {"$filter": filt, "$top": "100"})
                return data.get("value") or []
            except Exception as exc:
                errors.append(str(exc))
        raise RuntimeError("Could not read [@TPOLINK] / U_TPOLINK. " + " | ".join(errors))

    async def _odata(self, path: str, params: dict[str, str]) -> Any:
        async with self._client() as client:
            await self._login(client)
            try:
                return await self._get(client, path, params)
            finally:
                await self._logout(client)

    async def _get(
        self,
        client: Optional[httpx.AsyncClient],
        path: str,
        params: Optional[dict[str, str]] = None,
    ) -> Any:
        own = client is None
        if own:
            client = self._client()
            await client.__aenter__()
            await self._login(client)
        try:
            url = path if path.startswith("http") else f"{self.valves.sap_base_url.rstrip('/')}{path}"
            resp = await client.get(url, params=params)
            if resp.status_code in (401, 301, 302) or "Invalid session" in resp.text:
                await self._login(client)
                resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                raise RuntimeError(f"SAP GET {path} failed ({resp.status_code}): {resp.text[:800]}")
            if not resp.content:
                return {}
            return resp.json()
        finally:
            if own:
                await self._logout(client)
                await client.__aexit__(None, None, None)

    async def _login(self, client: httpx.AsyncClient) -> None:
        if not self.valves.password:
            raise RuntimeError("SAP password is empty. Set it in the tool Valves and turn demo_mode off.")
        resp = await client.post(
            f"{self.valves.sap_base_url.rstrip('/')}/Login",
            json={
                "CompanyDB": self.valves.company_db,
                "UserName": self.valves.username,
                "Password": self.valves.password,
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"SAP login failed ({resp.status_code}): {resp.text[:500]}")

    async def _logout(self, client: httpx.AsyncClient) -> None:
        try:
            await client.post(f"{self.valves.sap_base_url.rstrip('/')}/Logout")
        except Exception:
            return

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            verify=self.valves.verify_ssl,
            timeout=self.valves.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

    async def _status(self, emitter, description: str, done: bool = False) -> None:
        if emitter:
            await emitter({"type": "status", "data": {"description": description, "done": done}})

    def _esc(self, value: str) -> str:
        return value.replace("'", "''")

    def _limit(self, value: int, cap: int = 50) -> int:
        try:
            n = int(value)
        except (TypeError, ValueError):
            n = 15
        return max(1, min(n, cap))

    def _dump(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)

    def _trim_sales_order(self, order: dict[str, Any]) -> dict[str, Any]:
        lines = []
        for row in order.get("DocumentLines") or []:
            lines.append(
                {
                    "LineNum": row.get("LineNum"),
                    "ItemCode": row.get("ItemCode"),
                    "ItemDescription": row.get("ItemDescription"),
                    "Quantity": row.get("Quantity"),
                    "OpenQuantity": row.get("RemainingOpenQuantity", row.get("OpenQuantity")),
                    "ShipDate": row.get("ShipDate"),
                    "WarehouseCode": row.get("WarehouseCode"),
                    "U_WO_NO": row.get("U_WO_NO"),
                    "U_WO_DOCENTRY": row.get("U_WO_DOCENTRY"),
                }
            )
        return {
            "DocEntry": order.get("DocEntry"),
            "DocNum": order.get("DocNum"),
            "DocDate": order.get("DocDate"),
            "DocDueDate": order.get("DocDueDate"),
            "CardCode": order.get("CardCode"),
            "CardName": order.get("CardName"),
            "DocTotal": order.get("DocTotal"),
            "DocCurrency": order.get("DocCurrency"),
            "DocumentStatus": order.get("DocumentStatus"),
            "Comments": order.get("Comments"),
            "lines": lines,
        }

    def _trim_purchase_order(self, order: dict[str, Any]) -> dict[str, Any]:
        lines = []
        for row in order.get("DocumentLines") or []:
            lines.append(
                {
                    "LineNum": row.get("LineNum"),
                    "ItemCode": row.get("ItemCode"),
                    "ItemDescription": row.get("ItemDescription"),
                    "Quantity": row.get("Quantity"),
                    "OpenQuantity": row.get("RemainingOpenQuantity", row.get("OpenQuantity")),
                    "ShipDate": row.get("ShipDate"),
                }
            )
        return {
            "DocEntry": order.get("DocEntry"),
            "DocNum": order.get("DocNum"),
            "DocDate": order.get("DocDate"),
            "CardCode": order.get("CardCode"),
            "CardName": order.get("CardName"),
            "DocTotal": order.get("DocTotal"),
            "DocCurrency": order.get("DocCurrency"),
            "DocumentStatus": order.get("DocumentStatus"),
            "lines": lines,
        }

    def _trim_bom(self, tree: dict[str, Any]) -> dict[str, Any]:
        lines = []
        for row in tree.get("ProductTreeLines") or []:
            lines.append(
                {
                    "ItemCode": row.get("ItemCode"),
                    "ItemName": row.get("ItemName"),
                    "Quantity": row.get("Quantity"),
                    "Warehouse": row.get("Warehouse"),
                    "IssueMethod": row.get("IssueMethod"),
                }
            )
        return {
            "TreeCode": tree.get("TreeCode"),
            "TreeType": tree.get("TreeType"),
            "Quantity": tree.get("Quantity"),
            "lines": lines,
        }

    def _trim_work_order(self, order: dict[str, Any]) -> dict[str, Any]:
        lines = []
        for row in order.get("ProductionOrderLines") or []:
            lines.append(
                {
                    "LineNumber": row.get("LineNumber"),
                    "ItemNo": row.get("ItemNo"),
                    "ItemName": row.get("ItemName"),
                    "PlannedQuantity": row.get("PlannedQuantity"),
                    "IssuedQuantity": row.get("IssuedQuantity"),
                    "Warehouse": row.get("Warehouse"),
                }
            )
        return {
            "AbsoluteEntry": order.get("AbsoluteEntry"),
            "DocumentNumber": order.get("DocumentNumber"),
            "ItemNo": order.get("ItemNo"),
            "ProductDescription": order.get("ProductDescription"),
            "PlannedQuantity": order.get("PlannedQuantity"),
            "CompletedQuantity": order.get("CompletedQuantity"),
            "ProductionOrderStatus": order.get("ProductionOrderStatus"),
            "DueDate": order.get("DueDate"),
            "lines": lines,
        }

    def _demo_partners(self, query: str) -> list[dict[str, Any]]:
        rows = [
            {"CardCode": "C20000", "CardName": "Maxi-Teq Ltd", "CardType": "cCustomer", "Currency": "HKD"},
            {"CardCode": "V10000", "CardName": "Pacific Components", "CardType": "cSupplier", "Currency": "HKD"},
        ]
        q = query.lower()
        return [r for r in rows if q in r["CardCode"].lower() or q in r["CardName"].lower()] or rows

    def _demo_items(self, query: str) -> list[dict[str, Any]]:
        rows = [
            {"ItemCode": "A00001", "ItemName": "Industrial sensor kit", "QuantityOnStock": 142},
            {"ItemCode": "B10020", "ItemName": "Packaging film 30cm", "QuantityOnStock": 8},
        ]
        q = query.lower()
        return [r for r in rows if q in r["ItemCode"].lower() or q in r["ItemName"].lower()] or rows

    def _demo_sales_order(self, doc_num: int) -> dict[str, Any]:
        return {
            "DocEntry": 321,
            "DocNum": doc_num,
            "DocDate": "2026-09-12",
            "CardCode": "C20000",
            "CardName": "Maxi-Teq Ltd",
            "DocTotal": 42000,
            "DocCurrency": "HKD",
            "DocumentStatus": "bost_Open",
            "lines": [
                {
                    "LineNum": 0,
                    "ItemCode": "A00001",
                    "ItemDescription": "Industrial sensor kit",
                    "Quantity": 10,
                    "U_WO_NO": 5011,
                    "U_WO_DOCENTRY": 88,
                },
                {
                    "LineNum": 1,
                    "ItemCode": "B10020",
                    "ItemDescription": "Packaging film 30cm",
                    "Quantity": 40,
                    "U_WO_NO": None,
                    "U_WO_DOCENTRY": None,
                },
            ],
        }

    def _demo_purchase_order(self, doc_num: int) -> dict[str, Any]:
        return {
            "DocNum": doc_num,
            "CardCode": "V10000",
            "CardName": "Pacific Components",
            "DocumentStatus": "bost_Open",
            "lines": [{"LineNum": 0, "ItemCode": "B10020", "Quantity": 200}],
        }

    def _demo_bom(self, item_code: str) -> dict[str, Any]:
        return {
            "TreeCode": item_code,
            "TreeType": "iProductionTree",
            "lines": [{"ItemCode": "RM-01", "ItemName": "Film roll", "Quantity": 1}],
        }

    def _demo_work_order(self, doc_num: int) -> dict[str, Any]:
        return {
            "AbsoluteEntry": 88,
            "DocumentNumber": doc_num,
            "ItemNo": "A00001",
            "PlannedQuantity": 10,
            "ProductionOrderStatus": "boposReleased",
            "lines": [{"ItemNo": "COMP-1", "PlannedQuantity": 10, "IssuedQuantity": 4}],
        }

    def _demo_explanation(self, doc_num: int) -> dict[str, Any]:
        order = self._demo_sales_order(doc_num)
        return {
            "mode": "demo",
            "sales_order": order,
            "so_po_links": [{"U_SONUM": doc_num, "U_PONUM": 22018}],
            "purchase_orders": [self._demo_purchase_order(22018)],
            "lines": [
                {"line": order["lines"][0], "source": "work_order", "work_order": self._demo_work_order(5011)},
                {"line": order["lines"][1], "source": "bom", "bom": self._demo_bom("B10020")},
            ],
        }

"""
title: SAP Business One
author: lwkenneth-akit
version: 0.3.1
description: Read-only SAP B1 tool. qty_to_ship returns a short total so a 16k context model can answer.
requirements: httpx
"""
import json
from typing import Any
import httpx
from pydantic import BaseModel, Field
ITEM_UDF_FIELDS = ("U_kzbuchng","U_kzdruck","U_aussch","U_din","U_me_lager","U_me_verbr","U_losgr","U_match","U_sachb_id","U_wbz","U_wst_id","U_znr","U_kalk_pr","U_dispo","U_ke","U_gruppe","U_picture2","U_picture3","U_bestellt","U_text_d","U_text_eng","U_sa","U_form","U_un_nr","U_vg","U_nag","U_nag_eng","U_zollt","U_spezgew","U_verschn","U_brgew","U_batchroh","U_prccode","U_bereitst","U_verfb","U_uland","U_losgr_ka","U_kalksche","U_beasprio","U_haltbark","U_haltbar2","U_beas_vri","U_beas_ver","U_beas_caf","U_beas_kumulierung","U_beas_shortvariantd","U_beas_prodrelease","U_beas_mps","U_YWATId","U_YDEFDATE","U_YVARIETY","U_WClassification","U_WGENDER","U_WPOREMARK","U_WCOMMENT","U_CDIA39","U_CDIAM6_12","U_CINTERNDIAM","U_CHANDCLEAR","U_CCASEOPEN","U_CLUGSIZE","U_CCASETHICK","U_CDIALDIAM","U_CDIALTHICK","U_CCALIBER","U_CHANDHEIGHT","U_CATM","U_CTOPRCONST","U_CTOPRMAT","U_TIRINGCOLOR","U_CLENSHAPE","U_CSBMAT","U_CSBSIZE","U_CCRMAT","U_CCRPOS","U_CCRRECESS","U_CCRDIAM","U_CCRREF","U_CPUSHMAT","U_CPUSHTYPE","U_CPUSHDIAM","U_CCBMAT","U_CCBCONST","U_CCBSHAPE","U_CCBFINISH","U_CCBMARKIN","U_CCBMARKOUT","U_CCASEPART1","U_CCPFINISH1","U_CCPPLATING","U_CCASEPART2","U_CCPFINISH2","U_CCPPLATING2","U_CCASEPART3","U_CCPFINISH3","U_CCPPLATING3","U_CCASEPART4","U_CCPFINISH4","U_CCPPLATING4","U_CCASEPART5","U_CCPFINISH5","U_CCPPLATING5","U_SETCHCHARGE","U_SCASELUGSIZE","U_SPATTERN","U_SCOLOR","U_SSITCHING","U_SMARKLONG","U_SMARKSHORT","U_SLINING","U_SEDGE","U_SENDING","U_STHICK","U_SBUCKLEMAT","U_SBUCKLEMARK","U_SBUCKLEPROV","U_MCAILBER","U_MCALPOS","U_BUSIZE","U_BUMARK","U_BUCOLOR","U_BUPLATING","U_BUFINISH","U_BRLONGLINK","U_BRSHORTLINK","U_BRENDPIECE","U_BRENDPITHICK","U_BRLUGTHICK","U_BRCASELUGSIZE","U_BRSBSIZE","U_BRMARKOUT","U_BRMARKIN","U_BRPART1","U_BRFINISH1","U_BRPLATING1","U_BRPART2","U_BRFINISH2","U_BRPLATING2","U_BRPART3","U_BRFINISH3","U_BRPLATING3","U_BRPART4","U_BRFINISH4","U_BRPLATING4","U_BRPART5","U_BRFINISH5","U_BRPLATING5","U_DTHICK","U_DCASEOPEN","U_DDIALDIAM","U_DINTERNDIAM","U_DWINPOS","U_DCROWNPOS","U_DLOGO","U_DPRNCOLOR","U_DBKCOLOR","U_DBKFINISH","U_DINDPLATING","U_DLINKCOLOR","U_DLINKPRNCOLOR","U_DILLUM","U_DMARK12H","U_DMARK6HA","U_DMARK6HB","U_DMARK3H","U_DMARKBACK","U_YOLDMODEL","U_SHOLE","U_AMATERIAL","U_ACAILBER","U_HTYPE","U_HKIND","U_HMODEL","U_HLENGTH","U_HPLATING","U_HLUMIN","U_HGRADE","U_CUSTCODE","U_YPACKCODE","U_YREVIEW","U_HTHICK","U_HPOS","U_MSTEM","U_MWINDOWS","U_MDATEBACK","U_MDATELETTER","U_MDATELANG","U_DBRAND","U_DIRINGSIZE","U_PictureFile","U_Q_Case","U_Q_plating","U_Q_Band","U_Q_Leather","U_Q_Movement","U_Q_Other","U_Q_DIAL2","U_CCRCONSTRUCTION","U_CCROTHERPARTS","U_BRTYPE","U_SCONSTRUCT","U_SRING","U_DLAYER","U_DINDEXCONST","U_CMAT","U_BRMAT","U_SBUCKLETYPE","U_HMAT","U_SMAT","U_DMAT","U_CBEZEL","U_YSUPPREF","U_WODesc","U_CCRFINISH","U_CCRPLATING","U_CCBODYFINISH","U_CCBODYPLATING","U_BLANKETITEM","U_H_COLOR","U_Q_Other2","U_FTECHDRAWING","U_CBMARK","U_YBRAND","U_YPROJECT","U_YCARDCODE","U_RENDERING","U_OTHERDRAW","U_YCOMPLEX","U_FTDCASE","U_FTDDIAL","U_FTDHANDS","U_FTDSTRAP","U_FTDCROWN","U_FTDBUCKLE","U_FRENDERING","U_FCASEBACK1","U_FCASEBACK2","U_FOTDRAWING","U_FSAMPLE","U_RACKNO","U_Q_SHAND","U_Q_SSHAND","U_beas_BinGroup","U_SBUCKLE","U_WCustRef2","U_SubGroup","U_NEWCOST","U_COSTREMARK","U_Battery","U_MovementType","U_CUSTOM_MAT","U_SwissOH","U_to_odoo_date","U_SOCASEBACK","U_LimitedEdition","U_Total_Commited","U_YCOLOR","U_UDFBACKUP")
class Tools:
    def __init__(self):
        self.valves = self.Valves()
    class Valves(BaseModel):
        sap_base_url: str = Field(default="https://your-b1-server:50000/b1s/v2", description="Service Layer base URL, including /b1s/v2")
        company_db: str = Field(default="SBODemoUS", description="SAP company database")
        username: str = Field(default="manager", description="Read-only SAP user")
        password: str = Field(default="", description="SAP password")
        verify_ssl: bool = Field(default=False, description="Verify SSL")
        demo_mode: bool = Field(default=True, description="Sample data until login works")
        timeout_seconds: float = Field(default=30.0, description="Timeout")
    async def sap_status(self, __event_emitter__=None) -> str:
        """Check SAP Business One Service Layer login. Call this first if another SAP tool fails."""
        if self.valves.demo_mode:
            return self._dump({"ok": True, "mode": "demo"})
        try:
            async with self._client() as client:
                await self._login(client)
                version = await self._get(client, "/")
                await self._logout(client)
            return self._dump({"ok": True, "mode": "live", "service_layer": version})
        except Exception as exc:
            return self._dump({"ok": False, "error": str(exc)})
    async def qty_to_ship(self, date_from: str, date_to: str, item_name: str = "", __event_emitter__=None) -> str:
        """Sum open sales-order line quantity due to ship between two dates. Use this when asked how many watches or items to ship in a month. Returns only the total and top items. Reads RDR1.ShipDate. Does not change SAP.\n\n        :param date_from: Start date YYYY-MM-DD, inclusive. Example 2026-11-01.\n        :param date_to: End date YYYY-MM-DD, inclusive. Example 2026-11-30.\n        :param item_name: Optional item code or description filter. Leave empty for all items.\n        """
        start, end = date_from.strip(), date_to.strip()
        if len(start) != 10 or len(end) != 10:
            return self._dump({"error": "Use dates as YYYY-MM-DD, for example 2026-11-01 and 2026-11-30."})
        if self.valves.demo_mode:
            return self._dump({"mode": "demo", "date_from": start, "date_to": end, "total_open_qty": 120, "line_count": 2, "by_item": [{"ItemCode": "A00001", "ItemDescription": "Watch", "open_qty": 80}, {"ItemCode": "B10020", "ItemDescription": "Watch strap", "open_qty": 40}]})
        try:
            rows = await self._ship_lines(start, end)
            return self._dump(self._sum_ship_lines(rows, item_name, start, end))
        except Exception as exc:
            return self._dump({"error": str(exc)})
    async def search_business_partners(self, query: str, limit: int = 15, __event_emitter__=None) -> str:
        """Search customers and vendors by code, name, or tax id.\n\n        :param query: Card code, card name, or tax id.\n        :param limit: Maximum rows.\n        """
        if self.valves.demo_mode:
            return self._dump([{"CardCode": "C20000", "CardName": "Maxi-Teq Ltd"}])
        q = self._esc(query)
        data = await self._odata("/BusinessPartners", {"$select": "CardCode,CardName,CardType,Phone1,EmailAddress,CurrentAccountBalance,Currency,Valid,Frozen", "$filter": f"contains(CardCode,'{q}') or contains(CardName,'{q}') or contains(FederalTaxID,'{q}')", "$top": str(self._limit(limit))})
        return self._dump(data.get("value", data))
    async def search_items(self, query: str, limit: int = 15, __event_emitter__=None) -> str:
        """Search items by code or name.\n\n        :param query: Item code or name.\n        :param limit: Maximum rows.\n        """
        if self.valves.demo_mode:
            return self._dump([{"ItemCode": "A00001", "ItemName": "Sample item"}])
        q = self._esc(query)
        data = await self._odata("/Items", {"$select": "ItemCode,ItemName,QuantityOnStock,SalesUnit,Valid,Frozen", "$filter": f"contains(ItemCode,'{q}') or contains(ItemName,'{q}')", "$top": str(self._limit(limit))})
        return self._dump(data.get("value", data))
    async def get_item_master(self, item_code: str, include_empty_udf: bool = False, __event_emitter__=None) -> str:
        """Get item master OITM with most user-defined fields. Use for case, dial, hands, strap, buckle, movement, brand, and project fields. Read only.\n\n        :param item_code: Exact item code.\n        :param include_empty_udf: Also return blank user-defined fields.\n        """
        code = item_code.strip()
        if not code:
            return self._dump({"error": "item_code is required."})
        if self.valves.demo_mode:
            return self._dump({"mode": "demo", "ItemCode": code, "ItemName": "Sample item", "user_defined_fields": {"U_YBRAND": "Sample Brand", "U_CMAT": "Stainless steel", "U_CDIALDIAM": "39", "U_MovementType": "Automatic"}})
        try:
            item = await self._get(None, f"/Items('{self._esc(code)}')")
            item.update(await self._item_udf(code))
            return self._dump(self._trim_item(item, include_empty_udf))
        except Exception as exc:
            return self._dump({"error": str(exc)})
    async def get_sales_order(self, doc_num: int, __event_emitter__=None) -> str:
        """Get a sales order header and lines by DocNum.\n\n        :param doc_num: Sales order document number.\n        """
        if self.valves.demo_mode:
            return self._dump({"DocNum": doc_num, "CardCode": "C20000", "lines": [{"ItemCode": "A00001", "U_WO_NO": 5011}]})
        return self._dump(await self._doc_by_num("/Orders", doc_num))
    async def list_open_sales_orders(self, card_code: str = "", limit: int = 20, __event_emitter__=None) -> str:
        """List open sales orders.\n\n        :param card_code: Customer code, or empty for all.\n        :param limit: Maximum orders.\n        """
        if self.valves.demo_mode:
            return self._dump([{"DocNum": 10421, "CardCode": "C20000", "DocumentStatus": "bost_Open"}])
        filt = "DocumentStatus eq 'bost_Open'" + (f" and CardCode eq '{self._esc(card_code.strip())}'" if card_code.strip() else "")
        data = await self._odata("/Orders", {"$select": "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocCurrency,DocumentStatus", "$filter": filt, "$orderby": "DocDate desc", "$top": str(self._limit(limit, 50))})
        return self._dump(data.get("value", data))
    async def get_purchase_order(self, doc_num: int, __event_emitter__=None) -> str:
        """Get a purchase order header and lines by DocNum.\n\n        :param doc_num: Purchase order document number.\n        """
        if self.valves.demo_mode:
            return self._dump({"DocNum": doc_num, "CardCode": "V10000"})
        return self._dump(await self._doc_by_num("/PurchaseOrders", doc_num))
    async def get_so_po_links(self, sales_order_doc_num: int, __event_emitter__=None) -> str:
        """Read [@TPOLINK] rows for a sales order. U_SONUM links to ORDR.DocNum and U_PONUM links to OPOR.DocNum.\n\n        :param sales_order_doc_num: Sales order document number.\n        """
        if self.valves.demo_mode:
            return self._dump([{"U_SONUM": sales_order_doc_num, "U_PONUM": 22018}])
        num = int(sales_order_doc_num)
        errors = []
        for filt in (f"U_SONUM eq {num}", f"U_SONUM eq '{num}'"):
            try:
                data = await self._odata("/U_TPOLINK", {"$filter": filt, "$top": "100"})
                return self._dump(data.get("value") or [])
            except Exception as exc:
                errors.append(str(exc))
        return self._dump({"error": " | ".join(errors)})
    async def get_bom(self, item_code: str, __event_emitter__=None) -> str:
        """Get standard BOM OITT/ITT1. Use when the sales line has no work order.\n\n        :param item_code: Parent item code.\n        """
        if self.valves.demo_mode:
            return self._dump({"TreeCode": item_code, "lines": [{"ItemCode": "RM-01", "Quantity": 1}]})
        return self._dump(await self._get(None, f"/ProductTrees('{self._esc(item_code.strip())}')"))
    async def get_work_order(self, doc_num: int = 0, doc_entry: int = 0, __event_emitter__=None) -> str:
        """Get work order OWOR/WOR1. Match DocNum to RDR1.U_WO_NO or DocEntry to RDR1.U_WO_DOCENTRY.\n\n        :param doc_num: Work order number. Use 0 if unknown.\n        :param doc_entry: Work order DocEntry. Use 0 if unknown.\n        """
        if self.valves.demo_mode:
            return self._dump({"DocumentNumber": doc_num or 5011, "ItemNo": "A00001"})
        if doc_entry:
            return self._dump(await self._get(None, f"/ProductionOrders({int(doc_entry)})"))
        if not doc_num:
            return self._dump({"error": "Provide doc_num or doc_entry."})
        data = await self._odata("/ProductionOrders", {"$filter": f"DocumentNumber eq {int(doc_num)}", "$top": "1"})
        rows = data.get("value") or []
        return self._dump(rows[0] if rows else {"error": f"No work order {doc_num}"})
    async def explain_sales_order(self, doc_num: int, __event_emitter__=None) -> str:
        """Explain a sales order with linked purchase orders, work order, or BOM. Work order if U_WO_NO or U_WO_DOCENTRY is set; otherwise OITT/ITT1.\n\n        :param doc_num: Sales order document number.\n        """
        if self.valves.demo_mode:
            return self._dump({"mode": "demo", "DocNum": doc_num, "rule": "work order if U_WO_NO else BOM"})
        try:
            order = await self._doc_by_num("/Orders", doc_num)
            links = json.loads(await self.get_so_po_links(doc_num))
            return self._dump({"sales_order": order, "so_po_links": links})
        except Exception as exc:
            return self._dump({"error": str(exc)})
    async def _ship_lines(self, date_from: str, date_to: str) -> list:
        filt = "Orders/DocEntry eq Orders/DocumentLines/DocEntry and Orders/DocumentStatus eq 'bost_Open' and Orders/DocumentLines/LineStatus eq 'bost_Open' and Orders/DocumentLines/ShipDate ge '" + date_from + "' and Orders/DocumentLines/ShipDate le '" + date_to + "'"
        expand = "Orders($select=DocNum,CardCode),Orders/DocumentLines($select=ItemCode,ItemDescription,Quantity,ShipDate,RemainingOpenQuantity,OpenQuantity)"
        rows = []
        skip = 0
        for _ in range(3):
            data = await self._odata("/$crossjoin(Orders,Orders/DocumentLines)", {"$expand": expand, "$filter": filt, "$top": "100", "$skip": str(skip)})
            batch = data.get("value") or []
            rows.extend(batch)
            if len(batch) < 100:
                break
            skip += 100
        return rows
    def _sum_ship_lines(self, rows: list, item_name: str, date_from: str, date_to: str) -> dict:
        needle = item_name.strip().lower()
        by_item = {}
        total = 0.0
        for row in rows:
            line = row.get("Orders/DocumentLines") or {}
            code = str(line.get("ItemCode") or "")
            desc = str(line.get("ItemDescription") or "")[:80]
            if needle and needle not in code.lower() and needle not in desc.lower():
                continue
            qty = line.get("RemainingOpenQuantity")
            if qty in (None, ""):
                qty = line.get("OpenQuantity")
            if qty in (None, ""):
                qty = line.get("Quantity") or 0
            qty = float(qty or 0)
            total += qty
            bucket = by_item.setdefault(code, {"ItemCode": code, "ItemDescription": desc, "open_qty": 0.0})
            bucket["open_qty"] += qty
        items = sorted(by_item.values(), key=lambda r: r["open_qty"], reverse=True)
        return {"date_from": date_from, "date_to": date_to, "total_open_qty": total, "line_count": len(rows), "item_count": len(items), "by_item": items[:15], "note": "Open sales order quantity by RDR1.ShipDate. Top 15 items only."}
    async def _item_udf(self, item_code: str) -> dict:
        merged = {}
        fields = list(ITEM_UDF_FIELDS)
        for start in range(0, len(fields), 40):
            batch = fields[start:start+40]
            data = await self._odata("/Items", {"$select": "ItemCode," + ",".join(batch), "$filter": f"ItemCode eq '{self._esc(item_code)}'", "$top": "1"})
            rows = data.get("value") or []
            if rows:
                merged.update(rows[0])
        merged.pop("ItemCode", None)
        return merged
    def _trim_item(self, item: dict, include_empty_udf: bool) -> dict:
        keep = ["ItemCode","ItemName","ForeignName","ItemsGroupCode","QuantityOnStock","SalesUnit","PurchaseUnit","Valid","Frozen"]
        out = {k: item.get(k) for k in keep if k in item}
        udf = {}
        for key in ITEM_UDF_FIELDS:
            if key not in item:
                continue
            value = item.get(key)
            if not include_empty_udf and value in (None, "", 0):
                continue
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            udf[key] = value
        out["user_defined_fields"] = udf
        out["user_defined_field_count"] = len(udf)
        return out
    async def _doc_by_num(self, path: str, doc_num: int) -> dict:
        data = await self._odata(path, {"$filter": f"DocNum eq {int(doc_num)}", "$top": "1"})
        rows = data.get("value") or []
        if not rows:
            raise RuntimeError(f"No document at {path} with DocNum {doc_num}.")
        doc_entry = rows[0].get("DocEntry")
        return rows[0] if doc_entry is None else await self._get(None, f"{path}({int(doc_entry)})")
    async def _odata(self, path: str, params: dict) -> Any:
        async with self._client() as client:
            await self._login(client)
            try:
                return await self._get(client, path, params)
            finally:
                await self._logout(client)
    async def _get(self, client, path: str, params=None) -> Any:
        own = client is None
        if own:
            client = self._client()
            await client.__aenter__()
            await self._login(client)
        try:
            url = path if str(path).startswith("http") else f"{self.valves.sap_base_url.rstrip('/')}{path}"
            resp = await client.get(url, params=params)
            if resp.status_code in (401, 301, 302) or "Invalid session" in resp.text:
                await self._login(client)
                resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                raise RuntimeError(f"SAP GET {path} failed ({resp.status_code}): {resp.text[:800]}")
            return resp.json() if resp.content else {}
        finally:
            if own:
                await self._logout(client)
                await client.__aexit__(None, None, None)
    async def _login(self, client) -> None:
        if not self.valves.password:
            raise RuntimeError("SAP password is empty. Set valves and turn demo_mode off.")
        resp = await client.post(f"{self.valves.sap_base_url.rstrip('/')}/Login", json={"CompanyDB": self.valves.company_db, "UserName": self.valves.username, "Password": self.valves.password})
        if resp.status_code >= 400:
            raise RuntimeError(f"SAP login failed ({resp.status_code}): {resp.text[:500]}")
    async def _logout(self, client) -> None:
        try:
            await client.post(f"{self.valves.sap_base_url.rstrip('/')}/Logout")
        except Exception:
            return
    def _client(self):
        return httpx.AsyncClient(verify=self.valves.verify_ssl, timeout=self.valves.timeout_seconds, headers={"Content-Type": "application/json"})
    def _esc(self, value: str) -> str:
        return value.replace("'", "''")
    def _limit(self, value: int, cap: int = 50) -> int:
        try:
            n = int(value)
        except (TypeError, ValueError):
            n = 15
        return max(1, min(n, cap))
    def _dump(self, payload) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)

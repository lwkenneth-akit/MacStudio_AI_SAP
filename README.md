# Mac Studio AI + SAP B1

Open WebUI tool that reads SAP Business One 10 through Service Layer.
It does not create, update, or delete SAP data.

## Import into Open WebUI

1. Open WebUI as an admin.
2. Go to Workspace, then Tools, then Create (or Import).
3. Paste the contents of `openwebui/sap_b1_tool.py`, or import that file.
4. Save. Open the tool Valves and set:
   - `sap_base_url`: `https://your-b1-server:50000/b1s/v2`
   - `company_db`: your company database
   - `username` / `password`: a read-only SAP user
   - `verify_ssl`: false if the Service Layer certificate is self-signed
   - `demo_mode`: false after login works
5. Enable the tool on the model (llama3.3:70b).
6. In chat, ask: "Check SAP login" or "Explain sales order 10421".

`demo_mode` is on by default, so the tool returns sample data until you turn it off.

## What the model can call

- `sap_status`
- `search_business_partners`
- `search_items`
- `get_sales_order` / `list_open_sales_orders` (ORDR, RDR1)
- `get_purchase_order` (OPOR, POR1)
- `get_so_po_links` (`[@TPOLINK]`: `U_SONUM` to sales DocNum, `U_PONUM` to purchase DocNum)
- `get_work_order` (OWOR, WOR1; matched by `RDR1.U_WO_NO` or `RDR1.U_WO_DOCENTRY`)
- `get_bom` (OITT, ITT1; used when the sales line has no work order)
- `explain_sales_order` (combines the rules above)

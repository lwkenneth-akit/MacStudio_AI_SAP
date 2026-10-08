# Mac Studio AI + SAP B1

Open WebUI tool that reads SAP Business One 10 through Service Layer.
It does not create, update, or delete SAP data.

## Import into Open WebUI

1. Workspace, Tools, open the SAP Business One tool.
2. Replace the code with `openwebui/sap_b1_tool.py` and save.
3. Set Valves: Service Layer URL, company database, user, password.
4. Turn `demo_mode` off after login works.
5. Enable the tool on llama3.3:70b. Function calling must be Native.

## Ship quantity

`qty_to_ship` sums open sales-order lines (`RDR1.ShipDate` and open quantity).
Ask: "How many watches need to ship from 2026-11-01 to 2026-11-30?"
Leave the item filter empty to include all items.

Other calls: item master user-defined fields, sales orders, purchase orders, [@TPOLINK], work orders, and standard BOM.

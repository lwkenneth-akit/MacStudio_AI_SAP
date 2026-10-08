# Mac Studio AI + SAP B1

Open WebUI tool that reads SAP Business One 10 through Service Layer.
It does not create, update, or delete SAP data.

## Import into Open WebUI

1. Open WebUI as an admin.
2. Go to Workspace, then Tools, then the existing SAP Business One tool.
3. Replace the code with `openwebui/sap_b1_tool.py` and save.
4. In Valves, set the Service Layer URL, company database, user, and password.
5. Turn `demo_mode` off after login works.
6. Enable the tool on llama3.3:70b.

## Item master

`get_item_master` reads OITM plus the user-defined fields from script.sql.
Blank fields are omitted unless `include_empty_udf` is true.
Ask: "Show the item master and custom fields for item A00001."

Other calls: sales orders, purchase orders, [@TPOLINK], work orders, and standard BOM.

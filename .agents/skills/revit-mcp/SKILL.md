---
name: revit-mcp
description: >-
  Dieu khien, truy van va tu dong hoa Autodesk Revit thong qua giao thuc Model Context Protocol (MCP)
  bang revit-mcp (https://github.com/mcp-servers-for-revit/revit-mcp va mcp-servers-for-revit).
  Kich hoat skill nay bat cu khi nao nguoi dung yeu cau lam viec, dung hinh, kiem tra thong so,
  tao family, quan ly doi tuong, hoac chay script truc tiep trong Revit.
---

# Revit MCP Integration Skill

Skill nay huong dan AI Agent su dung giao thuc **Model Context Protocol (MCP)** de ket noi hai chieu truc tiep voi **Autodesk Revit** (ho tro Revit 2020 - 2026), dua tren he thong [mcp-servers-for-revit](https://github.com/mcp-servers-for-revit/mcp-servers-for-revit).

---

## 1. Kien truc he thong (Architecture)

```
+------------------+          stdio           +------------------+
|   Antigravity    | <---------------------> |    MCP Server    |
|   (AI Client)    |                          | (Node.js / npx)  |
+------------------+                          +------------------+
                                                       |
                                                   WebSocket
                                                 (Port 8080)
                                                       v
+------------------+      Revit API In-Proc   +------------------+
|  Revit Project   | <--------------------- |   Revit Add-in   |
|   (Active Doc)   |                          | (C# Plugin .NET) |
+------------------+                          +------------------+
```

1. **MCP Server (`mcp-server-for-revit`)**: Chay duoi dang service cuc bo bang Node.js, tiep nhan tool calls tu AI agent qua standard I/O (stdio) va chuyen tiep qua WebSocket.
2. **Revit Plugin (`revit_mcp_plugin`)**: Add-in C# chay ngam ben trong Revit, mo cong ket noi WebSocket, tiep nhan lenh va thuc thi tren UI Thread cua Revit thong qua `ExternalEvent` hoac Transaction.
3. **Command Set (`RevitMCPCommandSet`)**: Bo lenh API phong phu giup truy van, khoi tao, sua doi doi tuong, them view, gan parameter va chay ma code tuy bien trong Revit.

---

## 2. Danh muc Cong cu (Tools) do Revit MCP cung cap

Khi he thong MCP ket noi thanh cong voi Revit dang mo, cac tool sau se san sang de goi:

| Nhom chuc nang | Ten Tool MCP | Mo ta chuc nang |
| :--- | :--- | :--- |
| **Thong tin Project** | `get_current_document` | Lay ten file, duong dan, don vi, Project Information cua file Revit dang mo. |
| **Truy van Doi tuong**| `get_elements` | Tim kiem element theo Category (Walls, Levels, Grids, Generic Models...), Type, hoac Id. |
| **Thong so Parameter**| `get_parameters` | Doc toan bo Instance & Type parameters cua ElementId duoc chi dinh. |
| **Gan Parameter**     | `set_parameter` | Thay doi gia tri tham so (Text, Number, Length, Yes/No) cua element trong Revit. |
| **Tao Doi tuong**     | `create_element` | Tao Wall, Floor, Column, Beam, Level, Grid hoac dat FamilyInstance theo toa do 3D. |
| **Xoa Doi tuong**     | `delete_element` | Xoa cac doi tuong theo danh sach ElementId. |
| **Chay Code truc tiep**| `execute_code` | Gui doan ma C# hoac Python truc tiep vao Revit de thuc thi Transaction phuc tap. |

---

## 3. Quy trinh Agent su dung Revit MCP

Moi khi nguoi dung yeu cau tac vu lien quan den Revit (vi du: "kiem tra cao do", "dat dai phan cach", "lay danh sach layer", "doi tham so L"):

1. **Buoc 1: Kiem tra ket noi Revit**
   - Goi `get_current_document` de xac nhan Revit dang mo dung file can thao tac.
2. **Buoc 2: Thu thap du lieu hien trang**
   - Neu can dat Family: Goi `get_elements(category="Generic Models")` hoac `FamilySymbols` de kiem tra Type da co trong project chua.
   - Neu can toa do: Truy van Level, Grid, hoac Curve dan duong.
3. **Buoc 3: Thuc thi thao tac (Modify / Create)**
   - Dung cac tool chuyen biet nhu `create_element` hoac `set_parameter`.
   - Neu tac vu doi hoi thuat toan hinh hoc phuc tap (nhu rai 3D Polyline theo duong cong), ket hop sinh ma script Dynamo hoac chay `execute_code`.
4. **Buoc 4: Kiem tra ket qua & Phan hoi**
   - Truy van lai Element vua tao de xac nhan khong co xung dot (clash) hay loi Transaction.
   - Bao cao so luong, ElementId, va thong so thuc te cho nguoi dung.

---

## 4. Cau hinh moi truong & Cai dat

### A. Cau hinh MCP Client (`mcp_config.json`)
File: `%USERPROFILE%\.gemini\config\mcp_config.json`
```json
{
  "mcpServers": {
    "revit-mcp": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "mcp-server-for-revit"]
    }
  }
}
```

### B. Cai dat Add-in vao Revit
1. Tai goi cai dat zip cho phien ban Revit tu [Releases](https://github.com/mcp-servers-for-revit/mcp-servers-for-revit/releases) (vi du `mcp-servers-for-revit-v1.0.0-Revit2025.zip`).
2. Giai nen va copy vao thu muc Add-in:
   `%AppData%\Autodesk\Revit\Addins\2025\`
   - `mcp-servers-for-revit.addin`
   - Thu muc `revit_mcp_plugin/`
3. Mo Revit -> Chon **Always Load**. Tren thanh Ribbon se xuat hien tab **mcp-servers-for-revit**.
4. Cai dat **Node.js 18+** tren Windows de lenh `npx` hoat dong tro tru.

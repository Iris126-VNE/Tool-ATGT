# 🛣️ Tool ATGT — Bộ Công Cụ Tự Động Hóa Dựng Hình & Gán LOI BIM An Toàn Giao Thông (Revit & Dynamo)

[![Autodesk Revit](https://img.shields.io/badge/Autodesk%20Revit-2024%20%7C%202025-0696D7?logo=autodesk&logoColor=white)](https://www.autodesk.com/products/revit/)
[![Dynamo BIM](https://img.shields.io/badge/Dynamo%20Player-Ready-FF6C00)](https://dynamobim.org/)
[![Python](https://img.shields.io/badge/Python-RevitAPI-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![BIM Standard](https://img.shields.io/badge/BIM%20LOI-BEP%20%26%201056%2FQ%C4%90--BXD-2EA44F)](#4-gán-thông-tin-bim-loi-hàng-loạt)

**Tool ATGT** là bộ giải pháp tự động hóa chuyên sâu trên **Autodesk Revit & Dynamo Player**, giúp kỹ sư BIM hạ tầng giao thông (Cao tốc, Quốc lộ, Đường đô thị) tự động rải các cấu kiện **An toàn giao thông (ATGT)** bám sát 100% theo bình đồ & trắc dọc 3D từ CAD/LandXML/IFC, đồng thời tự động gắn đầy đủ thông tin **LOI (Level of Information)** theo chuẩn BEP và Quyết định 1056/QĐ-BXD.

---

## ✨ Tính Năng Nổi Bật

- 🎯 **Thuật toán Dây cung 3D nối tiếp (Chord-Based Sequential Placement)**: Điểm cuối của đốt trước trùng khít với điểm đầu của đốt sau, khắc phục triệt để lỗi hở mối nối chữ V hoặc chồng lấn (clash) trên đường cong.
- 📐 **Bám sát cao độ & độ dốc dọc 3D (Pitch & Elevation Sync)**: Tự động đọc tọa độ World 3D từ `CAD ImportInstance`, `3D Polyline`, `ModelCurve`, `DirectShape` và nội suy các đỉnh bị rớt cao độ `Z = 0`.
- 🛡️ **Tự động định hướng mặt cấu kiện**: Tôn sóng hộ lan tự động quay mặt lượn sóng về phía lòng đường (hỗ trợ rải bên Phải, bên Trái, hoặc Cả hai bên cùng lúc).
- 🧹 **Chống trùng lặp thông minh (Automatic Corridor Purge)**: Khi bấm chạy lại (Re-run), tool tự động dọn sạch các cấu kiện cũ trên cùng tuyến trước khi tạo mới, không bao giờ bị đè nhiều lớp Family.
- 📋 **Gán tự động bộ tham số BIM LOI**: Tự động nạp Shared Parameters và điền thông tin Định danh (`100`), Định vị & Tọa độ (`200`), Hình học (`300`), Vật liệu (`400`) theo lý trình tăng dần.

---

## 📦 Danh Mục Bộ Công Cụ Trong Repository

| STT | Tên File Dynamo (`product/*.dyn`) | Script Python lõi (`src/*.py`) | Chức năng chính |
| :-: | :--- | :--- | :--- |
| **1** | `product/[LENH ATGT] RAI DAI PHAN CACH - TON SONG.dyn` | `src/Import_ATGT_To_Revit.py` | Rải **Dải phân cách (DPC)**, **Lưới chống chói** bám theo 3D Polyline với tùy chọn lệch tim & khe co giãn. |
| **2** | `product/[LENH ATGT] RAI TON SONG HO LAN.dyn` | `src/Rai_Ton_Song_Revit.py` | Rải **Tôn lượn sóng hộ lan** (`TS-ZZ-GUA`), tự động xoay mặt tôn hướng vào tim đường & bám dốc dọc 3D. |
| **3** | `product/[LENH ATGT] RAI HANG RAO.dyn` | `src/Rai_Hang_Rao_Revit.py` | Rải **Hàng rào bảo vệ hành lang ATGT** (thép gai, lưới B40) theo ranh giải phóng mặt bằng. |
| **4** | `product/[LENH ATGT] RAI HANG RAO - TUY CHON FAMILY.dyn` | `src/Rai_Hang_Rao_Tuy_Chon_Family_Revit.py` | Rải **bất kỳ Family nào trong dự án** qua menu thả (Dropdown), hỗ trợ cả Family dạng Điểm (Point-Based) và Dầm (Line/Beam-Based). |
| **5** | `product/[LENH ATGT] GAN LOI - THONG TIN BIM.dyn` | `src/Gan_LOI_ATGT_Revit.py` | Quét chọn hoặc tự động lọc toàn bộ cấu kiện ATGT để đánh mã theo lý trình và gắn bộ tham số **BIM LOI**. |

> **Công cụ phụ trợ xử lý dữ liệu 3D ngoài Revit (`src/`):**
> - `src/export_cad.lsp` + `src/export_atgt_3d_data.ps1`: Trích xuất Block/Polyline từ AutoCAD và nội suy cao độ từ bề mặt TIN LandXML (`src/TinSurface.cs`) ra file CSV 3D.
> - `src/Match_Ifc_Surface_Elevation.ps1`: Nội suy và khớp cao độ cấu kiện Revit theo bề mặt địa hình/mặt đường từ file `.ifc`.

---

## 🚀 Cài Đặt & Bắt Đầu Nhanh (Quick Start)

### Bước 1: Tải bộ công cụ về máy
Mở **Git Bash** hoặc **PowerShell** và clone repository về máy tính (hoặc bấm **Code -> Download ZIP** trên GitHub):
```bash
git clone https://github.com/Iris126-VNE/Tool-ATGT.git
```

### Bước 2: Mở trong Dynamo Player của Revit
1. Mở **Autodesk Revit** (khuyến nghị Revit 2024 / 2025) và mở file dự án `.rvt`.
2. Đảm bảo các Family ATGT cần rải (Dải phân cách, Tôn sóng, Hàng rào, Biển báo...) đã được load vào dự án.
3. Trên thanh Ribbon, vào tab **Manage** ➔ chọn **Dynamo Player**.
4. Bấm vào nút **Add Folder (Thêm thư mục)** trên Dynamo Player và trỏ đường dẫn tới thư mục **`Tool-ATGT/product`** vừa tải về.

### Bước 3: Chạy công cụ
1. Bấm vào tên lệnh `[LENH ATGT] ...` cần sử dụng trong danh sách của Dynamo Player.
2. Thiết lập các thông số đầu vào (Inputs) ➔ Bấm **Select** để chọn tuyến CAD/Polyline trên mô hình 3D ➔ Bấm **Play (Run)**.

> [!IMPORTANT]
> **Lưu ý khi mở trực tiếp bằng Dynamo Editor:**
> Nếu bạn mở file `.dyn` trong cửa sổ Dynamo thay vì Dynamo Player, hãy kiểm tra góc dưới bên trái và đảm bảo chế độ chạy đang để là **Manual (Thủ công)**. **Tuyệt đối không để Automatic** để tránh việc Dynamo tự chạy lại liên tục mỗi khi bạn nhập thông số.

---

## 📖 Hướng Dẫn Chi Tiết Từng Công Cụ

### 1. Rải Dải Phân Cách & Lưới Chống Chói
**File sử dụng:** `[LENH ATGT] RAI DAI PHAN CACH - TON SONG.dyn`

#### Quy trình thao tác:
1. Mở công cụ trên **Dynamo Player**.
2. Tại **Mục 1 (`CHON TIM TUYEN / MO HINH`)**: Bấm **Select** ➔ Click chọn khối CAD Import (ví dụ `DPC.dwg`), đường 3D Polyline, hoặc Model Line trên 3D View.
3. Tại **Mục 2 (`CHON KIEU FAMILY`)**: Chọn kiểu Family trong dự án (`Q2P_DPC_KM52-60`, `DPC_L=5M`, `DPC_L=3M`...).
4. Điều chỉnh thông số hình học và bấm **Play**.

#### Bảng thông số đầu vào:
| STT | Tên thông số trên Dynamo Player | Ý nghĩa & Hướng dẫn nhập | Mặc định |
| :-: | :--- | :--- | :--- |
| **1** | `1. CHON TIM TUYEN / MO HINH` | Chọn đối tượng đường dẫn (CAD Import, 3D Polyline, DirectShape, Model Line). | `None` |
| **2** | `2. CHON KIEU FAMILY` | Chọn Family Type muốn rải (hỗ trợ cả Point-Based và Line-Based). | `Q2P_DPC_KM52-60` |
| **3** | `3. CHIEU DAI DOT L / BUOC RAI (m)` | Chiều dài 1 đốt cấu kiện (`5.0`, `3.0`, `2.0`m đối với DPC; `4.0`m đối với Tôn sóng). | `3.0` |
| **4** | `4. CHIEU CAO DOT H (m)` | Chiều cao thân đốt (tự động đồng bộ vào tham số chiều cao Family). | `0.9` |
| **5** | `5. BE RONG DAY DOT W (m)` | Bề rộng đáy đốt DPC. | `0.6` |
| **6** | `6. KHE HO / DO LONG MONG NGAM (m)` | • `0.0`: Khít sát nhau 100%<br>• `0.01` – `0.02`: Khe co giãn 1–2cm<br>• `< 0` (VD `-0.05`): Mộng ngàm âm dương lồng vào nhau. | `0.01` |
| **7** | `7. CAO DO Z OFFSET (m)` | • `0.0`: Rải sát mặt đường<br>• `+0.9`: Rải Lưới chống chói nằm trên đỉnh DPC cao `0.9m`. | `0.0` |
| **8** | `8. GOC XOAY BU (Do)` | Mặc định `0.0` đã tự động xoay dọc theo dây cung tuyến. Nhập `90` hoặc `-90` nếu gốc Family bị dựng ngang. | `0.0` |
| **9** | `9. TEN LAYER CAD` | Để trống `""` để tự động nhận diện layer (`DPC`, `0_Ranh giua`, `C-TOPO-FEAT`...) hoặc nhập tên layer cụ thể. | `""` |
| **10** | `10. KHOANG LECH TIM MAT BANG (m)` | • `0.0`: Nằm đúng tim Polyline<br>• `> 0`: Dịch sang **bên PHẢI** theo hướng tuyến<br>• `< 0`: Dịch sang **bên TRÁI** theo hướng tuyến. | `0.0` |

---

### 2. Rải Tôn Lượn Sóng Hộ Lan (W-Beam Guardrail)
**File sử dụng:** `[LENH ATGT] RAI TON SONG HO LAN.dyn`

Công cụ tích hợp thuật toán pháp tuyến mặt bằng giúp **mặt cong lượn sóng luôn quay về phía lòng đường** và **cột đỡ luôn nằm phía taluy/lề đường**, đồng thời nghiêng theo đúng độ dốc dọc 3D của tuyến.

#### Bảng thông số đầu vào:
| STT | Tên thông số trên Dynamo Player | Ý nghĩa & Hướng dẫn nhập | Mặc định |
| :-: | :--- | :--- | :--- |
| **1** | `1. CHON TIM TUYEN / MO HINH` | Chọn CAD Import (`Ton luon song.dwg`), ModelCurve hoặc 3D Polyline. | `None` |
| **2** | `2. CHON KIEU FAMILY TON SONG` | Tên Family Symbol tôn sóng trong dự án. | `TS-ZZ-GUA` |
| **3** | `3. VI TRI BEN TUYEN` | • `Phai`: Rải lề phải (mặt tôn quay sang trái vào lòng đường)<br>• `Trai`: Rải lề trái (mặt tôn quay sang phải vào lòng đường)<br>• `Ca hai ben`: Rải đồng thời 2 bên lề đường. | `Phai` |
| **4** | `4. KHOANG CACH LECH TIM / MEP DUONG (m)` | • Nhập `0.0` nếu pick trực tiếp đường полиline tôn sóng ở lề đường.<br>• Nhập khoảng cách (VD `12.0`) nếu pick từ đường tim tuyến (Centerline). | `0.0` |
| **5** | `5. BUOC RAI / CHIEU DAI DOT TON L (m)` | Bước cột / chiều dài đốt tôn tiêu chuẩn (`4.0`m hoặc `2.0`m). | `4.0` |
| **6** | `6. CHIEU CAO DINH TON H (m)` | Chiều cao đỉnh tôn so với mặt đường (`0.75`m). | `0.75` |
| **7** | `7. CAO DO Z OFFSET (m)` | Độ cao tinh chỉnh theo phương đứng ($Z$). | `0.0` |
| **8** | `8. DAO CHIEU MAT TON 180 DO` | Nhập `Co` nếu chiều vẽ Polyline CAD ngược với chiều xe chạy thiết kế; mặc định `Khong`. | `Khong` |
| **9** | `9. TEN LAYER CAD` | Tên layer chứa đường dẫn tôn sóng trong file CAD. | `TS` |
| **10** | `10. MA TIEN TO LOI BIM` | Tiền tố đánh mã tự động tăng dần (`TS-KM52-0001`, `TS-KM52-0002`...). | `TS-KM52-` |
| **11** | `11. GOI THAU VA LY TRINH` | Thông tin gói thầu và đoạn lý trình phục vụ quản lý BIM. | `Goi thau XL01 \| Km52+000 - Km60+000` |

---

### 3. Rải Hàng Rào Bảo Vệ & Cấu Kiện Tùy Chọn Family
**File sử dụng:**
- `[LENH ATGT] RAI HANG RAO.dyn` *(Chuyên biệt cho Hàng rào bảo vệ hành lang ATGT)*
- `[LENH ATGT] RAI HANG RAO - TUY CHON FAMILY.dyn` *(Bản đa năng có **Dropdown Menu** chọn bất kỳ Family nào trong Revit)*

#### Điểm mạnh của bản Tùy Chọn Family (`RAI HANG RAO - TUY CHON FAMILY.dyn`):
- **Tự động nhận diện chủng loại Family (Smart Adaptive Engine)**:
  - Nếu chọn Family dạng **Structural Framing (Beam)** hoặc **Line-Based** (như hàng rào `FE_BW`, tôn sóng Line-based): Tự động dựng đoạn dầm nối tiếp 2 đầu và đồng bộ cao độ 2 đầu `STRUCTURAL_BEAM_END0_ELEVATION` / `END1_ELEVATION` bám sát địa hình 3D.
  - Nếu chọn Family dạng **Point-Based** (Cọc tiêu, Biển báo, Cột đèn, Đốt DPC): Tự động đặt tại tâm/đầu đốt và xoay góc tiếp tuyến chuẩn xác.
- **Dọn dẹp theo từng Family (Family-Specific Corridor Purge)**: Khi chạy lại cho Family A, tool chỉ xóa các đốt cũ của Family A trên tuyến đó, giữ nguyên các Family khác đã rải.

#### Bảng thông số đầu vào:
| STT | Tên thông số trên Dynamo Player | Ý nghĩa & Hướng dẫn nhập | Mặc định |
| :-: | :--- | :--- | :--- |
| **1** | `1. CHON TIM TUYEN / MO HINH` | Chọn 3D Polyline, CAD Import (layer `HR`, `TS`, `DPC`...), DirectShape, ModelCurve. | `None` |
| **2** | `2. CHON KIEU FAMILY (Dropdown)` | Chọn trực tiếp bất kỳ Family Type nào đang có trong dự án từ danh sách thả. | `GDXM-KM16+000-KM25+000-ZZ-FE_BW` |
| **3** | `3. VI TRI BEN TUYEN` | `Phai` / `Trai` / `Ca hai ben`. | `Phai` |
| **4** | `4. KHOANG CACH LECH TIM / MEP DUONG (m)` | `0.0` (nếu bắt trực tiếp đường ranh) hoặc khoảng cách từ tim ra ranh (`15.0`, `20.0`m). | `0.0` |
| **5** | `5. BUOC RAI / CHIEU DAI DOT L (m)` | Bước chia đốt: Hàng rào `2.5`m, Tôn sóng `4.0`m, DPC `3.0`m / `5.0`m. | `2.5` |
| **6** | `6. CHIEU CAO CAU KIEN H (m)` | Chiều cao cấu kiện: Hàng rào `1.8`m, Tôn sóng `0.75`m, DPC `0.9`m. | `1.8` |
| **7** | `7. CAO DO Z OFFSET (m)` | Độ cao tinh chỉnh theo phương đứng ($Z$). | `0.0` |
| **8** | `8. DAO CHIEU MAT CAU KIEN 180 DO` | `Khong` hoặc `Co` (đảo ngược 180 độ). | `Khong` |
| **9** | `9. TEN LAYER CAD` | Để trống `""` (nhận tất cả layer) hoặc nhập tên layer (`HR`, `TS`, `DPC`...). | `""` |
| **10** | `10. MA TIEN TO LOI BIM` | Để trống `""` (tự lấy theo tên Family) hoặc nhập tiền tố riêng (`HR-KM16-`). | `""` |
| **11** | `11. GOI THAU VA LY TRINH` | Thông tin gói thầu và lý trình quản lý. | `Goi thau XL01 \| Km0+000 - Km60+000` |

---

### 4. Gán Thông Tin BIM (LOI) Hàng Loạt
**File sử dụng:** `[LENH ATGT] GAN LOI - THONG TIN BIM.dyn`

Công cụ giúp chuẩn hóa dữ liệu phi hình học (LOI) cho toàn bộ cấu kiện ATGT trong mô hình theo đúng **Kế hoạch thực hiện BIM (BEP)** và **Quyết định 1056/QĐ-BXD**.

#### 3 cách chọn đối tượng linh hoạt:
1. **Cách 1 (Quét chọn trực tiếp)**: Quét chọn các đối tượng cần gán LOI trên màn hình Revit trước ➔ Bấm **Play** trên Dynamo Player.
2. **Cách 2 (Lọc theo từ khóa)**: Nhập tên Family hoặc từ khóa (ví dụ: `ton song`, `dpc`, `hang rao`, `bien bao`) vào ô Input đầu tiên `[0]` ➔ Bấm **Play**.
3. **Cách 3 (Tự động toàn dự án)**: Để trống ô `[0]` (hoặc nhập `all`) ➔ Tool tự động quét toàn bộ các cấu kiện ATGT trong dự án, sắp xếp theo dọc tuyến và đánh mã thứ tự tăng dần.

#### Hệ thống tham số BIM được tự động khởi tạo & gán giá trị:
| Nhóm tham số | Tên tham số Shared Parameter | Nguồn dữ liệu / Cách tính |
| :--- | :--- | :--- |
| **100 - Định danh** | `101-Mã cấu kiện` (đồng bộ vào `Mark`) | Tự động đánh số tăng dần dọc tuyến (`TS-HTS-0001`, `TS-HTS-0002`...) |
| **100 - Định danh** | `102-Phân loại cấu kiện` | Nhập từ Dynamo Player (Mặc định: `An toàn giao thông`) |
| **100 - Định danh** | `105-Mô tả cấu kiện` | Tự động nhận diện (`Tôn hộ lan`, `Dải phân cách`, `Hàng rào`, `Biển báo`) hoặc nhập tay |
| **200 - Định vị** | `201-Vị trí theo khu vực` | Đoạn lý trình quản lý (VD: `Km16+000-Km25+000`) |
| **200 - Định vị** | `202-Vị trí theo dự án` | Địa điểm / Gói thầu dự án (VD: `Tỉnh Tây Ninh`) |
| **200 - Định vị** | `203-Tọa độ X`, `204-Tọa độ Y`, `205-Cao độ` | Tự động trích xuất tọa độ thiết kế $(X, Y, Z)$ thực tế bằng đơn vị Mét |
| **300 - Hình học** | `301-Chiều rộng`, `302-Chiều dài`, `303-Chiều cao` | Tự động đọc kích thước thực tế từ Family / BoundingBox (m) |
| **400 - Vật liệu** | `401-Vật liệu thiết kế` (+ Cường độ, Mô đun, Màu sắc) | Nhập trên Dynamo Player và tổng hợp đồng bộ vào `Comments` |

---

## 🛠️ Công Cụ Phụ Trợ Xử Lý Bề Mặt 3D (CAD / LandXML / IFC)

Ngoài các script chạy trực tiếp trong Dynamo Player, thư mục `src/` còn cung cấp bộ công cụ xử lý tọa độ & bề mặt địa hình 3D bằng PowerShell + C# (`src/TinSurface.cs`):

1. **Nội suy dữ liệu CAD 2D lên bề mặt 3D LandXML (`src/export_atgt_3d_data.ps1`)**:
   - Sử dụng `src/export_cad.lsp` trong AutoCAD để xuất danh sách Block (Biển báo) và Polyline (DPC, Tôn sóng, Hàng rào, Vạch sơn) ra file `cad_extracted_data.tsv`.
   - Chạy lệnh PowerShell để nội suy cao độ $Z$ từ bề mặt `.xml` (LandXML) và xuất ra bộ file CSV 3D trong thư mục `output_3d/`:
     ```powershell
     .\src\export_atgt_3d_data.ps1 -CadTsvPath ".\cad_extracted_data.tsv" -XmlPath ".\Data\XML\TOP CAC CAU.xml" -OutputDir ".\output_3d"
     ```

2. **Khớp cao độ cấu kiện theo bề mặt IFC (`src/Match_Ifc_Surface_Elevation.ps1`)**:
   - Đọc lưới tam giác TIN trực tiếp từ file mặt đường `.ifc` và tính toán độ lệch cao độ `Elevation from Level` cho danh sách cấu kiện:
     ```powershell
     .\src\Match_Ifc_Surface_Elevation.ps1 -IfcPath ".\Data\Input\Top tuyến chính.ifc" -ElementsJsonPath ".\elements.json" -OutputJsonPath ".\elevation_updates.json"
     ```

---

## 📂 Cấu Trúc Thư Mục

```text
Tool-ATGT/
├── product/                                             # 📦 THƯ MỤC SẢN PHẨM (Trỏ Dynamo Player vào đây)
│   ├── [LENH ATGT] RAI DAI PHAN CACH - TON SONG.dyn     # Dynamo: Rải Dải phân cách & Lưới chống chói
│   ├── [LENH ATGT] RAI TON SONG HO LAN.dyn              # Dynamo: Rải Tôn lượn sóng hộ lan
│   ├── [LENH ATGT] RAI HANG RAO.dyn                     # Dynamo: Rải Hàng rào bảo vệ ATGT
│   ├── [LENH ATGT] RAI HANG RAO - TUY CHON FAMILY.dyn   # Dynamo: Rải cấu kiện với Dropdown chọn Family bất kỳ
│   ├── [LENH ATGT] GAN LOI - THONG TIN BIM.dyn          # Dynamo: Gán thông tin BIM LOI hàng loạt
│   ├── ATGT_Revit2025_Automation.dyn                    # Dynamo: Tổng hợp tự động hóa Revit 2025
│   └── HUONG_DAN_SU_DUNG.md                             # Tài liệu chi tiết thuật toán & thông số chuyên sâu
├── src/                                                 # 💻 MÃ NGUỒN LÕI (Python, C#, PowerShell, AutoLISP)
│   ├── Import_ATGT_To_Revit.py                          # Python Engine: Rải DPC & chuẩn hóa 3D Polyline
│   ├── Rai_Ton_Song_Revit.py                            # Python Engine: Rải Tôn sóng hộ lan 3D
│   ├── Rai_Hang_Rao_Revit.py                            # Python Engine: Rải Hàng rào bảo vệ 3D
│   ├── Rai_Hang_Rao_Tuy_Chon_Family_Revit.py            # Python Engine: Rải Family tùy chọn đa năng
│   ├── Gan_LOI_ATGT_Revit.py                            # Python Engine: Gán Shared Parameters & LOI BIM
│   ├── TinSurface.cs                                    # Thư viện C# xử lý lưới tam giác TIN (LandXML & IFC)
│   ├── export_atgt_3d_data.ps1                          # Script nội suy cao độ CAD + LandXML sang 3D CSV
│   ├── Match_Ifc_Surface_Elevation.ps1                  # Script khớp cao độ cấu kiện lên mặt đường IFC
│   └── export_cad.lsp                                   # AutoLISP trích xuất dữ liệu bình đồ ATGT từ AutoCAD
├── testing/                                             # 🧪 KIỂM THỬ & CHẨN ĐOÁN DỮ LIỆU CAD
│   ├── *.lsp                                            # Các script AutoLISP kiểm tra toạ độ, bounding box, polyline
│   └── *.scr                                            # Các script chạy batch kiểm thử trên AutoCAD
└── README.md                                            # 📖 Tài liệu hướng dẫn sử dụng tổng quan
```

---

## ❓ Câu Hỏi Thường Gặp & Xử Lý Sự Cố (FAQ)

<details>
<summary><b>1. Tại sao sau khi bấm Run, cấu kiện bị xoay ngang 90 độ vuông góc với tuyến?</b></summary>

- Do hệ trục cơ sở (Local Origin) lúc tạo Family `.rfa` đặt chiều dài dọc theo trục Y thay vì trục X.
- **Cách khắc phục**:
  - Với tool Dải phân cách: Nhập `90` hoặc `-90` vào mục **`8. GOC XOAY BU (Do)`**.
  - Với tool Tôn sóng / Hàng rào: Thuật toán đã tự động căn chỉnh vector tiếp tuyến; nếu hướng mặt bị ngược chỉ cần đổi mục **`8. DAO CHIEU MAT 180 DO`** sang `Co`.
</details>

<details>
<summary><b>2. Bấm Run nhiều lần khi chỉnh sửa thông số có làm chồng đè nhiều lớp Family lên nhau không?</b></summary>

- **Không.** Toàn bộ các công cụ trong bộ Tool ATGT đều được trang bị cơ chế **Automatic Corridor Purge** (Tự động dọn dẹp hành lang tuyến). Trước khi đặt đốt mới, tool tự động quét và xóa sạch các cấu kiện cũ thuộc cùng tuyến đó.
</details>

<details>
<summary><b>3. Đường Polyline trong file CAD bị lỗi một vài điểm đầu/cuối rơi về cao độ Z = 0 thì sao?</b></summary>

- Hàm `clean_path_elevations()` trong Python Engine sẽ tự động phát hiện các đỉnh có `Z = 0` bất thường trên đường 3D Polyline và tự động nội suy cao độ từ các đỉnh thực địa liền kề, ngăn chặn hoàn toàn hiện tượng cấu kiện bị cắm thẳng xuống mặt phẳng `Z = 0`.
</details>

<details>
<summary><b>4. Tool báo không tìm thấy đối tượng đường dẫn khi chọn khối CAD Import?</b></summary>

- Hãy kiểm tra mục **`9. TEN LAYER CAD`**:
  - Để trống `""` (hoặc xóa tên layer đang nhập) để tool tự động quét mọi layer có chứa đường Polyline trong khối CAD bạn vừa pick.
  - Hoặc kiểm tra chính xác tên Layer chứa đường tim trong AutoCAD (ví dụ: `DPC`, `TS`, `HR`, `0_Ranh giua`) và nhập đúng tên đó vào mục số 9.
</details>

---

## 📄 Giấy Phép & Liên Hệ

- **Repository**: [https://github.com/Iris126-VNE/Tool-ATGT.git](https://github.com/Iris126-VNE/Tool-ATGT.git)
- Phát triển phục vụ tự động hóa thiết kế & triển khai BIM Hạ tầng Giao thông trên Autodesk Revit.

# Cáº¨M NANG HÆ¯á»šNG DáºªN Bá»˜ TOOL ATGT & Gáº®N LOI BIM TRONG REVIT 2025

Bá»™ cÃ´ng cá»¥ **ATGT Revit 2025** bao gá»“m 2 giáº£i phÃ¡p tá»± Ä‘á»™ng hÃ³a chuyÃªn sÃ¢u dÃ nh cho cÃ¡c dá»± Ã¡n háº¡ táº§ng giao thÃ´ng (Cao tá»‘c, Quá»‘c lá»™, ÄÆ°á»ng Ä‘Ã´ thá»‹):
1. **`[LENH ATGT] RAI DAI PHAN CACH - TON SONG.dyn`**: Tá»± Ä‘á»™ng ráº£i cáº¥u kiá»‡n bÃ¡m 100% theo 3D Polyline tráº¯c Ä‘á»‹a (tá»« CAD/Revit) theo **thuáº­t toÃ¡n dÃ¢y cung ná»‘i tiáº¿p (Chord-Based Sequential Placement)**, **kháº¯c phá»¥c triá»‡t Ä‘á»ƒ lá»—i lá»‡ch tim vÃ  chá»“ng Ä‘Ã¨ Ä‘á»‘i tÆ°á»£ng**, Ä‘á»“ng thá»i **tá»± Ä‘á»™ng gáº¯n thÃ´ng tin LOI chuáº©n BIM** ngay khi táº¡o má»›i.
2. **`[LENH ATGT] GAN LOI - THONG TIN BIM.dyn`**: QuÃ©t chá»n hÃ ng loáº¡t cáº¥u kiá»‡n Ä‘Ã£ cÃ³ sáºµn trong mÃ´ hÃ¬nh Ä‘á»ƒ Ä‘Ã¡nh mÃ£ liÃªn tá»¥c theo lÃ½ trÃ¬nh vÃ  cáº­p nháº­t thÃ´ng tin LOI (GÃ³i tháº§u, LÃ½ trÃ¬nh, Váº­t liá»‡u, TiÃªu chuáº©n, NhÃ  tháº§u, TÃ¬nh tráº¡ng nghiá»‡m thu).

---

## I. NGUYÃŠN NHÃ‚N & CÃCH KHáº®C PHá»¤C Lá»†CH TIM & CHá»’NG Äá»I TÆ¯á»¢NG

Trong phiÃªn báº£n cáº­p nháº­t nÃ y, tool Ä‘Ã£ Ä‘Æ°á»£c nÃ¢ng cáº¥p thuáº­t toÃ¡n toÃ¡n há»c hÃ¬nh há»c 3D Ä‘á»ƒ giáº£i quyáº¿t triá»‡t Ä‘á»ƒ 2 váº¥n Ä‘á» lá»›n:

1. **Kháº¯c phá»¥c lá»—i Chá»“ng Ä‘á»‘i tÆ°á»£ng (Anti-Clash & Snap má»‘i ná»‘i 100%)**:
   - **TrÆ°á»›c Ä‘Ã¢y**: Äá»‘t Ä‘Æ°á»£c Ä‘áº·t táº¡i tÃ¢m phÃ¢n Ä‘oáº¡n vá»›i gÃ³c xoay tiáº¿p tuyáº¿n táº¡i tÃ¢m. TrÃªn cÃ¡c cung Ä‘Æ°á»ng cong, 2 Ä‘áº§u Ä‘á»‘t bá»‹ vá»ƒnh ra ngoÃ i, gÃ³c xoay khÃ¡c nhau khiáº¿n má»‘i ná»‘i giÃ¡p mi giá»¯a 2 Ä‘á»‘t bá»‹ gÃ£y gÃ³c chá»¯ V vÃ  Ä‘Ã¢m xuyÃªn/chá»“ng láº¥n vÃ o nhau.
   - **Hiá»‡n táº¡i**: Ãp dá»¥ng **Thuáº­t toÃ¡n DÃ¢y cung 3D ná»‘i tiáº¿p (Chord-based)**:
     - Äiá»ƒm cuá»‘i ($P_{end}$) cá»§a Ä‘á»‘t trÆ°á»›c chÃ­nh lÃ  Ä‘iá»ƒm Ä‘áº§u ($P_{start}$) cá»§a Ä‘á»‘t sau (khi khe há»Ÿ = 0).
     - ToÃ n bá»™ cÃ¡c Ä‘á»‘t káº¿t ná»‘i vá»›i nhau khÃ­t khao nhÆ° toa tÃ u, bÃ¡m sÃ¡t tá»«ng Ä‘á»‰nh tim Polyline, **cháº¥m dá»©t hoÃ n toÃ n hiá»‡n tÆ°á»£ng chá»“ng Ä‘á»‘i tÆ°á»£ng**.
   - **Tá»± Ä‘á»™ng xÃ³a sáº¡ch Ä‘á»‘i tÆ°á»£ng cÅ© (Clean Replacement)**: TrÆ°á»›c khi ráº£i má»›i, tool tá»± Ä‘á»™ng quÃ©t vÃ  xÃ³a sáº¡ch 100% cÃ¡c cáº¥u kiá»‡n ATGT cÅ© Ä‘Ã£ ráº£i dá»c theo tuyáº¿n (trÃ¡nh viá»‡c ngÆ°á»i dÃ¹ng báº¥m Run nhiá»u láº§n lÃ m chá»“ng nhiá»u lá»›p lÃªn nhau).

2. **Kháº¯c phá»¥c lá»—i Lá»‡ch tim Polyline & Bá»• sung [KHOáº¢NG Lá»†CH TIM]**:
   - **CÄƒn chuáº©n tÃ¢m Ä‘á»‘t**: Tá»a Ä‘á»™ Ä‘áº·t Family Ä‘Æ°á»£c tÃ­nh chÃ­nh xÃ¡c báº±ng trung Ä‘iá»ƒm hÃ¬nh há»c cá»§a Ä‘oáº¡n dÃ¢y cung 3D $(P_{start} + P_{end}) / 2$.
   - **Bá»• sung thÃ´ng sá»‘ [10. KHOáº¢NG Lá»†CH TIM Máº¶T Báº°NG (m)]**:
     - `0.0`: Máº·c Ä‘á»‹nh, cáº¥u kiá»‡n náº±m chuáº©n xÃ¡c 100% trÃ¹ng tim Polyline Ä‘Æ°á»£c chá»n.
     - Sá»‘ dÆ°Æ¡ng `> 0` (vÃ­ dá»¥ `+0.25`, `+0.5`): Tá»± Ä‘á»™ng tá»‹nh tiáº¿n Ä‘á»‘t sang **bÃªn PHáº¢I** theo hÆ°á»›ng tuyáº¿n.
     - Sá»‘ Ã¢m `< 0` (vÃ­ dá»¥ `-0.25`, `-0.5`): Tá»± Ä‘á»™ng tá»‹nh tiáº¿n Ä‘á»‘t sang **bÃªn TRÃI** theo hÆ°á»›ng tuyáº¿n.
     - *á»¨ng dá»¥ng*: Cá»±c ká»³ há»¯u Ã­ch khi báº£n váº½ CAD chá»‰ cÃ³ Ä‘Æ°á»ng mÃ©p bÃ³ vá»‰a/dáº£i phÃ¢n cÃ¡ch (cáº§n dá»‹ch vÃ o giá»¯a), hoáº·c khi Family cÃ³ gá»‘c Ä‘áº·t á»Ÿ cáº¡nh mÃ©p cáº§n bÃ¹ trá»« tÃ¢m.

> [!IMPORTANT]
> **LÆ¯U Ã CHáº¾ Äá»˜ CHáº Y TRONG DYNAMO**:
> LuÃ´n kiá»ƒm tra á»Ÿ gÃ³c dÆ°á»›i bÃªn trÃ¡i cá»­a sá»• Dynamo: hÃ£y Ä‘áº£m báº£o cháº¿ Ä‘á»™ Ä‘ang lÃ  **Manual** (Thá»§ cÃ´ng). Tuyá»‡t Ä‘á»‘i **khÃ´ng Ä‘á»ƒ Automatic**, vÃ¬ Automatic sáº½ kÃ­ch hoáº¡t táº¡o má»›i liÃªn tá»¥c má»—i khi báº¡n gÃµ má»™t phÃ­m sá»‘, dá»… gÃ¢y Ä‘Ã¨ Ä‘á»‘i tÆ°á»£ng.

---

## II. Báº¢NG THÃ”NG Sá» TRÃŠN DYNAMO PLAYER (`[LENH ATGT] RAI DAI PHAN CACH - TON SONG`)

Khi má»Ÿ **Dynamo Player** trong Revit vÃ  click biá»ƒu tÆ°á»£ng **Inputs**, báº£ng Ä‘iá»u khiá»ƒn sáº½ hiá»ƒn thá»‹ Ä‘áº§y Ä‘á»§ cÃ¡c thÃ´ng sá»‘:

| STT | TÃªn má»¥c trÃªn Dynamo Player | Thao tÃ¡c & MÃ´ táº£ chi tiáº¿t | GiÃ¡ trá»‹ máº·c Ä‘á»‹nh |
| :---: | :--- | :--- | :--- |
| **1** | **1. CHON TIM TUYEN / MO HINH (Click Select)** | Báº¥m **Select** -> Click chá»n Ä‘á»‘i tÆ°á»£ng Ä‘Æ°á»ng dáº«n (Khá»‘i CAD Import `DPC.dwg`, 3D Polyline, DirectShape, hoáº·c Model Line `LI`). | `None` |
| **2** | **2. CHON KIEU FAMILY (DPC / Ton Song / Luoi / Rao)** | Chá»n kiá»ƒu Family mong muá»‘n trong mÃ´ hÃ¬nh (`Q2P_DPC_KM52-60`, `DPC_L=5M`, `DPC_L=3M`, `TS-ZZ-GUA`, v.v.). Há»— trá»£ cáº£ Family dáº¡ng Ä‘iá»ƒm vÃ  Line-based. | `Q2P_DPC_KM52-60` |
| **3** | **3. CHIEU DAI DOT L / BUOC RAI (m) [DPC: 5.0m, Ton: 4.0m]** | Chiá»u dÃ i cá»§a 1 phÃ¢n Ä‘oáº¡n cáº¥u kiá»‡n.<br>â€¢ Dáº£i phÃ¢n cÃ¡ch: `5.0` (hoáº·c `3.0`, `2.0`, `1.0`)<br>â€¢ TÃ´n sÃ³ng há»™ lan: `4.0` (hoáº·c `2.0`) | `3.0` |
| **4** | **4. CHIEU CAO DOT H (m) [DPC: 0.9m, Ton: 0.7m]** | Chiá»u cao thÃ¢n Ä‘á»‘t DPC (tá»± Ä‘á»™ng gÃ¡n vÃ o tham sá»‘ kÃ­ch thÆ°á»›c Family). | `0.9` |
| **5** | **5. BE RONG DAY DOT W (m) [DPC: 0.6m]** | Bá» rá»™ng Ä‘Ã¡y thÃ¢n Ä‘á»‘t DPC. | `0.6` |
| **6** | **6. KHE HO / DO LONG MONG NGAM (m) [0.0: khit, >0: ho]** | â€¢ KhÃ­t sÃ¡t nhau: `0.0`<br>â€¢ Khe co giÃ£n: `+0.01` Ä‘áº¿n `+0.02` ($1 - 2\text{cm}$)<br>â€¢ Má»™ng ngÃ m Ã¢m dÆ°Æ¡ng lá»“ng vÃ o nhau: nháº­p sá»‘ Ã¢m (vÃ­ dá»¥ `-0.05`). | `0.01` |
| **7** | **7. CAO DO Z OFFSET (m) [0.0: mat duong, +0.9m: tren DPC]** | â€¢ Ráº£i sÃ¡t máº·t Ä‘Æ°á»ng: `0.0`<br>â€¢ Ráº£i LÆ°á»›i chá»‘ng chÃ³i trÃªn Ä‘á»‰nh DPC: `+0.9` (báº±ng chiá»u cao $H$). | `0.0` |
| **8** | **8. GOC XOAY BU (Do) [0.0: Song song tim tuyen; nhap 90, -90 neu can]** | GÃ³c xoay bá»• sung. Máº·c Ä‘á»‹nh `0.0` Ä‘Ã£ tá»± Ä‘á»™ng xoay chiá»u dÃ i Ä‘á»‘t dá»c song song theo hÆ°á»›ng dÃ¢y cung tim Ä‘Æ°á»ng. Náº¿u Family bá»‹ quay ngang thÃ¬ nháº­p `90` hoáº·c `-90`. | `0.0` |
| **9** | **9. TEN LAYER CAD [Bo trong = Tu dong nhan theo Family]** | Äá»ƒ trá»‘ng Ä‘á»ƒ tool tá»± Ä‘á»™ng nháº­n diá»‡n layer trong file CAD (`DPC`, `0_Ranh giua`, `C-TOPO-FEAT`, `TS`, `HR`, ...), hoáº·c nháº­p tÃªn layer CAD cá»¥ thá»ƒ. | `""` *(Ä‘á»ƒ trá»‘ng)* |
| **10** | **10. KHOANG LECH TIM MAT BANG (m) [0.0: Dung tim; >0: Sang phai, <0: Sang trai]** | Khoáº£ng cÃ¡ch dá»‹ch chuyá»ƒn tim Ä‘á»‘t so vá»›i Ä‘Æ°á»ng Polyline Ä‘Æ°á»£c chá»n.<br>â€¢ `0.0`: Náº±m chÃ­nh xÃ¡c 100% trÃªn tim Ä‘Æ°á»ng Polyline.<br>â€¢ `> 0`: Dá»‹ch sang bÃªn PHáº¢I theo hÆ°á»›ng tuyáº¿n.<br>â€¢ `< 0`: Dá»‹ch sang bÃªn TRÃI theo hÆ°á»›ng tuyáº¿n. | `0.0` |

---

## III. CÃC BÆ¯á»šC THá»°C HIá»†N TRÃŠN REVIT

1. Má»Ÿ Revit -> VÃ o tab **Manage** -> Má»Ÿ **Dynamo Player**.
2. Chá»n thÆ° má»¥c chá»©a tool: `g:\My Drive\1.Work\ATGT\Tool ATGT`.
3. Báº¥m vÃ o icon **Inputs** (chá»‰nh sá»­a Ä‘áº§u vÃ o) cá»§a tool `[LENH ATGT] RAI DAI PHAN CACH - TON SONG`.
4. Táº¡i **Má»¥c 1**: Báº¥m **Select** -> Click chá»n khá»‘i CAD Import hoáº·c Ä‘Æ°á»ng 3D Polyline trÃªn khung nhÃ¬n 3D View.
5. Táº¡i **Má»¥c 2**: Chá»n Family (`DPC_L=3M`, `DPC_L=5M`...).
6. Kiá»ƒm tra **Má»¥c 3 - 6**: Äáº·t chiá»u dÃ i Ä‘á»‘t $L=3.0\text{m}$, khe há»Ÿ $= 0.0$ hoáº·c $0.01\text{m}$.
7. Náº¿u cáº§n dá»‹ch tim sang trÃ¡i/pháº£i, nháº­p sá»‘ vÃ o **Má»¥c 10**.
8. Báº¥m nÃºt **Play (Run)**.
   - *Káº¿t quáº£*: ToÃ n bá»™ cÃ¡c Ä‘á»‘t cáº¥u kiá»‡n Ä‘Æ°á»£c ráº£i tháº³ng táº¯p, khá»›p khÃ­t 100% tá»«ng má»‘i ná»‘i, khÃ´ng bá»‹ chá»“ng Ä‘Ã¨, chuáº©n cao Ä‘á»™ 3D vÃ  tá»± Ä‘á»™ng mang mÃ£ LOI BIM.
---

## IV. HUONG DAN CHUYEN BIET: TOOL RAI TON SONG HO LAN (`[LENH ATGT] RAI TON SONG HO LAN.dyn`)

Day la cong cu chuyen dung de rai **Ton luon song ho lan (W-Beam Guardrail)** dua tren Family tieu chuan **`TS-ZZ-GUA.rfa`** (Type `KM52_60` hoac `TS-ZZ-GUA`) voi kha nang tuy bien ben tuyen tuyet doi:

### 1. Bang thong so dieu khien tren Dynamo Player

| STT | Ten thong so | Tuy chon & Y nghia | Mac dinh |
| :---: | :--- | :--- | :--- |
| **1** | **1. CHON TIM TUYEN / MO HINH** | Click **Select** -> Chon CAD Import (file `Ton luon song.dwg`), ModelCurve, hoac 3D Polyline. | `None` |
| **2** | **2. CHON KIEU FAMILY TON SONG** | Ten Family Symbol ton song trong du an (hoac tu dong load tu `Data\02_TON HO LAN\Family\TS-ZZ-GUA.rfa`). | `TS-ZZ-GUA` |
| **3** | **3. VI TRI BEN TUYEN (Phai / Trai / Ca hai ben)** | **Dieu chinh ben tuyen**:<br>â€¢ `Phai`: Rai le phai, mat ton tu dong quay sang trai huong vao long duong.<br>â€¢ `Trai`: Rai le trai, mat ton tu dong quay sang phai huong vao long duong.<br>â€¢ `Ca hai ben`: Rai dong thoi 2 ben le duong, mat ton 2 ben deu huong vao tim duong. | `Phai` |
| **4** | **4. KHOANG CACH LECH TIM / MEP DUONG (m)** | â€¢ Neu pick duong tim duong (Centerline): Nhap khoang cach tu tim ra le (vi du `12.0`m).<br>â€¢ Neu pick duong mep le / Polyline layer TS co san: Nhap `0.0`m. | `0.0` |
| **5** | **5. BUOC RAI / CHIEU DAI DOT TON L (m)** | Chieu dai dot ton / buoc cot tieu chuan (TCVN 12681: `4.0`m, hoac `2.0`m cho doan duong cong ban kinh nho). | `4.0` |
| **6** | **6. CHIEU CAO DINH TON H (m)** | Chieu cao dinh ton so voi mat duong / le duong (`0.75`m). | `0.75` |
| **7** | **7. CAO DO Z OFFSET (m)** | Do cao tinh chinh theo chieu dung ($Z$) so voi cao do polyline CAD. | `0.0` |
| **8** | **8. DAO CHIEU MAT TON 180 DO (Khong / Co)** | â€¢ `Khong`: Su dung goc quay tu dong theo thuat toan ben tuyen.<br>â€¢ `Co`: Xoay nguoc mat ton 180 do (neu huong polyline ve nguoc chieu xe chay). | `Khong` |
| **9** | **9. TEN LAYER CAD [Mac dinh = TS]** | Tu dong loc cac polyline ton song tren layer CAD (mac dinh `TS`). | `TS` |
| **10** | **10. MA TIEN TO LOI BIM** | Tien to ma cau kien tu dong danh so tang dan: `TS-KM52-0001`, `TS-KM52-0002`... | `TS-KM52-` |
| **11** | **11. GOI THAU VA LY TRINH** | Thong tin goi thau va doan ly trinh quan ly. | `Goi thau XL01 | Km52+000 - Km60+000` |

### 2. Nguyen ly xoay va huong mat ton song
- **Mat cong luon song (W-beam face)** bat buoc phai huong ve phia long duong (traffic lane) de dam bao xe va cham truot an toan.
- **Cot do va thanh chong (Posts)** phai nam o phia ngoai (ve phia taluy/le duong).
- Tool da tich hop cong thuc hinh hoc vector phap tuyen mat bang:
  $$\vec{N}_{phai} = \left(\frac{\Delta Y}{L_{2D}}, -\frac{\Delta X}{L_{2D}}\right), \quad \vec{N}_{trai} = -\vec{N}_{phai}$$
  Gup mat ton luon quay chinh xac 100% vao long duong ma ky su khong can phai xoay thu cong tung tam!
### 3. Tinh nang moi cap nhat: Thang voi nhau, Bam do doc 3D & Khong trung Family

- **Thang voi nhau theo tuyen (Collinear & Flush Tangent)**:
  - Khac phuc triet de tinh trang cac tam ton song bi quay ngang 90 do giong rang luoc.
  - He thong tu dong can chinh vector tiep tuyen giua 2 diem dau - cuoi cua tung dot ton 4.0m, giup toan bo cac tam ton nam thang hang, lien tuc va noi tiep khit khao.
- **Bam sat do doc 3D cua Polyline (Pitch angle)**:
  - Tinh toan goc doc doc $\alpha = \text{atan2}(\Delta Z, L_{2D})$ theo do doc cua 3D Polyline / CAD topo.
  - Tuan thu tuyet doi chieu doc thiet ke cua tuyen duong, cac dot ton nghieng deu theo doc doc doc va dong bo tham so cao do.
- **Khong bao gio trung Family khi chay lai (Automatic Corridor Purge)**:
  - Moi khi an Play / Run trong Dynamo, tool tu dong quet va xoa sach cac tam ton song cu cua tuyen nay truoc khi tao moi.
  - Loai bo 100% loi chong nhieu lop family len cung mot vi tri khi ky su thay doi thong so hoac chay lai nhieu lan.

---

## V. HUONG DAN CHUYEN BIET: TOOL RAI HANG RAO BAO VE (`[LENH ATGT] RAI HANG RAO.dyn`)

Day la cong cu chuyen dung de rai **Hang rao bao ve hanh lang ATGT (Hang rao thep gai / Luoi B40 / Fence)** dua tren Family tieu chuan **`GDXM-KM16+000-KM25+000-ZZ-FE_BW.rfa`** (Category `Structural Framing`, hoac cac Family Hang Rao dang Point-Based / Line-Based khac trong du an).

### 1. Bang thong so dieu khien tren Dynamo Player

| STT | Ten thong so | Tuy chon & Y nghia | Mac dinh |
| :---: | :--- | :--- | :--- |
| **1** | **1. CHON TIM TUYEN / MO HINH** | Click **Select** -> Chon CAD Import (layer `HR`), ModelCurve, DirectShape, hoac 3D Polyline ranh hanh lang. | `None` |
| **2** | **2. CHON KIEU FAMILY HANG RAO** | Ten Family Hang Rao trong du an (tu dong nhan dien hoac load tu `Data\03_HANG RAO\GDXM-KM16+000-KM25+000-ZZ-FE_BW.rfa`). | `GDXM-KM16+000-KM25+000-ZZ-FE_BW` |
| **3** | **3. VI TRI BEN TUYEN (Phai / Trai / Ca hai ben)** | **Dieu chinh ben tuyen**:<br>• `Phai`: Rai le phai / ranh GPMB phai.<br>• `Trai`: Rai le trai / ranh GPMB trai.<br>• `Ca hai ben`: Rai dong thoi 2 ben ranh hanh lang bao ve cua tuyen. | `Phai` |
| **4** | **4. KHOANG CACH LECH TIM / MEP DUONG (m)** | • Neu pick duong ranh hang rao / Layer HR co san: Nhap `0.0`m.<br>• Neu pick duong tim tuyen (Centerline): Nhap khoang cach tu tim ra ranh hang rao (vi du `15.0`m, `20.0`m). | `0.0` |
| **5** | **5. BUOC RAI / CHIEU DAI DOT RAO L (m)** | Khoang cach buoc coc / chieu dai 1 dot hang rao (TCVN ve hang rao cao toc: mac dinh `2.5`m, hoac `2.0`m, `3.0`m). | `2.5` |
| **6** | **6. CHIEU CAO HANG RAO H (m)** | Chieu cao hang rao so voi mat dat tu nhien / le duong (`1.8`m hoac `1.5`m, `1.2`m). | `1.8` |
| **7** | **7. CAO DO Z OFFSET (m)** | Do cao tinh chinh theo chieu dung ($Z$) so voi cao do polyline CAD / dia hinh. | `0.0` |
| **8** | **8. DAO CHIEU MAT RAO 180 DO (Khong / Co)** | • `Khong`: Su dung huong mac dinh.<br>• `Co`: Xoay nguoc mat hang rao 180 do neu can. | `Khong` |
| **9** | **9. TEN LAYER CAD [Mac dinh = HR]** | Tu dong loc cac polyline hang rao tren layer CAD (mac dinh `HR`). | `HR` |
| **10** | **10. MA TIEN TO LOI BIM** | Tien to ma cau kien tu dong danh so tang dan: `HR-KM16-0001`, `HR-KM16-0002`... | `HR-KM16-` |
| **11** | **11. GOI THAU VA LY TRINH** | Thong tin goi thau va doan ly trinh quan ly. | `Goi thau XL01 | Km16+000 - Km25+000` |

### 2. Cac dac tinh ky thuat vuot troi cua Tool Hang Rao
1. **Ho tro da dang Family (Hybrid Beam & Point-Based)**:
   - Tu dong nhan dien loai Family: Neu la `Structural Framing` (Line-Based Beam) nhu `FE_BW.rfa`, tool se tao doi tuong noi tiep khit khao giua 2 diem dau - cuoi.
   - Neu la Family dang diem (Point-Based Post / Coc BTCT), tool se tu dong dat tai vi tri trung diem va xoay dung goc tiep tuyen tuyen.
2. **Bam sat cao do dia hinh 3D & do doc doc**:
   - Dong bo truc tiep tham so cao do dau va cuoi dot dAM (`STRUCTURAL_BEAM_END0_ELEVATION`, `STRUCTURAL_BEAM_END1_ELEVATION`) giup hang rao uon luon mem mai theo dia hinh thuc te doc tuyen cao toc.
3. **Tu dong don dep tuyen (Corridor Purge)**:
   - Khi nhan chay lai, he thong tu dong phat hien va xoa sach cac dot hang rao cu tren cung tuyen, khong bao gio bi loi trung lap hay chong nhieu lop family.
4. **Dong bo thong tin LOI BIM**:
   - Gan san Mark, Ly trinh thuc te Km, Goi thau, Tieu chuan ket cau vao tham so Comments phuc vu nghiem thu va quan ly du lieu BIM.

---

## VI. HUONG DAN CHUYEN BIET: TOOL RAI HANG RAO & CAU KIEN TUY CHON FAMILY (`[LENH ATGT] RAI HANG RAO - TUY CHON FAMILY.dyn`)

Day la phien ban nang cap dac biet, cho phep ky su **tuy chon bat ky Family nao trong Revit** thong qua danh sach tha (**Dropdown Menu**) tren Dynamo Player. Ngoai Hang rao thep gai `FE_BW`, cong cu co the rai moi loai Hang rao (B40, coc BTCT), Ton song, Dai phan cach, Coc tieu, Lan can theo tuyen voi day du tinh nang chuyen sau:

### 1. Bang thong so dieu khien tren Dynamo Player

| STT | Ten thong so | Tuy chon & Y nghia | Mac dinh |
| :---: | :--- | :--- | :--- |
| **1** | **1. CHON TIM TUYEN / MO HINH** | Click **Select** -> Chon 3D Polyline, CAD Import (Layer `HR`, `TS`, `DPC`...), DirectShape, ModelCurve. | `None` |
| **2** | **2. CHON KIEU FAMILY (Dropdown)** | **Menu tha chon bat ky Family Type nao trong Revit**: Hang rao thep gai, B40, Coc BTCT, Ton song `TS-ZZ-GUA`, `DPC_L=3M`, Coc tieu... | `GDXM-KM16+000-KM25+000-ZZ-FE_BW` |
| **3** | **3. VI TRI BEN TUYEN (Phai / Trai / Ca hai ben)** | `Phai`: Le phai / ranh GPMB phai.<br>`Trai`: Le trai / ranh GPMB trai.<br>`Ca hai ben`: Rai dong thoi 2 ben ranh tuyen. | `Phai` |
| **4** | **4. KHOANG CACH LECH TIM / MEP DUONG (m)** | • Bắt theo tim duong: Nhap khoang cach ra ranh rào (vi du `15.0`m, `20.0`m).<br>• Bắt theo duong ranh CAD: Nhap `0.0`m. | `0.0` |
| **5** | **5. BUOC RAI / CHIEU DAI DOT L (m)** | Buoc chia dot cau kien:<br>• Hang rao: `2.5`m (hoac `2.0`m, `3.0`m)<br>• Ton song ho lan: `4.0`m<br>• Dai phan cach: `3.0`m hoac `5.0`m | `2.5` |
| **6** | **6. CHIEU CAO CAU KIEN H (m)** | Chieu cao cau kien:<br>• Hang rao: `1.8`m hoac `1.5`m<br>• Ton song: `0.75`m<br>• Dai phan cach: `0.9`m | `1.8` |
| **7** | **7. CAO DO Z OFFSET (m)** | Do cao tinh chinh theo phuong dung so voi cao do polyline CAD / dia hinh. | `0.0` |
| **8** | **8. DAO CHIEU MAT CAU KIEN 180 DO (Khong / Co)** | `Khong`: Huong mac dinh theo chieu tuyen.<br>`Co`: Dao chieu mat cau kien 180 do. | `Khong` |
| **9** | **9. TEN LAYER CAD [Bo trong = Nhan toan bo]** | De trong de tu dong nhan tat ca layer trong file CAD, hoac nhap `HR`, `TS`, `DPC`... | `""` *(De trong)* |
| **10** | **10. MA TIEN TO LOI BIM [Bo trong = Tu dong]** | De trong de tool tu dong lay tien to theo ten Family (vi du `FE_BW-`, `TS-`, `DPC-`), hoac nhap tien to rieng. | `""` *(Tu dong)* |
| **11** | **11. GOI THAU VA LY TRINH** | Thong tin goi thau va doan ly trinh quan ly BIM. | `Goi thau XL01 \| Km0+000 - Km60+000` |

### 2. Tinh nang chuyen sau cua Tool Tuy Chon Family
- **Engine nhan dien Family da nang (Smart Adaptive Engine)**:
  - Neu nguoi dung chon Family dang **Structural Framing (Beam)** hoac **Line-Based**: Tool tao doan dầm 3D noi tiep giua diem dau va diem cuoi theo buoc $L$, tu dong dong bo tham so do doc doc (`END0_ELEVATION`, `END1_ELEVATION`).
  - Neu nguoi dung chon Family dang **Point-Based (Generic Model, Column, Coc tieu...)**: Tool dat tai vi tri trung diem/dau dot, tu dong dong bo cao do $Z$ thuc dia va xoay goc Yaw tiep tuyen voi tim duong.
- **Tu dong don dep Family tuong ung (Family-Specific Corridor Purge)**:
  - Khi chay lai cho Family A, tool chi don dep cac doi tuong cu cua Family A tren tuyen, hoan toan khong anh huong den cac Family khac (B, C) da rai truoc do.
- **Linh hoat tuy bien thong so**:
  - Tu do dieu chinh buoc rai $L$, chieu cao $H$, offset lech tim mat bang va chieu cao $Z$ cho bat ky chung loai cau kien giao thong nao.
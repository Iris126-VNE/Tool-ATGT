# -*- coding: utf-8 -*-
# ==============================================================================
# TOOL GAN LEVEL OF INFORMATION (LOI) & THONG TIN BIM CHO MO HINH ATGT TRONG REVIT
# He thong thong so chuan theo Form BIM Giao Thong / TCVN / Quyet dinh 1056/QD-BXD:
#   100-THAM SO DINH DANH: 101-Ma cau kien, 102-Phan loai, 105-Mo ta cau kien...
#   200-THAM SO DINH VI:   201-Vi tri khu vuc, 202-Vi tri du an, 203-X, 204-Y, 205-Cao do
#   300-THAM SO HINH HOC:  301-Rong, 302-Dai, 303-Cao, 304-Hinh dang thiet ke
#   400-THAM SO VAT LIEU:  401-Vat lieu, 402-Cuong do, 403-Mo dun dan hoi, 406-Mau sac
# ==============================================================================

import sys
import math
import re
import traceback

# ------------------------------------------------------------------------------
# KHOI TAO REVIT API & DYNAMO ENVIRONMENT
# ------------------------------------------------------------------------------
IS_DYNAMO = False
try:
    import clr
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    clr.AddReference('RevitServices')

    from Autodesk.Revit.DB import *
    from Autodesk.Revit.UI import *
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
    IS_DYNAMO = True
except Exception:
    pass


# ------------------------------------------------------------------------------
# CAC HAM HO TRO UNWRAP VA DỌC THONG TIN REVIT
# ------------------------------------------------------------------------------
def unwrap_elements(input_data):
    """Giai phong UnwrapElement cho danh sach doi tuong tu Dynamo"""
    if input_data is None:
        return []

    raw_list = []
    if isinstance(input_data, (list, tuple)):
        raw_list = list(input_data)
    else:
        raw_list = [input_data]

    unwrapped = []
    for item in raw_list:
        if item is None:
            continue
        if hasattr(item, "InternalElement"):
            unwrapped.append(item.InternalElement)
        elif hasattr(item, "Id"):
            unwrapped.append(item)
        elif isinstance(item, (list, tuple)):
            unwrapped.extend(unwrap_elements(item))

    return unwrapped


def get_element_location_and_coords(elem):
    """
    Lay toa do tam thiet ke (X, Y, Z) tinh bang METERS tu doi tuong Revit.
    Ho tro LocationPoint, LocationCurve va BoundingBox.
    """
    loc = getattr(elem, "Location", None)
    
    # 1. LocationPoint (Point-based family)
    if isinstance(loc, LocationPoint):
        pt = loc.Point
        return pt, pt.X * 0.3048, pt.Y * 0.3048, pt.Z * 0.3048

    # 2. LocationCurve (Line-based family, Beam, StructuralFraming)
    if isinstance(loc, LocationCurve):
        c = loc.Curve
        if c:
            p0 = c.GetEndPoint(0)
            p1 = c.GetEndPoint(1)
            mid = (p0 + p1) * 0.5
            return mid, mid.X * 0.3048, mid.Y * 0.3048, mid.Z * 0.3048

    # 3. Fallback: BoundingBox center
    try:
        bbox = elem.get_BoundingBox(None)
        if bbox:
            mid = (bbox.Min + bbox.Max) * 0.5
            return mid, mid.X * 0.3048, mid.Y * 0.3048, mid.Z * 0.3048
    except Exception:
        pass

    return None, 0.0, 0.0, 0.0


def sort_elements_along_corridor(elements):
    """
    Sap xep cac doi tuong doc theo truc chinh cua tuyen (Corridor Principal Axis).
    Dam bao so thu tu (001, 002, 003...) tang dan deu dan theo huong tuyen.
    """
    if not elements or len(elements) <= 1:
        return elements

    pts_with_elem = []
    without_loc = []

    for el in elements:
        pt, x_m, y_m, z_m = get_element_location_and_coords(el)
        if pt is not None:
            pts_with_elem.append((pt, x_m, y_m, z_m, el))
        else:
            without_loc.append(el)

    if len(pts_with_elem) <= 1:
        return elements

    # Tim 2 diem xa nhat de xac dinh truc tuyen
    min_x_pt = min(pts_with_elem, key=lambda it: it[1])
    max_x_pt = max(pts_with_elem, key=lambda it: it[1])
    min_y_pt = min(pts_with_elem, key=lambda it: it[2])
    max_y_pt = max(pts_with_elem, key=lambda it: it[2])

    span_x = abs(max_x_pt[1] - min_x_pt[1])
    span_y = abs(max_y_pt[2] - min_y_pt[2])

    if span_x >= span_y:
        p_start = min_x_pt[0]
        p_end = max_x_pt[0]
    else:
        p_start = min_y_pt[0]
        p_end = max_y_pt[0]

    vx = p_end.X - p_start.X
    vy = p_end.Y - p_start.Y
    v_len = math.sqrt(vx * vx + vy * vy)
    if v_len > 1e-4:
        vx /= v_len
        vy /= v_len
    else:
        vx, vy = 1.0, 0.0

    # Chieu toa do len truc tuyen de sap xep
    pts_with_elem.sort(key=lambda it: (it[0].X - p_start.X) * vx + (it[0].Y - p_start.Y) * vy)

    sorted_elems = [it[4] for it in pts_with_elem]
    sorted_elems.extend(without_loc)
    return sorted_elems


# ------------------------------------------------------------------------------
# HAM GAN THAM SO SMART (PREFIX & EXACT MATCHING, HO TRO STRING/DOUBLE/INT)
# ------------------------------------------------------------------------------
def apply_param_value(param, value, is_metric_length=False):
    """Gan gia tri vao tham so Revit theo dung kieu du lieu StorageType"""
    if param is None or param.IsReadOnly or value is None:
        return False

    st = getattr(param, "StorageType", None)
    st_name = str(st)

    try:
        if "String" in st_name:
            if isinstance(value, float):
                param.Set("{0:.3f}".format(value))
            else:
                param.Set(str(value))
            return True
        elif "Double" in st_name:
            val_f = float(value)
            if is_metric_length:
                # Revit luu tru chieu dai noi bo la FEET: 1 foot = 0.3048 m
                param.Set(val_f / 0.3048)
            else:
                param.Set(val_f)
            return True
        elif "Integer" in st_name:
            param.Set(int(value))
            return True
    except Exception:
        pass

    return False


def set_element_param_smart(inst, prefix_tag, candidate_names, value, is_metric_length=False):
    """
    Tim kiem va gan gia tri cho tham so trong Revit.
    Uu tien:
    1. Tim dung ten tham so theo LookupParameter (nhanh nhat)
    2. Tim tham so bat dau bang prefix_tag (VD: '101-', '201-', '301-', '401-')
    3. Quet tat ca tham so theo ten chuan hoa (bo dau cach, gach duoi, hoa thuong)
    """
    if inst is None or value is None:
        return False

    # 1. Lookup theo danh sach ten tham so
    for name in candidate_names:
        try:
            p = inst.LookupParameter(name)
            if p and not p.IsReadOnly:
                if apply_param_value(p, value, is_metric_length):
                    return True
        except Exception:
            pass

    # 2. Quet theo Prefix Tag (VD: '101-', '201-', '301-')
    if prefix_tag:
        clean_prefix = prefix_tag.lower().strip()
        try:
            for p in inst.Parameters:
                if p and not p.IsReadOnly and p.Definition:
                    p_name_lower = p.Definition.Name.lower().strip()
                    if p_name_lower.startswith(clean_prefix):
                        if apply_param_value(p, value, is_metric_length):
                            return True
        except Exception:
            pass

    # 3. Quet Parameters theo dang normalized
    try:
        norm_cands = [c.lower().replace("_", "").replace(" ", "").replace("-", "") for c in candidate_names]
        for p in inst.Parameters:
            if p and not p.IsReadOnly and p.Definition:
                p_norm = p.Definition.Name.lower().replace("_", "").replace(" ", "").replace("-", "")
                if p_norm in norm_cands:
                    if apply_param_value(p, value, is_metric_length):
                        return True
    except Exception:
        pass

    return False


# ------------------------------------------------------------------------------
# TRICH XUAT KICH THUOC HINH HOC (WIDTH, LENGTH, HEIGHT, SHAPE)
# ------------------------------------------------------------------------------
def extract_element_dimensions(inst):
    """
    Lay kich thuoc hinh hoc (m) tu Family Instance, Symbol hoac BoundingBox.
    Tra ve: width_m, length_m, height_m, shape_desc
    """
    width_m = None
    length_m = None
    height_m = None

    # Danh sach ten tham so chieu dai/rong/cao
    w_cands = ["Width", "Rộng", "Chiều rộng", "B", "W", "Bề rộng", "Chiều rộng thiết kế", "301-Chiều rộng thiết kế"]
    l_cands = ["Length", "Dài", "Chiều dài", "L", "Span", "Chiều dài thiết kế", "302-Chiều dài thiết kế"]
    h_cands = ["Height", "Cao", "Chiều cao", "H", "Chiều cao thiết kế", "303-Chiều cao thiết kế"]

    def _lookup_geom_param(host, candidates):
        if not host:
            return None
        for name in candidates:
            try:
                p = host.LookupParameter(name)
                if p and p.HasValue:
                    st_name = str(p.StorageType)
                    if "Double" in st_name:
                        return p.AsDouble() * 0.3048
                    elif "String" in st_name:
                        return float(p.AsString())
            except Exception:
                pass
        return None

    # 1. Kiem tra Instance parameters
    width_m = _lookup_geom_param(inst, w_cands)
    length_m = _lookup_geom_param(inst, l_cands)
    height_m = _lookup_geom_param(inst, h_cands)

    # 2. Kiem tra Symbol (Type) parameters neu instance chua co
    symbol = getattr(inst, "Symbol", None)
    if symbol:
        if width_m is None:
            width_m = _lookup_geom_param(symbol, w_cands)
        if length_m is None:
            length_m = _lookup_geom_param(symbol, l_cands)
        if height_m is None:
            height_m = _lookup_geom_param(symbol, h_cands)

    # 3. Tinh toan tu BoundingBox neu chua tim thay
    try:
        bbox = inst.get_BoundingBox(None)
        if bbox:
            dx = abs(bbox.Max.X - bbox.Min.X) * 0.3048
            dy = abs(bbox.Max.Y - bbox.Min.Y) * 0.3048
            dz = abs(bbox.Max.Z - bbox.Min.Z) * 0.3048

            if length_m is None:
                length_m = max(dx, dy)
            if width_m is None:
                width_m = min(dx, dy)
            if height_m is None:
                height_m = dz
    except Exception:
        pass

    # Gia tri mac dinh chuan ATGT neu khong tinh duoc
    if width_m is None or width_m <= 0:
        width_m = 0.310
    if length_m is None or length_m <= 0:
        length_m = 4.000
    if height_m is None or height_m <= 0:
        height_m = 0.750

    # Xac dinh mo ta hinh dang dua tren loai cau kien
    fam_name = getattr(symbol, "FamilyName", "") if symbol else ""
    inst_name = getattr(inst, "Name", "")
    full_name = (fam_name + " " + inst_name).lower()

    if any(k in full_name for k in ["lcc", "luoi", "lưới", "chong choi", "chống chói"]):
        shape_desc = "Khung lưới chống chói 2 trụ định hình (TCVN 12681:2019)"
    elif any(k in full_name for k in ["ton", "song", "sóng", "guard", "ho lan", "hộ lan", "w-beam"]):
        shape_desc = "Tấm tôn lượn sóng chữ W 2 bước sóng (TCVN 12681:2019)"
    elif any(k in full_name for k in ["dpc", "phan cach", "phân cách", "barrier", "new jersey"]):
        shape_desc = "Dải phân cách bê tông định hình New Jersey (TCVN 12681:2019)"
    elif any(k in full_name for k in ["rao", "hang rao", "hàng rào", "fence", "b40"]):
        shape_desc = "Hàng rào lưới thép mạ kẽm B40 định hình"
    elif any(k in full_name for k in ["bien", "biển", "sign"]):
        shape_desc = "Biển báo hiệu đường bộ định hình (QCVN 41:2019/BGTVT)"
    else:
        shape_desc = "Cấu kiện an toàn giao thông định hình"

    return width_m, length_m, height_m, shape_desc


# ------------------------------------------------------------------------------
# HAM CHINH: GAN FORM LOI BIM CHO TAT CA CAC DOI TUONG
# ------------------------------------------------------------------------------
def assign_bim_loi_form(document, elements, prefix="TS-LCC-", cat_class="An toàn giao thông",
                        elem_desc="Lưới chống chói", station_loc="Km16+000-Km25+000",
                        project_loc="Tỉnh Tây Ninh", material="Thép mạ kẽm nhúng nóng",
                        strength="SS400", elastic_mod="2.1x10^5 MPa", color="Xanh lục / Bạc mạ kẽm"):
    """
    Gan dong loat form thong tin LOI BIM theo dung giao dien Data:
      101-Ma cau kien: TS-LCC-001 / TS-HTS-001 (So thu tu 3 chu so)
      102-Phan loai cau kien: An toan giao thong
      105-Mo ta cau kien: Luoi chong choi / Ton ho lan
      201-Vi tri theo khu vuc: Km16+000-Km25+000
      202-Vi tri theo du an: Tinh Tay Ninh
      203-Toa do X thiet ke: X (m)
      204-Toa do Y thiet ke: Y (m)
      205-Cao do thiet ke: Z (m)
      301-Chieu rong thiet ke: W (m)
      302-Chieu dai thiet ke: L (m)
      303-Chieu cao thiet ke: H (m)
      304-Hinh dang thiet ke: Mo ta kieu dang
      401-Vat lieu thiet ke: Thep ma kem nhung nong
      402-Cuong do thiet ke: SS400
      403-Mo dun dan hoi: 2.1x10^5 MPa
      406-Mau sac: Bac ma kem
    """
    if not elements or len(elements) == 0:
        return 0, "", []

    # Xu ly tien to ma va so thu tu khoi dau
    base_prefix = prefix
    start_seq = 1
    m = re.match(r'^(.*?)(\d+)$', prefix.strip())
    if m:
        base_prefix = m.group(1)
        start_seq = int(m.group(2))
    elif not base_prefix.endswith('-') and not base_prefix.endswith('_'):
        base_prefix += '-'

    # Sap xep tang dan deu dan doc theo tuyen
    sorted_elems = sort_elements_along_corridor(elements)
    count = 0
    errors = []

    first_code = "{0}{1:03d}".format(base_prefix, start_seq)
    last_code = first_code

    for i, inst in enumerate(sorted_elems):
        try:
            curr_seq = start_seq + i
            mark_code = "{0}{1:03d}".format(base_prefix, curr_seq)
            last_code = mark_code

            # 1. Lay toa do thiet ke (X, Y, Z) tinh bang met
            pt, x_m, y_m, z_m = get_element_location_and_coords(inst)

            # 2. Trich xuat kich thuoc va hinh dang hinh hoc
            width_m, length_m, height_m, shape_desc = extract_element_dimensions(inst)

            # 3. Xac dinh mo ta cau kien neu de trong hoac tu dong
            curr_elem_desc = elem_desc
            if not curr_elem_desc or curr_elem_desc.strip().lower() in ["", "auto", "tu dong"]:
                sym = getattr(inst, "Symbol", None)
                fn = (getattr(sym, "FamilyName", "") + " " + getattr(inst, "Name", "")).lower()
                if any(k in fn for k in ["lcc", "luoi", "lưới", "chong choi", "chống chói"]):
                    curr_elem_desc = "Lưới chống chói"
                elif any(k in fn for k in ["ton", "song", "guard", "ho lan"]):
                    curr_elem_desc = "Tôn hộ lan"
                elif any(k in fn for k in ["dpc", "phan cach", "barrier"]):
                    curr_elem_desc = "Dải phân cách"
                elif any(k in fn for k in ["rao", "fence"]):
                    curr_elem_desc = "Hàng rào"
                elif any(k in fn for k in ["bien", "sign"]):
                    curr_elem_desc = "Biển báo"
                else:
                    curr_elem_desc = "Cấu kiện an toàn giao thông"

            # 4. Gan BuiltInParameter chuan cua Revit
            # 4.1. BuiltInParameter.ALL_MODEL_MARK: Ma cau kien
            try:
                p_mark = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if p_mark and not p_mark.IsReadOnly:
                    p_mark.Set(mark_code)
            except Exception:
                pass

            # 4.2. BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS: Tong hop thong tin LOI
            loi_summary = (
                "[BIM LOI] Mã: {0} | Phân loại: {1} | Mô tả: {2} | "
                "Khu vực: {3} | Dự án: {4} | Tọa độ: ({5:.2f}, {6:.2f}, {7:.2f}) | "
                "Vật liệu: {8} | Cường độ: {9} | Màu: {10}"
            ).format(
                mark_code, cat_class, curr_elem_desc,
                station_loc, project_loc, x_m, y_m, z_m,
                material, strength, color
            )
            try:
                p_comm = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if p_comm and not p_comm.IsReadOnly:
                    p_comm.Set(loi_summary)
            except Exception:
                pass

            # 5. Gan CAC THAM SO THEO FORM BIM (Group Data 100, 200, 300, 400)
            # --- 100-THAM SO DINH DANH ---
            set_element_param_smart(inst, "101-", ["101-Mã cấu kiện", "101-Ma cau kien", "Mã cấu kiện", "Ma_Cau_Kien", "BIM_Code"], mark_code)
            set_element_param_smart(inst, "102-", ["102-Phân loại cấu kiện", "102-Phan loai cau kien", "Phân loại cấu kiện", "Phan_Loai_Cau_Kien"], cat_class)
            set_element_param_smart(inst, "105-", ["105-Mô tả cấu kiện", "105-Mo ta cau kien", "Mô tả cấu kiện", "Mo_Ta_Cau_Kien", "Description"], curr_elem_desc)

            # --- 200-THAM SO DINH VI ---
            set_element_param_smart(inst, "201-", ["201-Vị trí theo khu vực", "201-Vi tri theo khu vuc", "Vị trí theo khu vực", "Lý trình", "Ly_Trinh"], station_loc)
            set_element_param_smart(inst, "202-", ["202-Vị trí theo dự án", "202-Vi tri theo du an", "Vị trí theo dự án", "Gói thầu", "Goi_Thau", "Dự án"], project_loc)
            set_element_param_smart(inst, "203-", ["203-Tọa độ X thiết kế", "203-Toa do X thiet ke", "Tọa độ X thiết kế", "Coordinate_X"], x_m, is_metric_length=True)
            set_element_param_smart(inst, "204-", ["204-Tọa độ Y thiết kế", "204-Toa do Y thiet ke", "Tọa độ Y thiết kế", "Coordinate_Y"], y_m, is_metric_length=True)
            set_element_param_smart(inst, "205-", ["205-Cao độ thiết kế", "205-Cao do thiet ke", "Cao độ thiết kế", "Elevation"], z_m, is_metric_length=True)

            # --- 300-THAM SO HINH HOC ---
            set_element_param_smart(inst, "301-", ["301-Chiều rộng thiết kế", "301-Chieu rong thiet ke", "Chiều rộng thiết kế", "Width"], width_m, is_metric_length=True)
            set_element_param_smart(inst, "302-", ["302-Chiều dài thiết kế", "302-Chieu dai thiet ke", "Chiều dài thiết kế", "Length"], length_m, is_metric_length=True)
            set_element_param_smart(inst, "303-", ["303-Chiều cao thiết kế", "303-Chieu cao thiet ke", "Chiều cao thiết kế", "Height"], height_m, is_metric_length=True)
            set_element_param_smart(inst, "304-", ["304-Hình dạng thiết kế", "304-Hinh dang thiet ke", "Hình dạng thiết kế"], shape_desc)

            # --- 400-THAM SO VAT LIEU ---
            set_element_param_smart(inst, "401-", ["401-Vật liệu thiết kế", "401-Vat lieu thiet ke", "Vật liệu thiết kế", "Vật liệu", "Material"], material)
            set_element_param_smart(inst, "402-", ["402-Cường độ thiết kế", "402-Cuong do thiet ke", "Cường độ thiết kế", "Strength"], strength)
            set_element_param_smart(inst, "403-", ["403-Mô đun đàn hồi", "403-Mo dun dan hoi", "Mô đun đàn hồi", "Elastic_Modulus"], elastic_mod)
            set_element_param_smart(inst, "406-", ["406-Màu sắc", "406-Mau sac", "Màu sắc", "Color"], color)

            count += 1
        except Exception as ex:
            if len(errors) < 5:
                errors.append(str(ex))

    summary_code = "{0} -> {1}".format(first_code, last_code)
    return count, summary_code, errors


# ------------------------------------------------------------------------------
# ENTRY POINT DYNAMO
# ------------------------------------------------------------------------------
if IS_DYNAMO:
    # IN[0]: Loc/Doi tuong (Select Elements, FamilyInstance list, filter string, hoac de trong de lay tat ca)
    input_0 = IN[0] if len(IN) > 0 else None

    # IN[1] -> IN[9]: Cac thong tin Form LOI do nguoi dung nhap tren Dynamo Player
    prefix_val      = str(IN[1]).strip() if len(IN) > 1 and IN[1] is not None and str(IN[1]).strip() != "" else "TS-HTS-"
    category_val    = str(IN[2]).strip() if len(IN) > 2 and IN[2] is not None and str(IN[2]).strip() != "" else "An toàn giao thông"
    elem_desc_val   = str(IN[3]).strip() if len(IN) > 3 and IN[3] is not None and str(IN[3]).strip() != "" else "Tôn hộ lan"
    station_val     = str(IN[4]).strip() if len(IN) > 4 and IN[4] is not None and str(IN[4]).strip() != "" else "Km16+000-Km25+000"
    project_loc_val = str(IN[5]).strip() if len(IN) > 5 and IN[5] is not None and str(IN[5]).strip() != "" else "Tỉnh Tây Ninh"
    material_val    = str(IN[6]).strip() if len(IN) > 6 and IN[6] is not None and str(IN[6]).strip() != "" else "Thép mạ kẽm nhúng nóng"
    strength_val    = str(IN[7]).strip() if len(IN) > 7 and IN[7] is not None and str(IN[7]).strip() != "" else "SS400"
    modulus_val     = str(IN[8]).strip() if len(IN) > 8 and IN[8] is not None and str(IN[8]).strip() != "" else "2.1x10^5 MPa"
    color_val       = str(IN[9]).strip() if len(IN) > 9 and IN[9] is not None and str(IN[9]).strip() != "" else "Bạc mạ kẽm"

    
# ------------------------------------------------------------------------------
# TU DONG KHOI TAO & LIEN KET THAM SO LOI (DATA) VAO DU AN REVIT
# ------------------------------------------------------------------------------
def ensure_shared_parameters_bound(document):
    """
    Tu dong kiem tra, chi giu lai 9 tham so LOI BIM theo BEP du an GD-XM cho ATGT
    va xoa cac tham so LOI khong lien quan de giam nhe kich thuoc file.
    """
    bep_keep_names = set([
        "101-Mã cấu kiện",
        "102-Phân loại cấu kiện",
        "105-Mô tả cấu kiện",
        "201-Vị trí theo khu vực",
        "202-Vị trí theo dự án",
        "301-Chiều rộng thiết kế",
        "302-Chiều dài thiết kế",
        "303-Chiều cao thiết kế",
        "401-Vật liệu thiết kế"
    ])

    # Xoa cac SharedParameterElement khong lien quan (nhom 100..406 du thua hoac -PRE cu)
    try:
        sp_elems = FilteredElementCollector(document).OfClass(SharedParameterElement).ToElements()
        del_ids = []
        for sp_el in sp_elems:
            nm = getattr(sp_el, "Name", "") or ""
            if nm not in bep_keep_names:
                if nm[:4] in ["100-", "103-", "104-", "200-", "203-", "204-", "205-", "300-", "304-", "305-", "306-", "307-", "308-", "309-", "400-", "402-", "403-", "404-", "405-", "406-"] or "-PRE" in nm:
                    del_ids.append(sp_el.Id)
        for did in del_ids:
            try:
                document.Delete(did)
            except Exception:
                pass
    except Exception:
        pass

    sp_path = r"G:\My Drive\1.Work\ATGT\Tool ATGT\Data\4_LUOI CHONG CHOI\SharedParameters_ATGT_LOI.txt"
    if not os.path.exists(sp_path):
        return

    revit_app = getattr(document, "Application", None)
    if not revit_app:
        return

    orig_sp = revit_app.SharedParametersFilename
    try:
        revit_app.SharedParametersFilename = sp_path
        sp_file = revit_app.OpenSharedParameterFile()
        if not sp_file:
            return

        # Tap hop cac Category can gan tham so
        cats = revit_app.Create.NewCategorySet()
        cat_enums = [
            BuiltInCategory.OST_StructuralFraming,
            BuiltInCategory.OST_GenericModel,
            BuiltInCategory.OST_Columns
        ]
        for c_enum in cat_enums:
            try:
                c = document.Settings.Categories.get_Item(c_enum)
                if c:
                    cats.Insert(c)
            except Exception:
                pass

        binding = revit_app.Create.NewInstanceBinding(cats)

        # Quet cac tham so da ton tai trong document
        existing_names = set()
        iterator = document.ParameterBindings.ForwardIterator()
        while iterator.MoveNext():
            try:
                existing_names.add(iterator.Key.Name)
            except Exception:
                pass

        # Nhom tham so: thu GroupTypeId.Data (Revit 2024+) hoac BuiltInParameterGroup.PG_DATA
        group_id = None
        try:
            group_id = GroupTypeId.Data
        except Exception:
            try:
                group_id = BuiltInParameterGroup.PG_DATA
            except Exception:
                pass

        for grp in sp_file.Groups:
            for p_def in grp.Definitions:
                if p_def.Name in bep_keep_names and p_def.Name not in existing_names:
                    try:
                        if group_id is not None:
                            document.ParameterBindings.Insert(p_def, binding, group_id)
                        else:
                            document.ParameterBindings.Insert(p_def, binding)
                    except Exception:
                        pass
    except Exception:
        pass
    finally:
        try:
            if orig_sp:
                revit_app.SharedParametersFilename = orig_sp
        except Exception:
            pass

    TransactionManager.Instance.EnsureInTransaction(doc)
    ensure_shared_parameters_bound(doc)

    elements = []

    # 1. Kiem tra xem nguoi dung co dang quet chon doi tuong truc tiep trong Revit khong
    if uidoc and uidoc.Selection:
        try:
            sel_ids = uidoc.Selection.GetElementIds()
            if sel_ids and sel_ids.Count > 0:
                for s_id in sel_ids:
                    el = doc.GetElement(s_id)
                    if el and not el.ViewSpecific:
                        elements.append(el)
        except Exception:
            pass

    # 2. Neu Revit Selection rong, kiem tra dau vao IN[0]
    if len(elements) == 0 and input_0 is not None:
        if isinstance(input_0, (list, tuple)) and len(input_0) > 0:
            elements = unwrap_elements(input_0)
        elif hasattr(input_0, "InternalElement") and isinstance(input_0.InternalElement, FamilySymbol):
            sym_id = input_0.InternalElement.Id
            filter_inst = FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType().ToElements()
            elements = [inst for inst in filter_inst if inst.Symbol.Id == sym_id]
        elif isinstance(input_0, FamilySymbol):
            filter_inst = FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType().ToElements()
            elements = [inst for inst in filter_inst if inst.Symbol.Id == input_0.Id]
        elif hasattr(input_0, "Id") or hasattr(input_0, "InternalElement"):
            elements = unwrap_elements(input_0)

    # 3. Neu van rong (hoac IN[0] la chuoi filter hoac de trong), tu dong quet toan bo cau kien ATGT
    if len(elements) == 0:
        filter_str = str(input_0).strip().lower() if input_0 is not None and isinstance(input_0, (str, bytes)) else ""
        
        # Quet qua 3 Category chinh chua cau kien ATGT
        cat_list = [
            BuiltInCategory.OST_GenericModel,
            BuiltInCategory.OST_StructuralFraming,
            BuiltInCategory.OST_Columns
        ]
        
        all_candidates = []
        for cat in cat_list:
            try:
                col = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().ToElements()
                all_candidates.extend(col)
            except Exception:
                pass

        keywords = ["ton", "song", "sóng", "guard", "ho lan", "hộ lan", "dpc", "phan cach", "phân cách", "barrier", "rao", "hang rao", "hàng rào", "fence", "bien", "biển", "sign", "atgt", "q2p", "luoi", "lưới", "chong choi", "chống chói", "ts-zz"]

        for e in all_candidates:
            e_name = (getattr(e, "Name", "") or "").lower()
            sym = getattr(e, "Symbol", None)
            f_name = (getattr(sym, "FamilyName", "") or "").lower() if sym else ""
            comb = e_name + " " + f_name

            if filter_str and filter_str not in ["", "all", "tat ca"]:
                if filter_str in comb:
                    elements.append(e)
            else:
                if any(kw in comb for kw in keywords):
                    elements.append(e)

    # Thuc thi gan thong tin
    if len(elements) > 0:
        assigned_count, code_range, errs = assign_bim_loi_form(
            doc, elements,
            prefix=prefix_val,
            cat_class=category_val,
            elem_desc=elem_desc_val,
            station_loc=station_val,
            project_loc=project_loc_val,
            material=material_val,
            strength=strength_val,
            elastic_mod=modulus_val,
            color=color_val
        )
        TransactionManager.Instance.TransactionTaskDone()

        report_lines = [
            "=" * 60,
            "THANH CONG: DA GAN FORM THONG TIN BIM LOI CHO {0} CAU KIEN!".format(assigned_count),
            "=" * 60,
            "- Khoang ma cau kien (101): [{0}]".format(code_range),
            "- Phan loai cau kien (102): {0}".format(category_val),
            "- Mo ta cau kien      (105): {0}".format(elem_desc_val),
            "- Vi tri khu vuc     (201): {0}".format(station_val),
            "- Vi tri du an       (202): {0}".format(project_loc_val),
            "- Toa do & Cao do (203-205): Tu dong tinh toan chinh xac (m)",
            "- Hinh hoc        (301-304): Tu dong trich xuat Rong x Dai x Cao & Hinh dang",
            "- Vat lieu thiet ke  (401): {0}".format(material_val),
            "- Cuong do thiet ke  (402): {0}".format(strength_val),
            "- Mo dun dan hoi     (403): {0}".format(modulus_val),
            "- Mau sac thiet ke   (406): {0}".format(color_val),
            "- Revit Parameters       : Dong bo ALL_MODEL_MARK & COMMENTS",
            "=" * 60
        ]
        if errs:
            report_lines.append("Luu y mot so thong bao ngoai le: " + " | ".join(errs[:3]))

        OUT = "\n".join(report_lines)
    else:
        TransactionManager.Instance.TransactionTaskDone()
        OUT = (
            "THONG BAO: Khong tim thay doi tuong ATGT phu hop de gan LOI.\n"
            "Huong dan su dung:\n"
            "1. Ban co the quet chon cac doi tuong ATGT trong Revit truoc khi bam Run.\n"
            "2. Hoac nhap ten loai Family can loc vao o input dau tien [0].\n"
            "3. Hoac de trong o [0] de cong cu tu dong tim kiem toan bo cau kien ATGT trong du an!"
        )

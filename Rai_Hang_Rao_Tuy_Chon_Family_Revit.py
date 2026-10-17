# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT: Rai_Hang_Rao_Tuy_Chon_Family_Revit.py
TOOL ATGT DEDICATED: RAI HANG RAO & CAU KIEN ATGT - TUY CHON DA DANG FAMILY
CHUAN MO HINH THUC TE REVIT (STRUCTURAL FRAMING BEAMS, LINE-BASED & POINT-BASED):
  - KHOANG CACH BUOC COC / DOT HANG RAO CHUAN THEO THIET KE TCVN (Mac dinh 2.50m)
  - Ho tro TUY CHON BAT KY FAMILY NAO trong Revit thong qua Dropdown FamilyTypes:
    + Family dầm/thanh rào theo tuyến: GDXM-KM16+000-KM25+000-ZZ-FE_BW, TS-ZZ-GUA, Beams...
    + Family cọc rào / cột BTCT dạng điểm (Point-Based Families)
    + Family dải phân cách (DPC), hộ lan, lan can, lưới chống chói (LCC 2 Trụ), cọc tiêu...
  - Tu dong nhan dien loai Family (Structural Framing, Line-Based, Point-Based, Column)
  - Noi tiep khit khao giua cac dot lien tiep theo ca do doc va cao do 3D (Z)
  - Tu dong lay dung 100% cao do 3D thuc te cua 3D Polyline CAD / Revit
  - Co co che CLEAN_PATH_ELEVATIONS: Tu dong xu ly loi cac dinh Z=0 do ban ve CAD
    de tranh hien tuong Family bi tut/cam xuong mat dat 0.0
  - Co bo loc FILTER_RELEVANT_PATHS: Uu tien tuyet doi tuyen co cao do 3D thuc te
  - Dong bo cao do Point-Based Family bang MoveElement truc tiep theo Location.Point.Z
  - Tu dong stitch/chain cac doan CAD 3D Polyline thanh tuyen lien tuc
  - Tu dong don dep cac FamilyInstance cu cua Family duoc chon tren tuyen (Khong trung lap)
  - Ho tro chon Ben Phai, Ben Trai, Ca hai ben (Ranh GPMB) & Dao chieu 180 do
  - Tu dong gan thong tin LOI BIM tieu chuan cao toc: Ma, Ly trinh Km, Goi thau
================================================================================
"""

import sys
import os
import math

METERS_TO_FEET = 3.28083989501312336

DEBUG_LOG_PATH = r"C:\Users\Admin\.gemini\antigravity-ide\scratch\debug_multi_family.log"

def write_debug_log(msg):
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass

try:
    with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("=== LOG RAI HANG RAO & CAU KIEN ATGT (DA DANG FAMILY) ===\n")
except Exception:
    pass

IS_DYNAMO = False
try:
    import clr
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    clr.AddReference('RevitServices')
    from Autodesk.Revit.DB import *
    from Autodesk.Revit.DB.Structure import StructuralType
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument
    IS_DYNAMO = True
except Exception:
    try:
        from Autodesk.Revit.DB import *
        from Autodesk.Revit.DB.Structure import StructuralType
    except Exception:
        pass


def clean_path_elevations(points):
    """
    Kiem tra va chuan hoa cao do Z cho cac duong 3D Polyline:
    Neu da so cac dinh co cao do thuc dia (|Z| > 0.05 feet ~ 1.5cm), nhung mot so dinh
    dau/cuoi bi loi Z = 0.0 (do ban ve CAD ket hop 2D-3D hoac bat diem mat bang),
    ham se tu dong dien day/noi suy cao do Z tu cac dinh lien ke de tranh hien tuong
    Family bi cam thang xuong mat phang 0.0.
    """
    if not points or len(points) < 2:
        return points

    valid_z_indices = [i for i, p in enumerate(points) if abs(p.Z) > 0.05]

    # Neu toan bo deu la Z=0 (duong 2D) hoac toan bo deu co Z hop le (3D hoan hao), giu nguyen
    if len(valid_z_indices) == 0 or len(valid_z_indices) == len(points):
        return points

    # Neu co it nhat 3 diem hoac >= 10% so diem co Z hop le, coi day la 3D polyline can duoc bao toan cao do
    if len(valid_z_indices) >= 3 or (float(len(valid_z_indices)) / float(len(points))) >= 0.1:
        first_valid_i = valid_z_indices[0]
        last_valid_i = valid_z_indices[-1]

        new_pts = list(points)

        # 1. Dien day cac diem o dau (truoc diem hop le dau tien) bang cao do diem hop le dau tien
        for i in range(first_valid_i):
            new_pts[i] = XYZ(new_pts[i].X, new_pts[i].Y, points[first_valid_i].Z)

        # 2. Dien day cac diem o cuoi (sau diem hop le cuoi cung) bang cao do diem hop le cuoi cung
        for i in range(last_valid_i + 1, len(points)):
            new_pts[i] = XYZ(new_pts[i].X, new_pts[i].Y, points[last_valid_i].Z)

        # 3. Noi suy tuyen tinh cac diem Z=0 nam giua cac diem hop le
        for k in range(len(valid_z_indices) - 1):
            i_start = valid_z_indices[k]
            i_end = valid_z_indices[k + 1]
            if i_end - i_start > 1:
                z_start = points[i_start].Z
                z_end = points[i_end].Z
                total_span = float(i_end - i_start)
                for mid_i in range(i_start + 1, i_end):
                    t = float(mid_i - i_start) / total_span
                    interp_z = z_start + t * (z_end - z_start)
                    new_pts[mid_i] = XYZ(new_pts[mid_i].X, new_pts[mid_i].Y, interp_z)

        return new_pts

    return points


class PolylinePath3D:
    def __init__(self, points, layer_name=""):
        cleaned = []
        for p in points:
            if not cleaned or p.DistanceTo(cleaned[-1]) > 1e-4:
                cleaned.append(p)
        cleaned = clean_path_elevations(cleaned)
        self.points = cleaned
        self.layer_name = layer_name
        self.lengths = []
        self.total_length = 0.0
        self._compute_lengths()

    def _compute_lengths(self):
        self.lengths = [0.0]
        accum = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            seg_len = p1.DistanceTo(p2)
            accum += seg_len
            self.lengths.append(accum)
        self.total_length = accum

    def point_at_distance(self, dist):
        if not self.points:
            return None
        if dist <= 0.0:
            return self.points[0]
        if dist >= self.total_length:
            return self.points[-1]

        for i in range(len(self.lengths) - 1):
            if self.lengths[i] <= dist <= self.lengths[i + 1]:
                seg_len = self.lengths[i + 1] - self.lengths[i]
                if seg_len < 1e-7:
                    return self.points[i]
                t = (dist - self.lengths[i]) / seg_len
                p1 = self.points[i]
                p2 = self.points[i + 1]
                return XYZ(
                    p1.X + t * (p2.X - p1.X),
                    p1.Y + t * (p2.Y - p1.Y),
                    p1.Z + t * (p2.Z - p1.Z)
                )
        return self.points[-1]

    def min_distance_to(self, pt):
        """Tinh khoang cach ngan nhat trong mat bang 2D tu diem pt den duong polyline"""
        if not self.points:
            return 999999.0
        min_d = 999999.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            dx = p2.X - p1.X
            dy = p2.Y - p1.Y
            seg_len_sq = dx * dx + dy * dy
            if seg_len_sq < 1e-8:
                d = math.sqrt((pt.X - p1.X)**2 + (pt.Y - p1.Y)**2)
            else:
                t = max(0.0, min(1.0, ((pt.X - p1.X) * dx + (pt.Y - p1.Y) * dy) / seg_len_sq))
                proj_x = p1.X + t * dx
                proj_y = p1.Y + t * dy
                d = math.sqrt((pt.X - proj_x)**2 + (pt.Y - proj_y)**2)
            if d < min_d:
                min_d = d
        return min_d


def get_symbol_names(symbol):
    f_name = ""
    t_name = ""
    try:
        if hasattr(symbol, "Family") and symbol.Family:
            f_name = symbol.Family.Name
        elif hasattr(symbol, "FamilyName"):
            f_name = str(symbol.FamilyName)
    except Exception:
        pass
    try:
        t_name = symbol.Name
    except Exception:
        pass
    return f_name, t_name


def activate_symbol_safe(sym, document):
    """Kich hoat FamilySymbol an toan trong Transaction cua Revit"""
    if sym is None:
        return
    try:
        TransactionManager.Instance.EnsureInTransaction(document)
        if not sym.IsActive:
            sym.Activate()
            document.Regenerate()
    except Exception:
        pass


def resolve_any_family_symbol(document, family_input):
    """
    Nhan dien linh hoat bat ky FamilySymbol nao tu Input:
    1. Dynamo FamilyType object (tu Dropdown DSRevitNodesUI.FamilyTypes)
    2. FamilySymbol object truc tiep tu Revit API
    3. Chuoi string ten Family / Family Type
    """
    if family_input is None:
        return None

    TransactionManager.Instance.EnsureInTransaction(document)

    if hasattr(family_input, "InternalElement") and family_input.InternalElement is not None:
        sym = family_input.InternalElement
        if isinstance(sym, FamilySymbol):
            activate_symbol_safe(sym, document)
            return sym

    if isinstance(family_input, FamilySymbol):
        activate_symbol_safe(family_input, document)
        return family_input

    target_str = str(family_input).strip()
    if not target_str:
        return None

    target_f = ""
    target_t = ""
    if ":" in target_str:
        parts = target_str.split(":", 1)
        target_f = parts[0].strip().lower()
        target_t = parts[1].strip().lower()
    else:
        target_f = target_str.lower()
        target_t = target_str.lower()

    collector = FilteredElementCollector(document).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()

    if target_f and target_t and target_f != target_t:
        for sym in collector:
            fn, tn = get_symbol_names(sym)
            if fn.lower() == target_f and tn.lower() == target_t:
                activate_symbol_safe(sym, document)
                return sym

    for sym in collector:
        fn, tn = get_symbol_names(sym)
        comb = (fn + " " + tn).lower()
        if target_f in fn.lower() or target_t in tn.lower() or target_t in comb:
            activate_symbol_safe(sym, document)
            return sym

    for sym in collector:
        fn, tn = get_symbol_names(sym)
        for part in target_str.lower().split():
            if len(part) >= 3 and (part in fn.lower() or part in tn.lower()):
                activate_symbol_safe(sym, document)
                return sym

    return None


def get_best_level(document, target_z_feet):
    """Tim Level gan nhat voi cao do target_z_feet"""
    try:
        levels = list(FilteredElementCollector(document).OfClass(Level).ToElements())
        if not levels:
            return None
        return min(levels, key=lambda lvl: abs(lvl.Elevation - target_z_feet))
    except Exception:
        return None


def set_instance_elevation(inst, target_z_feet, base_level=None):
    """
    Dong bo cao do Z thuc te tuyet doi cho doi tuong Revit:
    - Neu doi tuong da o dung cao do target_z_feet (sai so < 3mm), KHONG can lam gi them (tranh loi gap doi cao do).
    - Uu tien di chuyen truc tiep theo truc Z bang MoveElement vi MoveElement thay doi truc tiep Location.Point.Z.
    - Neu bi khoa boi Level/Host, set BuiltInParameter cao do va kiem tra lai vi tri.
    """
    if inst is None:
        return False

    # 1. Kiem tra truoc tien: Neu vi tri Location Point.Z da nam dung target_z_feet (sai so < 3mm)
    try:
        if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
            cur_z = inst.Location.Point.Z
            if abs(cur_z - target_z_feet) < 0.01:
                return True
    except Exception:
        pass

    lvl_elev = base_level.Elevation if base_level else 0.0
    offset_val = target_z_feet - lvl_elev

    # 2. Uu tien di chuyen truc tiep theo truc Z bang MoveElement
    try:
        if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
            cur_z = inst.Location.Point.Z
            diff_z = target_z_feet - cur_z
            ElementTransformUtils.MoveElement(inst.Document, inst.Id, XYZ(0, 0, diff_z))
            new_z = inst.Location.Point.Z
            if abs(new_z - target_z_feet) < 0.01:
                return True
    except Exception:
        pass

    # 3. Neu doi tuong bi khoa boi Level/Host, set BuiltInParameter cao do
    param_list = [
        BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM,
        BuiltInParameter.INSTANCE_ELEVATION_PARAM,
        BuiltInParameter.SCHEDULE_BASE_LEVEL_OFFSET_PARAM,
        BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM,
        BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM
    ]
    for bip in param_list:
        try:
            p = inst.get_Parameter(bip)
            if p and not p.IsReadOnly:
                p.Set(offset_val)
                if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
                    if abs(inst.Location.Point.Z - target_z_feet) < 0.01:
                        return True
        except Exception:
            pass

    # 4. Lookup theo cac ten tham so pho bien
    param_names = [
        "Elevation from Level", "Elevation", "Offset", "Z Offset", "Z_Offset",
        "Host Offset", "Base Offset", "Offset from Host", "Default Elevation", "Cao do"
    ]
    for p_name in param_names:
        try:
            p = inst.LookupParameter(p_name)
            if p and not p.IsReadOnly and p.StorageType == StorageType.Double:
                p.Set(offset_val)
                if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
                    if abs(inst.Location.Point.Z - target_z_feet) < 0.01:
                        return True
        except Exception:
            pass

    # 5. MoveElement fallback neu van chua dung cao do
    try:
        if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
            cur_z = inst.Location.Point.Z
            diff_z = target_z_feet - cur_z
            if abs(diff_z) > 0.005:
                ElementTransformUtils.MoveElement(inst.Document, inst.Id, XYZ(0, 0, diff_z))
                return True
    except Exception:
        pass

    return False


def cleanup_existing_instances_along_paths(document, paths, target_family_name="", max_dist_feet=100.0):
    """Don dep tat ca FamilyInstance cu cua cung Family tren tuyen tranh trung lap khi chay lai."""
    deleted_count = 0
    try:
        all_pts = []
        for p in paths:
            all_pts.extend(p.points)
        if not all_pts:
            return 0

        min_x = min(pt.X for pt in all_pts) - max_dist_feet
        max_x = max(pt.X for pt in all_pts) + max_dist_feet
        min_y = min(pt.Y for pt in all_pts) - max_dist_feet
        max_y = max(pt.Y for pt in all_pts) + max_dist_feet

        collector = FilteredElementCollector(document).OfClass(FamilyInstance).WhereElementIsNotElementType().ToElements()
        to_delete = []
        f_target = target_family_name.lower().strip() if target_family_name else ""

        for inst in collector:
            try:
                pt = None
                loc = getattr(inst, "Location", None)
                if loc:
                    if hasattr(loc, "Point") and loc.Point:
                        pt = loc.Point
                    elif hasattr(loc, "Curve") and loc.Curve:
                        pt = loc.Curve.GetEndPoint(0)

                if pt is None:
                    bb = inst.get_BoundingBox(None)
                    if bb:
                        pt = XYZ((bb.Min.X + bb.Max.X)*0.5, (bb.Min.Y + bb.Max.Y)*0.5, (bb.Min.Z + bb.Max.Z)*0.5)

                if pt is None:
                    continue

                if pt.X < min_x or pt.X > max_x or pt.Y < min_y or pt.Y > max_y:
                    continue

                s_fam_name = ""
                s_type_name = ""
                sym = getattr(inst, "Symbol", None)
                if sym:
                    s_fam_name, s_type_name = get_symbol_names(sym)

                if not s_fam_name:
                    type_id = inst.GetTypeId()
                    if type_id != ElementId.InvalidElementId:
                        elem_type = document.GetElement(type_id)
                        if elem_type:
                            if hasattr(elem_type, "FamilyName"):
                                s_fam_name = str(elem_type.FamilyName).lower()

                is_match = False
                if f_target:
                    if f_target in s_fam_name or s_fam_name in f_target or f_target in s_type_name or s_type_name in f_target:
                        is_match = True

                if is_match:
                    for p in paths:
                        if p.min_distance_to(pt) <= max_dist_feet:
                            to_delete.append(inst.Id)
                            break
            except Exception:
                pass

        if to_delete:
            from System.Collections.Generic import List
            del_list = List[ElementId]()
            for eid in set(to_delete):
                del_list.Add(eid)
            del_res = document.Delete(del_list)
            deleted_count = len(del_res)
            write_debug_log("Da don dep {0} doi tuong cu tren tuyen.".format(deleted_count))
    except Exception as ex:
        write_debug_log("Loi don dep doi tuong cu: " + str(ex))
    return deleted_count


def stitch_segments_into_continuous_paths(segments, tol=0.5):
    """Noi tat ca cac doan thang/curve 3D roi rac thanh cac chuoi Polyline lien tuc."""
    if not segments:
        return []

    remaining = []
    for item in segments:
        if len(item) == 3:
            p0, p1, lyr = item
        else:
            p0, p1 = item[:2]
            lyr = "Stitched_Corridor"
        if p0.DistanceTo(p1) > 1e-4:
            remaining.append([p0, p1, lyr])

    if not remaining:
        return []

    chains = []

    while remaining:
        first_seg = remaining.pop(0)
        current_chain = [first_seg[0], first_seg[1]]
        chain_layer = first_seg[2]

        extended = True
        while extended:
            extended = False
            tail = current_chain[-1]
            best_idx = -1
            best_dist = tol
            reverse_cand = False

            for i, seg in enumerate(remaining):
                d_start = tail.DistanceTo(seg[0])
                d_end = tail.DistanceTo(seg[1])

                if d_start < best_dist:
                    best_dist = d_start
                    best_idx = i
                    reverse_cand = False
                elif d_end < best_dist:
                    best_dist = d_end
                    best_idx = i
                    reverse_cand = True

            if best_idx >= 0:
                seg = remaining.pop(best_idx)
                pts = [seg[0], seg[1]]
                if reverse_cand:
                    pts.reverse()
                current_chain.extend(pts[1:])
                extended = True

        extended = True
        while extended:
            extended = False
            head = current_chain[0]
            best_idx = -1
            best_dist = tol
            prepend_as_is = False

            for i, seg in enumerate(remaining):
                d_end = head.DistanceTo(seg[1])
                d_start = head.DistanceTo(seg[0])

                if d_end < best_dist:
                    best_dist = d_end
                    best_idx = i
                    prepend_as_is = True
                elif d_start < best_dist:
                    best_dist = d_start
                    best_idx = i
                    prepend_as_is = False

            if best_idx >= 0:
                seg = remaining.pop(best_idx)
                pts = [seg[0], seg[1]]
                if not prepend_as_is:
                    pts.reverse()
                current_chain = pts[:-1] + current_chain
                extended = True

        if len(current_chain) >= 2:
            chains.append(PolylinePath3D(current_chain, chain_layer))

    chains.sort(key=lambda c: c.total_length, reverse=True)
    return chains


def extract_paths_from_input(elem, document, layer_filter=""):
    """
    Trich xuat toan bo duong dan tu Element duoc chon trong Dynamo.
    Ho tro: CAD ImportInstance (loc theo layer neu co), PolyLine, PolyCurve, Curve, DirectShape.
    Bao toan 100% tinh lien tuc va cao do 3D cua PolyLine tu CAD.
    """
    if elem is None:
        return []

    raw_list = []
    if isinstance(elem, (list, tuple)):
        for x in elem:
            if isinstance(x, (list, tuple)):
                raw_list.extend(x)
            elif x is not None:
                raw_list.append(x)
    else:
        raw_list.append(elem)

    if len(raw_list) >= 2 and all(hasattr(p, "X") and hasattr(p, "Y") for p in raw_list):
        pts = []
        for p in raw_list:
            z_val = getattr(p, "Z", 0.0)
            pts.append(XYZ(p.X, p.Y, z_val))
        return [PolylinePath3D(pts, "PointList")]

    direct_paths = []
    collected_segments = []

    for item in raw_list:
        if item is None:
            continue

        revit_elem = item
        if hasattr(item, "InternalElement") and item.InternalElement is not None:
            revit_elem = item.InternalElement

        if isinstance(revit_elem, ElementId):
            try:
                revit_elem = document.GetElement(revit_elem)
            except Exception:
                pass

        if hasattr(item, "Curves"):
            try:
                sub_c = item.Curves() if callable(item.Curves) else item.Curves
                pts = []
                for sc in sub_c:
                    p0 = XYZ(sc.StartPoint.X, sc.StartPoint.Y, sc.StartPoint.Z)
                    pts.append(p0)
                if sub_c:
                    p_end = XYZ(sub_c[-1].EndPoint.X, sub_c[-1].EndPoint.Y, sub_c[-1].EndPoint.Z)
                    pts.append(p_end)
                if len(pts) >= 2:
                    direct_paths.append(PolylinePath3D(pts, "DynamoPolyCurve"))
                continue
            except Exception:
                pass

        if hasattr(item, "StartPoint") and hasattr(item, "EndPoint"):
            try:
                p0 = XYZ(item.StartPoint.X, item.StartPoint.Y, item.StartPoint.Z)
                p1 = XYZ(item.EndPoint.X, item.EndPoint.Y, item.EndPoint.Z)
                collected_segments.append((p0, p1, "DynamoCurve"))
                continue
            except Exception:
                pass

        is_poly = False
        try:
            if isinstance(revit_elem, PolyLine) or (hasattr(revit_elem, "GetType") and revit_elem.GetType().Name == "PolyLine"):
                is_poly = True
        except Exception:
            pass

        if is_poly:
            try:
                coords = revit_elem.GetCoordinates()
                if coords and len(coords) >= 2:
                    pts = [XYZ(p.X, p.Y, p.Z) for p in coords]
                    direct_paths.append(PolylinePath3D(pts, "RevitPolyLine"))
                continue
            except Exception:
                pass

        if isinstance(revit_elem, Curve):
            collected_segments.append((revit_elem.GetEndPoint(0), revit_elem.GetEndPoint(1), "RevitCurve"))
            continue

        if hasattr(revit_elem, "get_Geometry"):
            try:
                opt = Options()
                opt.DetailLevel = ViewDetailLevel.Fine
                opt.IncludeNonVisibleObjects = True

                geom = revit_elem.get_Geometry(opt)
                if not geom:
                    opt_def = Options()
                    geom = revit_elem.get_Geometry(opt_def)

                if geom:
                    def parse_geom(g_obj, cur_layer="", transform=None):
                        if g_obj is None:
                            return

                        layer = cur_layer
                        if hasattr(g_obj, "GraphicsStyleId") and g_obj.GraphicsStyleId != ElementId.InvalidElementId:
                            try:
                                gs = document.GetElement(g_obj.GraphicsStyleId)
                                if gs and gs.GraphicsStyleCategory:
                                    layer = gs.GraphicsStyleCategory.Name
                            except Exception:
                                pass

                        if layer_filter and layer:
                            f_clean = layer_filter.strip().lower()
                            if f_clean not in layer.lower():
                                if not isinstance(g_obj, GeometryInstance):
                                    return

                        if isinstance(g_obj, GeometryInstance):
                            inst_geom = None
                            try:
                                inst_geom = g_obj.GetInstanceGeometry()
                            except Exception:
                                pass

                            count_before = len(direct_paths) + len(collected_segments)
                            if inst_geom:
                                for sub_g in inst_geom:
                                    parse_geom(sub_g, layer, None)

                            if (len(direct_paths) + len(collected_segments)) > count_before:
                                return

                            sym_geom = None
                            try:
                                sym_geom = g_obj.GetSymbolGeometry()
                            except Exception:
                                pass

                            inst_tr = g_obj.Transform if hasattr(g_obj, "Transform") else None
                            if transform is not None and inst_tr is not None:
                                current_tr = transform.Multiply(inst_tr)
                            elif inst_tr is not None:
                                current_tr = inst_tr
                            else:
                                current_tr = transform

                            if sym_geom:
                                for sub_g in sym_geom:
                                    parse_geom(sub_g, layer, current_tr)
                            return

                        is_sub_poly = False
                        try:
                            if isinstance(g_obj, PolyLine) or (hasattr(g_obj, "GetType") and g_obj.GetType().Name == "PolyLine"):
                                is_sub_poly = True
                        except Exception:
                            pass

                        if is_sub_poly:
                            try:
                                coords = g_obj.GetCoordinates()
                                if coords and len(coords) >= 2:
                                    pts = [transform.OfPoint(p) if transform else p for p in coords]
                                    direct_paths.append(PolylinePath3D(pts, layer))
                                return
                            except Exception:
                                pass

                        if isinstance(g_obj, Curve):
                            try:
                                c = g_obj.CreateTransformed(transform) if transform else g_obj
                                tess = c.Tessellate()
                                if tess and len(tess) >= 2:
                                    for ti in range(len(tess) - 1):
                                        collected_segments.append((tess[ti], tess[ti + 1], layer))
                                else:
                                    collected_segments.append((c.GetEndPoint(0), c.GetEndPoint(1), layer))
                                return
                            except Exception:
                                pass

                        if hasattr(g_obj, "GetEnumerator") and not isinstance(g_obj, (PolyLine, Curve, Solid)):
                            try:
                                for sub in g_obj:
                                    parse_geom(sub, layer, transform)
                                return
                            except Exception:
                                pass

                    for g in geom:
                        parse_geom(g, "", None)

            except Exception as ex_g:
                write_debug_log("Loi doc Geometry: " + str(ex_g))

    write_debug_log("Direct paths: {0}, Loose segments: {1}".format(len(direct_paths), len(collected_segments)))
    all_paths = list(direct_paths)
    if collected_segments:
        stitched = stitch_segments_into_continuous_paths(collected_segments, tol=0.5)
        all_paths.extend(stitched)

    all_paths.sort(key=lambda p: p.total_length, reverse=True)
    return all_paths


def filter_relevant_paths(paths, fam_name, user_layer=""):
    """
    Loc cac duong Polyline phu hop voi loai Family duoc chon tu file CAD:
    - Neu chi co 1 duong duy nhat: Su dung ngay lap tuc ma khong can loc.
    - Neu co user_layer: Uu tien layer duoc chi dinh boi nguoi dung.
    - Uu tien tuyet doi cac duong co cao do 3D thuc te (|Z| > 0.05 feet hoac Z bien thien doc tuyen).
    - Tu dong loc theo keyword Family & CAD layer: LCC, HR, RAO, FENCE, DPC, TS, C-TOPO-FEAT, TOPO, TIM...
    - Chon cac chuoi tuyen dai nhat co 3D elevation de rai.
    """
    if len(paths) <= 1:
        return paths

    def clean_layer(l_str):
        if not l_str: return ""
        s = l_str.lower().strip()
        if ":" in s:
            s = s.split(":")[-1].strip()
        return s

    # 1. Neu nguoi dung chi dinh ten Layer CAD cu the
    if user_layer and str(user_layer).strip():
        u_layer_clean = clean_layer(str(user_layer))
        matched = [p for p in paths if u_layer_clean in clean_layer(p.layer_name)]
        if len(matched) > 0:
            matched.sort(key=lambda p: p.total_length, reverse=True)
            return matched

    # 2. Uu tien tuyet doi: Cac duong 3D Polyline co cao do thuc te (|Z| > 0.05 hoac Z bien thien doc tuyen)
    paths_with_elevation = []
    for p in paths:
        if len(p.points) >= 2:
            z_vals = [pt.Z for pt in p.points]
            has_z = any(abs(z) > 0.05 for z in z_vals)
            z_range = max(z_vals) - min(z_vals)
            # Duong co cao do Z thuc te (>1.5cm) va tong chieu dai >= 1.0m
            if (has_z or z_range > 0.02) and (p.total_length / METERS_TO_FEET) >= 1.0:
                paths_with_elevation.append(p)

    if len(paths_with_elevation) > 0:
        paths_with_elevation.sort(key=lambda p: p.total_length, reverse=True)
        return paths_with_elevation

    # 3. Tu dong loc theo keyword Family
    fam_lower = fam_name.lower()
    target_keywords = ["c-topo-feat", "topo", "feat", "feature", "lcc", "chong choi", "luoi", "rao", "fence", "dpc", "ts", "ton", "cntr", "tim", "tuyen"]
    if "lcc" in fam_lower or "chong choi" in fam_lower or "luoi" in fam_lower:
        target_keywords = ["c-topo-feat", "topo", "feat", "lcc", "chong choi", "luoi", "dpc", "ranh giua", "cntr"]
    elif "dpc" in fam_lower or "dai" in fam_lower:
        target_keywords = ["c-topo-feat", "topo", "feat", "dpc", "ranh giua", "median", "cntr", "tim"]
    elif "ts" in fam_lower or "ton" in fam_lower:
        target_keywords = ["c-topo-feat", "topo", "feat", "ts", "ton", "song", "guard", "c-road"]
    elif "hr" in fam_lower or "rao" in fam_lower or "fence" in fam_lower:
        target_keywords = ["c-topo-feat", "topo", "feat", "hr", "rao", "fence", "b40"]

    matched_kw = []
    for p in paths:
        p_l = clean_layer(p.layer_name)
        if any(kw in p_l for kw in target_keywords):
            matched_kw.append(p)

    if len(matched_kw) > 0:
        matched_kw.sort(key=lambda p: p.total_length, reverse=True)
        return matched_kw

    # 4. Fallback: tra ve cac duong dai nhat
    paths_sorted = sorted(paths, key=lambda p: p.total_length, reverse=True)
    return paths_sorted


def apply_custom_dimensions(inst, length_m, height_m):
    """Gan thong so chieu dai va chieu cao vao FamilyInstance neu co tham so tuong ung"""
    for l_name in ["L", "Length", "Chieu dai", "DoanRao", "DoanTon", "BuocCot", "KhoangCach", "Span"]:
        try:
            p = inst.LookupParameter(l_name)
            if p and not p.IsReadOnly and p.StorageType == StorageType.Double:
                p.Set(length_m * METERS_TO_FEET)
                break
        except Exception:
            pass
    for h_name in ["H", "Height", "Chieu cao", "DinhRao", "DinhTon", "CaoDoRao", "ChieuCao"]:
        try:
            p = inst.LookupParameter(h_name)
            if p and not p.IsReadOnly and p.StorageType == StorageType.Double:
                p.Set(height_m * METERS_TO_FEET)
                break
        except Exception:
            pass


def apply_loi_param_value(param, value, is_metric_length=False):
    """Gan gia tri vao tham so Revit theo dung kieu du lieu StorageType"""
    if param is None or param.IsReadOnly or value is None:
        return False
    st_name = str(getattr(param, "StorageType", ""))
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


def set_loi_param_smart(inst, prefix_tag, candidate_names, value, is_metric_length=False):
    """Tim kiem va gan gia tri cho tham so trong Revit theo Prefix va Candidate list"""
    if inst is None or value is None:
        return False

    for name in candidate_names:
        try:
            p = inst.LookupParameter(name)
            if p and not p.IsReadOnly:
                if apply_loi_param_value(p, value, is_metric_length):
                    return True
        except Exception:
            pass

    if prefix_tag:
        clean_prefix = prefix_tag.lower().strip()
        try:
            for p in inst.Parameters:
                if p and not p.IsReadOnly and p.Definition:
                    p_name_lower = p.Definition.Name.lower().strip()
                    if p_name_lower.startswith(clean_prefix):
                        if apply_loi_param_value(p, value, is_metric_length):
                            return True
        except Exception:
            pass

    try:
        norm_cands = [c.lower().replace("_", "").replace(" ", "").replace("-", "") for c in candidate_names]
        for p in inst.Parameters:
            if p and not p.IsReadOnly and p.Definition:
                p_norm = p.Definition.Name.lower().replace("_", "").replace(" ", "").replace("-", "")
                if p_norm in norm_cands:
                    if apply_loi_param_value(p, value, is_metric_length):
                        return True
    except Exception:
        pass

    return False


def assign_loi_data(inst, seq_num, station_m, side_label, fam_name="ATGT", prefix="", package="XL01", length_m=2.5, height_m=1.8):
    """Gan ma cau kien va day du form thong tin BIM LOI cho tung dot cau kien"""
    if not prefix:
        clean_fn = fam_name.replace(" ", "_").replace("-", "_")
        prefix = clean_fn[:6].upper() + "-"

    if not prefix.endswith('-') and not prefix.endswith('_'):
        prefix += '-'

    mark_code = "{0}{1:03d}".format(prefix, seq_num)
    try:
        p_mark = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if p_mark and not p_mark.IsReadOnly:
            p_mark.Set(mark_code)
    except Exception:
        pass

    km_val = int(station_m / 1000.0)
    m_val = station_m - (km_val * 1000.0)
    station_str = "Km{0}+{1:06.2f}".format(km_val, m_val)

    # Toa do thuc te (m)
    x_m, y_m, z_m = 0.0, 0.0, 0.0
    loc = getattr(inst, "Location", None)
    if hasattr(loc, "Point"):
        pt = loc.Point
        x_m, y_m, z_m = pt.X * 0.3048, pt.Y * 0.3048, pt.Z * 0.3048
    elif hasattr(loc, "Curve") and loc.Curve:
        mid = (loc.Curve.GetEndPoint(0) + loc.Curve.GetEndPoint(1)) * 0.5
        x_m, y_m, z_m = mid.X * 0.3048, mid.Y * 0.3048, mid.Z * 0.3048

    loi_comments = (
        "[BIM LOI] Mã: {0} | Family: {1} | Vị trí: {2} | Lý trình: {3} | Dự án: {4} | Tọa độ: ({5:.2f}, {6:.2f}, {7:.2f})"
    ).format(mark_code, fam_name, side_label, station_str, package, x_m, y_m, z_m)

    try:
        p_comm = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p_comm and not p_comm.IsReadOnly:
            p_comm.Set(loi_comments)
    except Exception:
        pass

    # Gan he thong tham so BIM theo form TCVN
    set_loi_param_smart(inst, "101-", ["101-Mã cấu kiện", "Mã cấu kiện", "Ma_Cau_Kien"], mark_code)
    set_loi_param_smart(inst, "102-", ["102-Phân loại cấu kiện", "Phân loại cấu kiện"], "An toàn giao thông")
    set_loi_param_smart(inst, "105-", ["105-Mô tả cấu kiện", "Mô tả cấu kiện"], fam_name)
    set_loi_param_smart(inst, "201-", ["201-Vị trí theo khu vực", "Vị trí theo khu vực", "Lý trình"], station_str)
    set_loi_param_smart(inst, "202-", ["202-Vị trí theo dự án", "Vị trí theo dự án", "Dự án"], package)
    set_loi_param_smart(inst, "203-", ["203-Tọa độ X thiết kế", "Tọa độ X thiết kế"], x_m, is_metric_length=True)
    set_loi_param_smart(inst, "204-", ["204-Tọa độ Y thiết kế", "Tọa độ Y thiết kế"], y_m, is_metric_length=True)
    set_loi_param_smart(inst, "205-", ["205-Cao độ thiết kế", "Cao độ thiết kế"], z_m, is_metric_length=True)
    set_loi_param_smart(inst, "301-", ["301-Chiều rộng thiết kế", "Chiều rộng thiết kế"], 0.20, is_metric_length=True)
    set_loi_param_smart(inst, "302-", ["302-Chiều dài thiết kế", "Chiều dài thiết kế"], length_m, is_metric_length=True)
    set_loi_param_smart(inst, "303-", ["303-Chiều cao thiết kế", "Chiều cao thiết kế"], height_m, is_metric_length=True)
    set_loi_param_smart(inst, "304-", ["304-Hình dạng thiết kế", "Hình dạng thiết kế"], "Khung lưới thép B40 / Định hình ATGT")
    set_loi_param_smart(inst, "401-", ["401-Vật liệu thiết kế", "Vật liệu thiết kế"], "Thép mạ kẽm nhúng nóng")
    set_loi_param_smart(inst, "402-", ["402-Cường độ thiết kế", "Cường độ thiết kế"], "SS400")
    set_loi_param_smart(inst, "403-", ["403-Mô đun đàn hồi", "Mô đun đàn hồi"], "2.1x10^5 MPa")
    set_loi_param_smart(inst, "406-", ["406-Màu sắc", "Màu sắc"], "Bạc mạ kẽm")

    return mark_code


def execute_multi_family_placement(
    document,
    input_elem,
    family_symbol_input=None,
    side_selection="Phai",
    lateral_offset_m=0.0,
    panel_length_m=2.5,
    custom_height_m=1.8,
    z_offset_m=0.0,
    manual_flip_180="Khong",
    cad_layer_filter="",
    loi_prefix="",
    loi_package="Goi thau XL01 | Km0+000 - Km60+000"
):
    if input_elem is None:
        return "CHUA CHON TIM TUYEN / DUONG DAN: Vui long bam 'Select' tai muc 1 va click chon doi tuong Polyline, 3D Polyline, hoac file CAD!", []

    TransactionManager.Instance.EnsureInTransaction(document)
    try:
        symbol = resolve_any_family_symbol(document, family_symbol_input)
        if not symbol:
            return "LOI: Khong the nhan dien Family duoc chon ({0}). Vui long kiem tra Family da duoc load vao Revit chua!".format(str(family_symbol_input)), []

        fam_name = symbol.Family.Name if symbol.Family else symbol.Name
        is_beam = False
        is_curve_based = False

        try:
            if symbol.Category and symbol.Category.Name == "Structural Framing":
                is_beam = True
                is_curve_based = True
            elif hasattr(symbol, "Family") and symbol.Family:
                fpt = symbol.Family.FamilyPlacementType
                if fpt == FamilyPlacementType.CurveBased:
                    is_curve_based = True
        except Exception:
            pass

        raw_paths = extract_paths_from_input(input_elem, document, cad_layer_filter)
        if not raw_paths and cad_layer_filter:
            raw_paths = extract_paths_from_input(input_elem, document, "")
        if not raw_paths:
            return "LOI: Khong tim thay duong dan 3D hop le tu doi tuong duoc chon!", []

        # Loc dung layer va chuoi duong tim dai nhat cua tuyen co cao do 3D thuc te
        paths = filter_relevant_paths(raw_paths, fam_name, cad_layer_filter)
        if not paths:
            paths = raw_paths

        # 1. TU DONG DON DEP CAC CAU KIEN CU CUNG FAMILY TREN TUYEN (KHONG TRUNG LAP)
        cleaned_count = cleanup_existing_instances_along_paths(document, paths, fam_name, max_dist_feet=100.0)

        side_clean = str(side_selection).strip().lower()
        is_right = ("phai" in side_clean) or ("right" in side_clean)
        is_left = ("trai" in side_clean) or ("left" in side_clean)
        is_both = ("ca hai" in side_clean) or ("both" in side_clean) or (is_right and is_left)

        if not is_left and not is_both:
            is_right = True

        flip_clean = str(manual_flip_180).lower()
        user_wants_flip = ("co" in flip_clean) or ("yes" in flip_clean) or ("180" in flip_clean) or ("true" in flip_clean)

        step_len_m = float(panel_length_m) if panel_length_m and float(panel_length_m) > 0.1 else 2.5
        step_feet = step_len_m * METERS_TO_FEET
        offset_dist_feet = abs(lateral_offset_m) * METERS_TO_FEET
        z_offset_feet = z_offset_m * METERS_TO_FEET

        runs = []

        if is_both and len(paths) == 1:
            runs.append((paths[0],  offset_dist_feet, "Ben Phai", False))
            runs.append((paths[0], -offset_dist_feet, "Ben Trai", True))
        elif is_both and len(paths) > 1:
            centroid_x = sum(p.points[0].X for p in paths) / float(len(paths))
            centroid_y = sum(p.points[0].Y for p in paths) / float(len(paths))
            center_xy = XYZ(centroid_x, centroid_y, 0)
            for p in paths:
                v_mid = p.points[0] - center_xy
                t_dir = (p.points[1] - p.points[0]) if len(p.points) > 1 else XYZ(1, 0, 0)
                cross_z = t_dir.X * v_mid.Y - t_dir.Y * v_mid.X
                if cross_z < 0:
                    runs.append((p, offset_dist_feet, "Ben Phai", False))
                else:
                    runs.append((p, -offset_dist_feet, "Ben Trai", True))
        elif is_left:
            for p in paths:
                runs.append((p, -offset_dist_feet, "Ben Trai", True))
        else:
            for p in paths:
                runs.append((p, offset_dist_feet, "Ben Phai", False))

        created_instances = []
        total_length_placed_m = 0.0
        global_seq = 1
        first_code = ""
        last_code = ""

        for path_obj, off_dist, side_label, side_needs_reverse in runs:
            curr_s = 0.0
            path_len = path_obj.total_length
            needs_face_flip = side_needs_reverse ^ user_wants_flip

            last_end_point_off = None

            while curr_s + (step_feet * 0.5) <= path_len:
                s_start = curr_s
                s_end = curr_s + step_feet

                p1 = path_obj.point_at_distance(s_start)
                p2 = path_obj.point_at_distance(s_end)

                chord_dx = p2.X - p1.X
                chord_dy = p2.Y - p1.Y
                len_2d = math.sqrt(chord_dx * chord_dx + chord_dy * chord_dy)

                if len_2d < 1e-4:
                    curr_s += step_feet
                    continue

                norm_right_x = chord_dy / len_2d
                norm_right_y = -chord_dx / len_2d

                if last_end_point_off is not None:
                    p1_off = last_end_point_off
                else:
                    p1_off = XYZ(p1.X + off_dist * norm_right_x, p1.Y + off_dist * norm_right_y, p1.Z + z_offset_feet)

                p2_off = XYZ(p2.X + off_dist * norm_right_x, p2.Y + off_dist * norm_right_y, p2.Z + z_offset_feet)
                last_end_point_off = p2_off

                # QUAN TRONG: line_start va line_end luon luon chay xuoi theo chieu tuyen
                # De dam bao diem dau dot (i+1) khop tuyet doi 100% voi diem cuoi dot (i) ca ve toa do mat bang lan cao do doc doc (Z)
                line_start = p1_off
                line_end = p2_off

                best_lvl = get_best_level(document, line_start.Z)
                inst = None

                # 1. Thu tao theo Line-Based (Structural Framing Beam hoac CurveBased)
                if is_curve_based or is_beam:
                    try:
                        line_3d = Line.CreateBound(line_start, line_end)
                        if best_lvl:
                            if is_beam:
                                inst = document.Create.NewFamilyInstance(line_3d, symbol, best_lvl, StructuralType.Beam)
                            else:
                                inst = document.Create.NewFamilyInstance(line_3d, symbol, best_lvl, StructuralType.NonStructural)
                        else:
                            if is_beam:
                                inst = document.Create.NewFamilyInstance(line_3d, symbol, StructuralType.Beam)
                            else:
                                inst = document.Create.NewFamilyInstance(line_3d, symbol, StructuralType.NonStructural)
                    except Exception as ex_b:
                        write_debug_log("Loi tao CurveBased/Beam: " + str(ex_b))

                # Xu ly chuyen biet cho Structural Framing (Dam / Thanh rao / Ton song / Beams)
                if is_beam and inst is not None:
                    # A. TAT CHE DO AUTO-JOIN & CUTBACK CUA REVIT:
                    try:
                        from Autodesk.Revit.DB.Structure import StructuralFramingUtils
                        StructuralFramingUtils.DisallowJoinAtEnd(inst, 0)
                        StructuralFramingUtils.DisallowJoinAtEnd(inst, 1)
                    except Exception:
                        pass

                    # B. RESET TOAN BO THAM SO CUTBACK VA EXTENSION VE 0.0 DE DAM CHAM NHAU KHIT KHAO
                    for cut_param in [
                        BuiltInParameter.START_JOIN_CUTBACK,
                        BuiltInParameter.END_JOIN_CUTBACK,
                        BuiltInParameter.STRUCTURAL_ATTACHMENT_START,
                        BuiltInParameter.STRUCTURAL_ATTACHMENT_END,
                        BuiltInParameter.BEAM_START_EXTENSION,
                        BuiltInParameter.BEAM_END_EXTENSION
                    ]:
                        try:
                            p_cut = inst.get_Parameter(cut_param)
                            if p_cut and not p_cut.IsReadOnly:
                                p_cut.Set(0.0)
                        except Exception:
                            pass

                    # C. DONG BO CHINH XAC CAO DO 2 DAU DOT DAM THEO DUNG DO DOC 3D
                    try:
                        p_s = inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION)
                        p_e = inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION)
                        lvl_elev = best_lvl.Elevation if best_lvl else 0.0
                        if p_s and not p_s.IsReadOnly:
                            p_s.Set(line_start.Z - lvl_elev)
                        if p_e and not p_e.IsReadOnly:
                            p_e.Set(line_end.Z - lvl_elev)
                    except Exception:
                        pass

                    # D. CAN CHINH TIM TRUC YZ DE MAT CAT KHOP NHAU KHONG BI LECH
                    try:
                        p_yz = inst.get_Parameter(BuiltInParameter.YZ_JUSTIFICATION)
                        if p_yz and not p_yz.IsReadOnly:
                            p_yz.Set(0)
                    except Exception:
                        pass

                    # E. DAO CHIEU MAT RAO 180 DO (CROSS-SECTION ROTATION) NEU CAN
                    if needs_face_flip:
                        try:
                            p_rot = inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEND_DIR_ANGLE)
                            if p_rot and not p_rot.IsReadOnly:
                                p_rot.Set(math.pi)
                        except Exception:
                            pass

                # 2. Fallback neu la Point-Based Family (Generic Model, LCC 2 Tru, Column, Coc tieu, DPC, etc.)
                if inst is None:
                    mid_pt = XYZ(
                        (line_start.X + line_end.X) * 0.5,
                        (line_start.Y + line_end.Y) * 0.5,
                        (line_start.Z + line_end.Z) * 0.5
                    )
                    try:
                        # Thu tao unhosted truoc de xoay 3D khong bi rang buoc boi mat phang ngang cua Level
                        inst = document.Create.NewFamilyInstance(mid_pt, symbol, StructuralType.NonStructural)
                    except Exception:
                        pass

                    if inst is None and best_lvl:
                        try:
                            inst = document.Create.NewFamilyInstance(mid_pt, symbol, best_lvl, StructuralType.NonStructural)
                        except Exception as ex_pt:
                            write_debug_log("Loi tao Point-based: " + str(ex_pt))

                    if inst is not None:
                        # 1. Dong bo cao do Z thuc te tai trung diem
                        set_instance_elevation(inst, mid_pt.Z, best_lvl)

                        loc_pt = inst.Location.Point if (hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None) else mid_pt

                        # A. Xoay mat bang (Yaw) theo huong day cung tuyen
                        yaw_rad = math.atan2(chord_dy, chord_dx)
                        if needs_face_flip:
                            yaw_rad += math.pi

                        if abs(yaw_rad) > 1e-4:
                            axis_rot = Line.CreateBound(loc_pt, XYZ(loc_pt.X, loc_pt.Y, loc_pt.Z + 10.0))
                            ElementTransformUtils.RotateElement(document, inst.Id, axis_rot, yaw_rad)

                        # B. XOAY THEO DO DOC DOC (PITCH SLOPE):
                        # Giup hai dau dot cau kien nang/ha khop tuyet doi theo do doc doc cua tuyen
                        chord_dz = line_end.Z - line_start.Z
                        pitch_angle = math.atan2(chord_dz, len_2d)

                        if abs(pitch_angle) > 1e-6:
                            try:
                                loc_pt = inst.Location.Point if (hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None) else mid_pt
                                u_x = math.cos(yaw_rad)
                                u_y = math.sin(yaw_rad)
                                pitch_axis_end = XYZ(
                                    loc_pt.X - u_y * 10.0,
                                    loc_pt.Y + u_x * 10.0,
                                    loc_pt.Z
                                )
                                axis_pitch = Line.CreateBound(loc_pt, pitch_axis_end)
                                rot_pitch = pitch_angle if not needs_face_flip else -pitch_angle
                                ElementTransformUtils.RotateElement(document, inst.Id, axis_pitch, rot_pitch)
                            except Exception as ex_pitch:
                                write_debug_log("Khong the xoay pitch: " + str(ex_pitch))

                        # C. Dong bo tham so do doc / goc nghieng neu family co tham so
                        for p_slope_name in ["Slope", "Pitch", "Goc", "Angle", "DoDoc", "GocDoc", "GocNghieng", "SlopeAngle"]:
                            try:
                                p_sl = inst.LookupParameter(p_slope_name)
                                if p_sl and not p_sl.IsReadOnly:
                                    if p_sl.StorageType == StorageType.Double:
                                        try:
                                            p_sl.Set(pitch_angle)
                                        except Exception:
                                            p_sl.Set(math.tan(pitch_angle))
                                        break
                            except Exception:
                                pass

                        for p_e_name in ["End Elevation Offset", "End Offset", "Z_End", "CaoDoCuoi", "End Level Offset", "Elevation at End"]:
                            try:
                                pe = inst.LookupParameter(p_e_name)
                                if pe and not pe.IsReadOnly and pe.StorageType == StorageType.Double:
                                    pe.Set(line_end.Z - lvl_elev)
                                    break
                            except Exception:
                                pass

                if inst is None:
                    curr_s += step_feet
                    continue

                actual_3d_len_m = math.sqrt(chord_dx * chord_dx + chord_dy * chord_dy + (line_end.Z - line_start.Z)**2) / METERS_TO_FEET
                apply_custom_dimensions(inst, actual_3d_len_m, custom_height_m)

                station_m = s_start / METERS_TO_FEET
                mk = assign_loi_data(inst, global_seq, station_m, side_label, fam_name, loi_prefix, loi_package)
                if not first_code: first_code = mk
                last_code = mk

                created_instances.append(inst)
                total_length_placed_m += step_len_m
                global_seq += 1

                curr_s += step_feet

        clean_msg = " | Da tu dong don dep {0} doi tuong cu cung Family tren tuyen".format(cleaned_count) if cleaned_count > 0 else ""

        z_sample_m = (paths[0].points[0].Z / METERS_TO_FEET) if (paths and len(paths[0].points) > 0) else 0.0
        elev_info = "- Cao do tuyen 3D: Z ~ {0:.2f} m (Z Offset = {1:+.2f} m)\n".format(z_sample_m, z_offset_m)

        result_summary = (
            "THANH CONG: Da rai {0} doi tuong Family [{1}] (KHOANG CACH BUOC RAI = {2:.2f}M, KHOP NOI 100% THEO DO DOC)!\n"
            "- Tong chieu dai tuyen: {4:.2f} m | So dot/cau kien: {0}\n"
            "{12}"
            "- Vi tri ben tuyen: {5}\n"
            "- Buoc dot L = {2:.2f} m | Chieu cao H = {6:.2f} m | Offset = {7:.2f} m\n"
            "- Tinh nang do doc: Diem dau va diem cuoi cac family da duoc dong bo khop noi khit khao theo dung cao do 3D & do doc doc (Pitch Slope)\n"
            "- Khoang ma LOI BIM: [{8} -> {9}]\n"
            "- Goi thau: {10}\n"
            "- Loai Family nhan dien: {11}{3}"
        ).format(
            len(created_instances),
            fam_name,
            step_len_m,
            clean_msg,
            total_length_placed_m,
            side_selection,
            custom_height_m,
            lateral_offset_m,
            first_code,
            last_code,
            loi_package,
            "Structural Framing Beam (Line-based)" if is_beam else ("Curve-Based" if is_curve_based else "Point-Based Family"),
            elev_info
        )

        return result_summary, [i.Id.IntegerValue for i in created_instances]

    finally:
        TransactionManager.Instance.TransactionTaskDone()


if IS_DYNAMO:
    try:
        in_elem        = IN[0] if len(IN) > 0 else None
        in_sym         = IN[1] if len(IN) > 1 and IN[1] else None
        in_side        = IN[2] if len(IN) > 2 and IN[2] else "Phai"
        in_offset      = float(IN[3]) if len(IN) > 3 and IN[3] is not None and str(IN[3]).strip() != "" else 0.0
        in_len         = float(IN[4]) if len(IN) > 4 and IN[4] is not None and str(IN[4]).strip() != "" else 2.5
        in_h           = float(IN[5]) if len(IN) > 5 and IN[5] is not None and str(IN[5]).strip() != "" else 1.8
        in_z_off       = float(IN[6]) if len(IN) > 6 and IN[6] is not None and str(IN[6]).strip() != "" else 0.0
        in_flip        = str(IN[7]).strip() if len(IN) > 7 and IN[7] is not None and str(IN[7]).strip() != "" else "Khong"
        in_layer       = str(IN[8]).strip() if len(IN) > 8 and IN[8] is not None and str(IN[8]).strip() != "" else ""
        in_prefix      = str(IN[9]).strip() if len(IN) > 9 and IN[9] is not None and str(IN[9]).strip() != "" else ""
        in_pkg         = str(IN[10]).strip() if len(IN) > 10 and IN[10] is not None and str(IN[10]).strip() != "" else "Goi thau XL01 | Km0+000 - Km60+000"

        res_text, elem_ids = execute_multi_family_placement(
            doc,
            in_elem,
            in_sym,
            in_side,
            in_offset,
            in_len,
            in_h,
            in_z_off,
            in_flip,
            in_layer,
            in_prefix,
            in_pkg
        )

        OUT = res_text
    except Exception as ex:
        import traceback
        OUT = "LOI THUC THI: {0}\n{1}".format(str(ex), traceback.format_exc())

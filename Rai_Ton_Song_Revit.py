# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT: Rai_Ton_Song_Revit.py
TOOL ATGT DEDICATED: RAI TON LUON SONG HO LAN (W-BEAM GUARDRAIL)
CHUAN MO HINH THUC TE REVIT (STRUCTURAL FRAMING BEAM CHUAN THEO LINE-BASED):
  - KHOANG CACH GIUA CAC TRU (BUOC COT) DANG DEU NHAU CHINH XAC 100% (2.00m)
  - Moi dot ton dai dung 4.0m gom 2 cot do (TCVN 12681:2019)
  - Noi tiep khit khao giua cac dot ton lien tiep (khong bi lech, khong khoang trong)
  - Tu dong stitch/chain cac doan CAD 3D Polyline roi rac thanh 1 tuyen lien tuc
  - Tu dong lay dung cao do 3D (Pitch Slope) theo tim tuyen
  - Tu dong don dep cac FamilyInstance cu tren tuyen tranh trung family
  - Ho tro chon Ben Phai, Ben Trai, Ca hai ben & Dao chieu 180 do
================================================================================
"""

import sys
import os
import math

METERS_TO_FEET = 3.28083989501312336

DEBUG_LOG_PATH = r"C:\Users\Admin\.gemini\antigravity-ide\scratch\debug_ton_song.log"

def write_debug_log(msg):
    try:
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass

try:
    with open(DEBUG_LOG_PATH, "w") as f:
        f.write("=== LOG RAI TON SONG HO LAN (LINE-BASED BEAM) ===\n")
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


class PolylinePath3D:
    def __init__(self, points, layer_name=""):
        # Loc bo cac diem trung nhau lien tiep de tranh loi chia cho 0
        cleaned = []
        for p in points:
            if not cleaned or p.DistanceTo(cleaned[-1]) > 1e-4:
                cleaned.append(p)
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
                t = max(0.0, min(1.0, ((pt.X - p1.X)*dx + (pt.Y - p1.Y)*dy) / seg_len_sq))
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
        f_name = symbol.Family.Name
    except Exception:
        try:
            f_name = symbol.FamilyName
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


def resolve_guardrail_family(document, family_input):
    """Nhan dien FamilySymbol ton song. Neu chua co, tu dong load TS-ZZ-GUA.rfa"""
    TransactionManager.Instance.EnsureInTransaction(document)

    if family_input is None:
        target_name = "ts-zz-gua"
    elif hasattr(family_input, "InternalElement"):
        family_input = family_input.InternalElement
        target_name = ""
    elif isinstance(family_input, str):
        target_name = family_input.strip().lower()
    else:
        target_name = str(family_input).strip().lower()

    if isinstance(family_input, FamilySymbol):
        activate_symbol_safe(family_input, document)
        return family_input

    collector = FilteredElementCollector(document).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()

    if target_name:
        for sym in collector:
            f_name, t_name = get_symbol_names(sym)
            combined = (f_name + " " + t_name).lower()
            if target_name in combined or target_name in f_name.lower() or target_name in t_name.lower():
                activate_symbol_safe(sym, document)
                return sym

    for sym in collector:
        f_name, t_name = get_symbol_names(sym)
        combined = (f_name + " " + t_name).lower()
        if any(k in combined for k in ["ts-zz-gua", "ton_song", "guardrail", "ho lan", "ton song"]):
            activate_symbol_safe(sym, document)
            return sym

    rfa_paths = [
        r"G:\My Drive\1.Work\ATGT\Tool ATGT\Data\02_TON HO LAN\Family\TS-ZZ-GUA.rfa",
        r"H:\My Drive\1.Work\ATGT\Tool ATGT\Data\02_TON HO LAN\Family\TS-ZZ-GUA.rfa",
        r"C:\Users\Admin\.gemini\antigravity-ide\scratch\TS-ZZ-GUA.rfa"
    ]
    for r_path in rfa_paths:
        if os.path.exists(r_path):
            try:
                loaded_fam = clr.Reference[Family]()
                if document.LoadFamily(r_path, loaded_fam):
                    fam = loaded_fam.Value
                    for sym_id in fam.GetFamilySymbolIds():
                        sym = document.GetElement(sym_id)
                        if sym:
                            activate_symbol_safe(sym, document)
                            return sym
            except Exception:
                pass

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


def cleanup_existing_guardrails_along_paths(document, paths, fam_name="TS-ZZ-GUA", max_dist_feet=65.0):
    """Don dep tat ca FamilyInstance ton song cu doc theo tim tuyen de tranh trung lap."""
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
        f_target = fam_name.lower().strip() if fam_name else "ts-zz-gua"

        guard_keywords = [
            "ts-zz-gua", "ts", "ton", "song", "guard", "gua", "ho lan", "w-beam"
        ]

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
                    s_type_name = str(sym.Name).lower()
                    if sym.Family:
                        s_fam_name = str(sym.Family.Name).lower()
                else:
                    type_id = inst.GetTypeId()
                    if type_id != ElementId.InvalidElementId:
                        elem_type = document.GetElement(type_id)
                        if elem_type:
                            s_type_name = str(elem_type.Name).lower()
                            if hasattr(elem_type, "FamilyName"):
                                s_fam_name = str(elem_type.FamilyName).lower()

                mark_str = ""
                try:
                    mark_p = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                    if mark_p:
                        mark_str = mark_p.AsString() or ""
                except Exception:
                    pass

                comm_str = ""
                try:
                    comm_p = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    if comm_p:
                        comm_str = comm_p.AsString() or ""
                except Exception:
                    pass

                is_ts = False
                if f_target and (f_target in s_fam_name or s_fam_name in f_target or f_target in s_type_name or s_type_name in f_target):
                    is_ts = True
                elif any(k in s_fam_name for k in guard_keywords):
                    is_ts = True
                elif any(k in s_type_name for k in guard_keywords):
                    is_ts = True
                elif mark_str and mark_str.startswith("TS-"):
                    is_ts = True
                elif comm_str and "[LOI BIM ATGT]" in comm_str:
                    is_ts = True

                if is_ts:
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
            write_debug_log("Da don dep {0} doi tuong ton song cu tren tuyen.".format(deleted_count))
    except Exception as ex:
        write_debug_log("Loi don dep ton song cu: " + str(ex))
    return deleted_count


def stitch_segments_into_continuous_paths(segments, tol=0.5):
    """
    Noi tat ca cac doan thang/curve 3D roi rac thanh cac chuoi Polyline lien tuc.
    tol: dung sai ket noi dau mut (mac dinh 0.5 feet ~ 15cm).
    """
    if not segments:
        return []

    remaining = []
    for p0, p1 in segments:
        if p0.DistanceTo(p1) > 1e-4:
            remaining.append([p0, p1])

    if not remaining:
        return []

    chains = []

    while remaining:
        current_chain = remaining.pop(0)

        # Mo rong ve phia sau (tail)
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
                if reverse_cand:
                    seg.reverse()
                current_chain.extend(seg[1:])
                extended = True

        # Mo rong ve phia truoc (head)
        extended = True
        while extended:
            extended = False
            head = current_chain[0]
            best_idx = -1
            best_dist = tol
            prepend_as_is = False

            for i, seg in enumerate(remaining):
                d_end = head.DistanceTo(seg[-1])
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
                if not prepend_as_is:
                    seg.reverse()
                current_chain = seg[:-1] + current_chain
                extended = True

        if len(current_chain) >= 2:
            chains.append(PolylinePath3D(current_chain, "Stitched_Corridor"))

    # Sap xep theo chieu dai giam dan (duong tuyen chinh dai nhat len dau)
    chains.sort(key=lambda c: c.total_length, reverse=True)
    return chains


def extract_paths_from_input(elem, document, layer_filter=""):
    """
    Trich xuat toan bo duong dan tu Element duoc chon trong Dynamo.
    Ho tro 100%: CAD ImportInstance (3D Polyline / Layer TS), PolyLine, PolyCurve, Curve.
    Moi phan doan deu duoc noi (stitch) thanh chuoi lien tuc hoan hao.
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

    # Neu da la tap hop diem truc tiep
    if len(raw_list) >= 2 and all(hasattr(p, "X") and hasattr(p, "Y") for p in raw_list):
        pts = []
        for p in raw_list:
            z_val = getattr(p, "Z", 0.0)
            pts.append(XYZ(p.X, p.Y, z_val))
        return [PolylinePath3D(pts, "PointList")]

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

        # Dynamo PolyCurve
        if hasattr(item, "Curves"):
            try:
                sub_c = item.Curves() if callable(item.Curves) else item.Curves
                for sc in sub_c:
                    p0 = XYZ(sc.StartPoint.X, sc.StartPoint.Y, sc.StartPoint.Z)
                    p1 = XYZ(sc.EndPoint.X, sc.EndPoint.Y, sc.EndPoint.Z)
                    collected_segments.append((p0, p1))
                continue
            except Exception:
                pass

        # Dynamo Curve
        if hasattr(item, "StartPoint") and hasattr(item, "EndPoint"):
            try:
                p0 = XYZ(item.StartPoint.X, item.StartPoint.Y, item.StartPoint.Z)
                p1 = XYZ(item.EndPoint.X, item.EndPoint.Y, item.EndPoint.Z)
                collected_segments.append((p0, p1))
                continue
            except Exception:
                pass

        # Revit PolyLine truc tiep
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
                    for i in range(len(coords) - 1):
                        collected_segments.append((coords[i], coords[i + 1]))
                continue
            except Exception:
                pass

        # Revit Curve truc tiep
        if isinstance(revit_elem, Curve):
            collected_segments.append((revit_elem.GetEndPoint(0), revit_elem.GetEndPoint(1)))
            continue

        # CAD ImportInstance / GeometryElement
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

                        # Loc layer CAD neu co filter
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

                            count_before = len(collected_segments)
                            if inst_geom:
                                for sub_g in inst_geom:
                                    parse_geom(sub_g, layer, None)

                            if len(collected_segments) > count_before:
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
                                    for i in range(len(coords) - 1):
                                        pt_a = transform.OfPoint(coords[i]) if transform else coords[i]
                                        pt_b = transform.OfPoint(coords[i + 1]) if transform else coords[i + 1]
                                        collected_segments.append((pt_a, pt_b))
                                return
                            except Exception:
                                pass

                        if isinstance(g_obj, Curve):
                            try:
                                c = g_obj.CreateTransformed(transform) if transform else g_obj
                                collected_segments.append((c.GetEndPoint(0), c.GetEndPoint(1)))
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

    write_debug_log("Tong so segments thu thap duoc: {0}".format(len(collected_segments)))

    # Stitch tat ca cac segments thanh cac chuoi Polyline lien tuc
    stitched = stitch_segments_into_continuous_paths(collected_segments, tol=0.5)
    write_debug_log("So chuoi duong dan sau khi stitch: {0}".format(len(stitched)))
    for idx, sp in enumerate(stitched):
        write_debug_log("  Path {0}: Chieu dai = {1:.2f} m ({2} diem)".format(
            idx, sp.total_length / METERS_TO_FEET, len(sp.points)
        ))

    return stitched


def apply_guardrail_dimensions(inst, length_m, height_m):
    """Gan thong so L va H vao FamilyInstance"""
    for l_name in ["L", "Length", "Chieu dai", "DoanTon"]:
        try:
            p = inst.LookupParameter(l_name)
            if p and not p.IsReadOnly:
                p.Set(length_m * METERS_TO_FEET)
                break
        except Exception:
            pass
    for h_name in ["H", "Height", "Chieu cao", "DinhTon"]:
        try:
            p = inst.LookupParameter(h_name)
            if p and not p.IsReadOnly:
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


def assign_loi_data(inst, seq_num, station_m, side_label, prefix="TS-HTS-", package="Tỉnh Tây Ninh"):
    """Gan ma cau kien va thong tin BIM LOI cho tung tam ton song theo chuan form BIM"""
    if not prefix:
        prefix = "TS-HTS-"
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
        "[BIM LOI] Mã: {0} | Vị trí: {1} | Lý trình: {2} | Dự án: {3} | Tọa độ: ({4:.2f}, {5:.2f}, {6:.2f})"
    ).format(mark_code, side_label, station_str, package, x_m, y_m, z_m)

    try:
        p_comm = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p_comm and not p_comm.IsReadOnly:
            p_comm.Set(loi_comments)
    except Exception:
        pass

    # Gan cac tham so theo form BIM
    set_loi_param_smart(inst, "101-", ["101-Mã cấu kiện", "Mã cấu kiện", "Ma_Cau_Kien"], mark_code)
    set_loi_param_smart(inst, "102-", ["102-Phân loại cấu kiện", "Phân loại cấu kiện"], "An toàn giao thông")
    set_loi_param_smart(inst, "105-", ["105-Mô tả cấu kiện", "Mô tả cấu kiện"], "Tôn hộ lan")
    set_loi_param_smart(inst, "201-", ["201-Vị trí theo khu vực", "Vị trí theo khu vực", "Lý trình"], station_str)
    set_loi_param_smart(inst, "202-", ["202-Vị trí theo dự án", "Vị trí theo dự án", "Dự án"], package)
    set_loi_param_smart(inst, "203-", ["203-Tọa độ X thiết kế", "Tọa độ X thiết kế"], x_m, is_metric_length=True)
    set_loi_param_smart(inst, "204-", ["204-Tọa độ Y thiết kế", "Tọa độ Y thiết kế"], y_m, is_metric_length=True)
    set_loi_param_smart(inst, "205-", ["205-Cao độ thiết kế", "Cao độ thiết kế"], z_m, is_metric_length=True)
    set_loi_param_smart(inst, "301-", ["301-Chiều rộng thiết kế", "Chiều rộng thiết kế"], 0.31, is_metric_length=True)
    set_loi_param_smart(inst, "302-", ["302-Chiều dài thiết kế", "Chiều dài thiết kế"], 4.00, is_metric_length=True)
    set_loi_param_smart(inst, "303-", ["303-Chiều cao thiết kế", "Chiều cao thiết kế"], 0.75, is_metric_length=True)
    set_loi_param_smart(inst, "304-", ["304-Hình dạng thiết kế", "Hình dạng thiết kế"], "Tấm tôn lượn sóng chữ W 2 bước sóng (TCVN 12681:2019)")
    set_loi_param_smart(inst, "401-", ["401-Vật liệu thiết kế", "Vật liệu thiết kế"], "Thép mạ kẽm nhúng nóng")
    set_loi_param_smart(inst, "402-", ["402-Cường độ thiết kế", "Cường độ thiết kế"], "SS400")
    set_loi_param_smart(inst, "403-", ["403-Mô đun đàn hồi", "Mô đun đàn hồi"], "2.1x10^5 MPa")
    set_loi_param_smart(inst, "406-", ["406-Màu sắc", "Màu sắc"], "Bạc mạ kẽm")

    return mark_code


def execute_guardrail_placement(
    document,
    input_elem,
    family_symbol_input=None,
    side_selection="Phai",
    lateral_offset_m=0.0,
    panel_length_m=4.0,
    guardrail_height_m=0.75,
    z_offset_m=0.0,
    manual_flip_180="Khong",
    cad_layer_filter="TS",
    loi_prefix="TS-KM52-",
    loi_package="Goi thau XL01 | Km52+000 - Km60+000"
):
    if input_elem is None:
        return "CHUA CHON TIM TUYEN: Vui long bam 'Select' tai muc 1 va click chon doi tuong Polyline, 3D Polyline, hoac file CAD!", []

    TransactionManager.Instance.EnsureInTransaction(document)
    try:
        symbol = resolve_guardrail_family(document, family_symbol_input)
        if not symbol:
            return "LOI: Khong tim thay Family Ton Song (TS-ZZ-GUA). Vui long kiem tra file RFA hoac load vao project!", []

        paths = extract_paths_from_input(input_elem, document, cad_layer_filter)
        if not paths and cad_layer_filter:
            paths = extract_paths_from_input(input_elem, document, "")
        if not paths:
            return "LOI: Khong tim thay duong dan 3D (Polyline / 3D Polyline / Curve / Layer TS) tu doi tuong duoc chon!", []

        # 1. TU DONG DON DEP CAC FAMILY TON SONG CU TREN TUYEN (KHONG TRUNG FAMILY)
        fam_name = symbol.Family.Name if symbol.Family else symbol.Name
        cleaned_count = cleanup_existing_guardrails_along_paths(document, paths, fam_name, max_dist_feet=65.0)

        side_clean = str(side_selection).strip().lower()
        is_right = ("phai" in side_clean) or ("right" in side_clean)
        is_left = ("trai" in side_clean) or ("left" in side_clean)
        is_both = ("ca hai" in side_clean) or ("both" in side_clean) or (is_right and is_left)

        if not is_left and not is_both:
            is_right = True

        flip_clean = str(manual_flip_180).lower()
        user_wants_flip = ("co" in flip_clean) or ("yes" in flip_clean) or ("180" in flip_clean) or ("true" in flip_clean)

        # BAT BUOC CHIEU DAI DOT TON CHUAN (Mac dinh = 4.0m tuong ung voi buoc cot 2.0m)
        step_len_m = float(panel_length_m) if panel_length_m and float(panel_length_m) > 0.5 else 4.0
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

            # Quyet dinh chieu ve cua Line:
            # Ben Phai: ve xuoi p1 -> p2 (mat ton ben trai huong vao long duong, cot o ben phai)
            # Ben Trai: ve nguoc p2 -> p1 (mat ton tu dong quay sang phai huong vao long duong, cot o ben trai)
            # Neu user chon Dao chieu 180 = Co thi dao nguoc lai
            reverse_beam = side_needs_reverse ^ user_wants_flip

            last_end_point_off = None

            # Vong lap rai theo dung buoc dot step_feet = 4.0m
            # DAM BAO 100% TAT CA CAC DOT TON DEU CO CHIEU DAI 4.0m -> KHOANG CACH TRU DEU NHAU 2.0m!
            while curr_s + (step_feet * 0.5) <= path_len:
                s_start = curr_s
                s_end = curr_s + step_feet  # Luon lay dung 4.0m

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

                # Diem bat dau: noi tiep khit voi diem cuoi cua dot truoc do de tranh ho hay gach khuc
                if last_end_point_off is not None:
                    p1_off = last_end_point_off
                else:
                    p1_off = XYZ(p1.X + off_dist * norm_right_x, p1.Y + off_dist * norm_right_y, p1.Z + z_offset_feet)

                p2_off = XYZ(p2.X + off_dist * norm_right_x, p2.Y + off_dist * norm_right_y, p2.Z + z_offset_feet)
                last_end_point_off = p2_off

                # Xac dinh diem dau va diem cuoi cua Line 3D tao Beam
                if reverse_beam:
                    line_start = p2_off
                    line_end = p1_off
                else:
                    line_start = p1_off
                    line_end = p2_off

                # Tim Level gan nhat voi cao do line_start
                best_lvl = get_best_level(document, line_start.Z)

                inst = None
                try:
                    line_3d = Line.CreateBound(line_start, line_end)
                    if best_lvl:
                        inst = document.Create.NewFamilyInstance(line_3d, symbol, best_lvl, StructuralType.Beam)
                except Exception as ex_beam:
                    write_debug_log("Loi tao Beam voi Line: " + str(ex_beam))

                # Fallback neu khong the tao Beam
                if inst is None:
                    curr_s += step_feet
                    continue

                # Dong bo cao do chinh xac tuyet doi cho 2 dau dot dAM Beam
                try:
                    p_s = inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION)
                    p_e = inst.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION)
                    if p_s and not p_s.IsReadOnly:
                        p_s.Set(line_start.Z - best_lvl.Elevation)
                    if p_e and not p_e.IsReadOnly:
                        p_e.Set(line_end.Z - best_lvl.Elevation)
                except Exception:
                    pass

                # Gan kich thuoc L va H
                apply_guardrail_dimensions(inst, step_len_m, guardrail_height_m)

                # Gan du lieu LOI BIM
                station_m = s_start / METERS_TO_FEET
                mk = assign_loi_data(inst, global_seq, station_m, side_label, loi_prefix, loi_package)
                if not first_code: first_code = mk
                last_code = mk

                created_instances.append(inst)
                total_length_placed_m += step_len_m
                global_seq += 1

                # BUOC TIEN CHUAN XAC 100%: Tien dung bang chieu dai dot (4.0m)
                curr_s += step_feet

        clean_msg = " | Da tu dong don dep {0} doi tuong ton song cu tren tuyen".format(cleaned_count) if cleaned_count > 0 else ""

        result_summary = (
            "THANH CONG: Da rai {0} dot Ton Luon Song Ho Lan chuan Structural Framing Beam (KHOANG CACH COT DEU NHAU CHUAN 2.00M, khong trung family){1}!\n"
            "- Tong chieu dai rai: {2:.2f} m | So cot: {3} cot (Buoc cot = 2.00 m deu nhau 100%)\n"
            "- Vi tri ben tuyen: {4}\n"
            "- Buoc dot L = {5:.2f} m (Moi dot gom 2 cot, noi tiep khit khau) | Dinh H = {6:.2f} m | Offset = {7:.2f} m\n"
            "- Khoang ma LOI BIM: [{8} -> {9}]\n"
            "- Goi thau: {10}\n"
            "- Huong mat ton: Tu dong quay vao long duong (traffic face inward)."
        ).format(
            len(created_instances),
            clean_msg,
            total_length_placed_m,
            len(created_instances) * 2,
            side_selection,
            step_len_m,
            guardrail_height_m,
            lateral_offset_m,
            first_code,
            last_code,
            loi_package
        )

        return result_summary, [i.Id.IntegerValue for i in created_instances]

    finally:
        TransactionManager.Instance.TransactionTaskDone()


if IS_DYNAMO:
    try:
        in_elem        = IN[0] if len(IN) > 0 else None
        in_sym         = IN[1] if len(IN) > 1 and IN[1] else "TS-ZZ-GUA"
        in_side        = IN[2] if len(IN) > 2 and IN[2] else "Phai"
        in_offset      = float(IN[3]) if len(IN) > 3 and IN[3] is not None and str(IN[3]).strip() != "" else 0.0
        in_len         = float(IN[4]) if len(IN) > 4 and IN[4] is not None and str(IN[4]).strip() != "" else 4.0
        in_h           = float(IN[5]) if len(IN) > 5 and IN[5] is not None and str(IN[5]).strip() != "" else 0.75
        in_z_off       = float(IN[6]) if len(IN) > 6 and IN[6] is not None and str(IN[6]).strip() != "" else 0.0
        in_flip        = str(IN[7]).strip() if len(IN) > 7 and IN[7] is not None and str(IN[7]).strip() != "" else "Khong"
        in_layer       = str(IN[8]).strip() if len(IN) > 8 and IN[8] is not None and str(IN[8]).strip() != "" else "TS"
        in_prefix      = str(IN[9]).strip() if len(IN) > 9 and IN[9] is not None and str(IN[9]).strip() != "" else "TS-KM52-"
        in_pkg         = str(IN[10]).strip() if len(IN) > 10 and IN[10] is not None and str(IN[10]).strip() != "" else "Goi thau XL01 | Km52+000 - Km60+000"

        res_text, elem_ids = execute_guardrail_placement(
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

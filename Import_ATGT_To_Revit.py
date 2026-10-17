# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT: Import_ATGT_To_Revit.py
MUC DICH: Tu dong rai cac doi tuong ATGT trong Autodesk Revit 2025:
          1. Ho tro 100% tren doi tuong 3D POLYLINE (CAD ImportInstance,
             DirectShape, ModelCurve, CurveElement, Dynamo PolyCurve).
          2. TOA DO VA CAO DO 3D CHUAN XAC: Su dung GetInstanceGeometry() de lay
             dung 100% toa do Revit World va cao do tráº¯c Ä‘á»‹a Z thuc te doc tuyen.
          3. DONG BO CAO DO CHO FAMILY: Tu dong gan cao do Z thuc te cho tung dot
             Family qua INSTANCE_ELEVATION_PARAM, Offset, hoac CurveBased Line 3D.
          4. TU DONG DIEN DAY CAO DO: Neu 3D Polyline co cac dinh dau/cuoi bi
             Z=0 do CAD 2D/3D ket hop, tu dong noi suy/dien day theo cao do thuc dia.
          5. TU DONG CAN CHINH GOC XOAY CHIEU DAI: Khac phuc triet de loi
             Family bi xoay ngang 90 do dam vuong goc voi tim tuyen.
          6. THUAT TOAN NOI CHUOI O(N) SPATIAL HASH: Noi hang nghin doan line CAD
             thanh 1 chuoi 3D Polyline lien tuc trong vai mili-giay.
          7. Ho tro ca Point-Based Family va Curve-Based (Line-Based) Family.
          8. DA XOA HOAN TOAN BUOC 10 (CSV) - Chi tap trung 100% vao doi tuong pick chon.
================================================================================
"""

import sys
import os
import math

# Hang so chuyen doi don vi Revit API (Internal units: Feet)
METERS_TO_FEET = 3.28083989501312336

# Kiem tra moi truong Dynamo vs Standalone Revit Python
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

def write_debug_log(msg):
    """Ghi log chan doan de kiem tra tien trinh thuc thi cua tool"""
    try:
        log_dir = r"H:\My Drive\1.Work\ATGT\Tool ATGT\ErrorReports"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, "debug_atgt_run.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
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

def unloop_closed_path(points, max_island_width_feet=15.0):
    """
    Neu mot duong 3D polyline la vong khep kin di va ve (round-trip loop)
    chay quanh dao dai phan cach (nua di va nua ve song song nguoc chieu nhau cach nhau < 4.5m):
    Chi giu lai nua dau (nua di) de tranh rai 2 hang de len nhau hoac bi quay dau xe!
    """
    if not points or len(points) < 4:
        return points

    p_start = points[0]
    p_end = points[-1]
    if p_start.DistanceTo(p_end) < max_island_width_feet:
        total_d = sum(points[k].DistanceTo(points[k+1]) for k in range(len(points)-1))
        if total_d < 1.0:
            return points
        half_d = total_d / 2.0
        cum = 0.0
        mid_idx = len(points) // 2
        for k in range(len(points)-1):
            cum += points[k].DistanceTo(points[k+1])
            if cum >= half_d:
                mid_idx = k
                break

        pt_quarter = points[mid_idx // 2]
        pt_three_quarter = points[min(len(points) - 1, mid_idx + (len(points) - mid_idx) // 2)]
        if pt_quarter.DistanceTo(pt_three_quarter) < max_island_width_feet:
            return points[:mid_idx + 1]

    return points

class PolylinePath3D:
    """Lop bieu dien duong dan 3D Polyline lien tuc co the lay toa do va tiep tuyen theo khoang cach s"""
    def __init__(self, points, layer_name=""):
        self.points = []
        self.layer_name = layer_name

        # Chuan hoa cao do 3D thuc dia doc theo tuyen
        pts_cleaned = clean_path_elevations(points)
        pts_unlooped = unloop_closed_path(pts_cleaned)

        for p in pts_unlooped:
            if len(self.points) == 0 or self.points[-1].DistanceTo(p) > 1e-4:
                self.points.append(p)

        self.cum_lens = [0.0]
        for i in range(len(self.points) - 1):
            d = self.points[i].DistanceTo(self.points[i+1])
            self.cum_lens.append(self.cum_lens[-1] + d)

        self.total_length = self.cum_lens[-1] if len(self.cum_lens) > 0 else 0.0

    def evaluate(self, dist):
        """Tra ve diem (XYZ) va vector tiep tuyen (XYZ) tai khoang cach dist doc theo 3D Polyline"""
        if len(self.points) == 0:
            return XYZ.Zero, XYZ.BasisX
        if len(self.points) == 1:
            return self.points[0], XYZ.BasisX
        if dist <= 0.0:
            p0 = self.points[0]
            p1 = self.points[1]
            return p0, XYZ(p1.X - p0.X, p1.Y - p0.Y, p1.Z - p0.Z)
        if dist >= self.total_length:
            p_end = self.points[-1]
            p_prev = self.points[-2]
            return p_end, XYZ(p_end.X - p_prev.X, p_end.Y - p_prev.Y, p_end.Z - p_prev.Z)

        for i in range(len(self.cum_lens) - 1):
            if self.cum_lens[i] <= dist <= self.cum_lens[i+1]:
                seg_len = self.cum_lens[i+1] - self.cum_lens[i]
                t = (dist - self.cum_lens[i]) / seg_len if seg_len > 1e-5 else 0.0
                p1 = self.points[i]
                p2 = self.points[i+1]
                pt = XYZ(
                    p1.X + t * (p2.X - p1.X),
                    p1.Y + t * (p2.Y - p1.Y),
                    p1.Z + t * (p2.Z - p1.Z)
                )
                tangent = XYZ(p2.X - p1.X, p2.Y - p1.Y, p2.Z - p1.Z)
                return pt, tangent

        return self.points[-1], XYZ.BasisX

    def min_distance_to(self, pt):
        """Khoang cach ngan nhat tu diem pt den duong 3D polyline (tinh tren mat bang XY)"""
        if not self.points:
            return 1e9
        if len(self.points) == 1:
            p0 = self.points[0]
            return math.sqrt((pt.X - p0.X)**2 + (pt.Y - p0.Y)**2)

        min_d = 1e9
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i+1]
            dx = p2.X - p1.X
            dy = p2.Y - p1.Y
            l2 = dx * dx + dy * dy
            if l2 < 1e-6:
                d = math.sqrt((pt.X - p1.X)**2 + (pt.Y - p1.Y)**2)
            else:
                t = max(0.0, min(1.0, ((pt.X - p1.X) * dx + (pt.Y - p1.Y) * dy) / l2))
                proj_x = p1.X + t * dx
                proj_y = p1.Y + t * dy
                d = math.sqrt((pt.X - proj_x)**2 + (pt.Y - proj_y)**2)
            if d < min_d:
                min_d = d
        return min_d

def get_symbol_family_and_type(sym):
    f_name = ""
    t_name = ""
    try:
        if hasattr(sym, "Family") and sym.Family:
            f_name = sym.Family.Name
    except Exception:
        pass
    try:
        t_name = sym.Name
    except Exception:
        pass
    return f_name, t_name

def stitch_connected_paths(paths, tol_feet=2.0):
    """
    Noi nhanh O(N) cac doan duong Polyline/Curve roi rac co chung diem dau/cuoi thanh
    cac duong 3D Polyline lien tuc dai nhat co the.
    Su dung bang bam khong gian (spatial grid hash) de xu ly hang nghin doan line trong chop mat.
    """
    if len(paths) <= 1:
        return paths

    def grid_key(pt):
        gx = int(math.floor(pt.X / tol_feet))
        gy = int(math.floor(pt.Y / tol_feet))
        gz = int(math.floor(pt.Z / tol_feet))
        return (gx, gy, gz)

    # Nhom theo layer neu co
    by_layer = {}
    for p in paths:
        lay = p.layer_name or ""
        if lay not in by_layer:
            by_layer[lay] = []
        by_layer[lay].append(p)

    all_stitched = []

    for lay, group in by_layer.items():
        segments = []
        for p in group:
            if len(p.points) >= 2:
                segments.append(list(p.points))

        if len(segments) <= 1:
            for s in segments:
                all_stitched.append(PolylinePath3D(s, lay))
            continue

        # Xay dung spatial hash index cho tat ca cac diem dau va cuoi
        grid = {}
        for s_idx, pts in enumerate(segments):
            for is_head, pt in [(True, pts[0]), (False, pts[-1])]:
                k = grid_key(pt)
                if k not in grid:
                    grid[k] = []
                grid[k].append((s_idx, is_head))

        visited = [False] * len(segments)

        for start_idx in range(len(segments)):
            if visited[start_idx]:
                continue

            visited[start_idx] = True
            chain = list(segments[start_idx])

            # Mo rong ve phia tail cua chain
            growing = True
            while growing:
                growing = False
                tail_pt = chain[-1]
                gx, gy, gz = grid_key(tail_pt)
                best_seg = None
                best_dist = tol_feet
                best_is_head = True

                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            neighbor_k = (gx + dx, gy + dy, gz + dz)
                            for cand_idx, cand_is_head in grid.get(neighbor_k, []):
                                if not visited[cand_idx]:
                                    cand_pt = segments[cand_idx][0] if cand_is_head else segments[cand_idx][-1]
                                    d = tail_pt.DistanceTo(cand_pt)
                                    if d < best_dist:
                                        best_dist = d
                                        best_seg = cand_idx
                                        best_is_head = cand_is_head

                if best_seg is not None:
                    visited[best_seg] = True
                    add_pts = segments[best_seg]
                    if best_is_head:
                        chain.extend(add_pts[1:])
                    else:
                        chain.extend(list(reversed(add_pts[:-1])))
                    growing = True

            # Mo rong ve phia head cua chain
            growing = True
            while growing:
                growing = False
                head_pt = chain[0]
                gx, gy, gz = grid_key(head_pt)
                best_seg = None
                best_dist = tol_feet
                best_is_head = True

                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            neighbor_k = (gx + dx, gy + dy, gz + dz)
                            for cand_idx, cand_is_head in grid.get(neighbor_k, []):
                                if not visited[cand_idx]:
                                    cand_pt = segments[cand_idx][0] if cand_is_head else segments[cand_idx][-1]
                                    d = head_pt.DistanceTo(cand_pt)
                                    if d < best_dist:
                                        best_dist = d
                                        best_seg = cand_idx
                                        best_is_head = cand_is_head

                if best_seg is not None:
                    visited[best_seg] = True
                    add_pts = segments[best_seg]
                    if not best_is_head:
                        chain = add_pts[:-1] + chain
                    else:
                        chain = list(reversed(add_pts[1:])) + chain
                    growing = True

            all_stitched.append(PolylinePath3D(chain, lay))

    return all_stitched

def set_instance_elevation(inst, target_z_feet, level=None):
    """
    Dong bo cao do Z thuc te tuyet doi cho doi tuong Revit:
    - Neu doi tuong da o dung cao do target_z_feet (sai so < 3mm), KHONG can lam gi them (tranh loi gap doi cao do).
    - Neu bi lech (do level hosting), uu tien vi chinh bang MoveElement hoac set parameter cao do.
    """
    if inst is None:
        return False

    # 1. KIEM TRA TRUOC TIEN: Neu vi tri Location Point.Z da nam dung target_z_feet (sai so < 3mm)
    # TUYET DOI KHONG SET THEM PARAMETER de tranh Revit cong don gap doi cao do!
    try:
        if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
            cur_z = inst.Location.Point.Z
            if abs(cur_z - target_z_feet) < 0.01:
                return True
    except Exception:
        pass

    level_elev = level.Elevation if level else 0.0
    offset_val = target_z_feet - level_elev

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
        BuiltInParameter.INSTANCE_ELEVATION_PARAM,
        BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM,
        BuiltInParameter.SCHEDULE_BASE_LEVEL_OFFSET_PARAM,
        BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM,
        BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM
    ]
    for bip in param_list:
        try:
            p = inst.get_Parameter(bip)
            if p and not p.IsReadOnly:
                p.Set(offset_val)
                break
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
                break
        except Exception:
            pass

    # 5. Kiem tra lan cuoi va tinh chinh neu con lech
    try:
        if hasattr(inst, "Location") and hasattr(inst.Location, "Point") and inst.Location.Point is not None:
            cur_z_final = inst.Location.Point.Z
            diff_final = target_z_feet - cur_z_final
            if abs(diff_final) > 0.01:
                ElementTransformUtils.MoveElement(inst.Document, inst.Id, XYZ(0, 0, diff_final))
    except Exception:
        pass

    return True

def resolve_symbol(document, family_input, rfa_file=None):
    """Nhan dien FamilySymbol tu Input: co the la FamilyType object, FamilySymbol, hoac chuoi ten"""
    if family_input is None:
        return None

    # 1. Dynamo FamilyType object
    if hasattr(family_input, "InternalElement"):
        sym = family_input.InternalElement
        if not sym.IsActive:
            sym.Activate()
            document.Regenerate()
        return sym

    # 2. FamilySymbol truc tiep
    if isinstance(family_input, FamilySymbol):
        if not family_input.IsActive:
            family_input.Activate()
            document.Regenerate()
        return family_input

    # 3. Chuoi ky tu ten family
    target = str(family_input).strip().lower()
    collector = FilteredElementCollector(document).OfClass(FamilySymbol)
    for sym in collector:
        f_name, t_name = get_symbol_family_and_type(sym)
        if target == f_name.lower() or target == t_name.lower() or target in f_name.lower():
            if not sym.IsActive:
                sym.Activate()
                document.Regenerate()
            return sym

    # 4. Load tu file RFA neu chua co
    if rfa_file and os.path.exists(rfa_file):
        try:
            document.LoadFamily(rfa_file)
            document.Regenerate()
            collector = FilteredElementCollector(document).OfClass(FamilySymbol)
            for sym in collector:
                f_name, t_name = get_symbol_family_and_type(sym)
                if target == f_name.lower() or target == t_name.lower() or target in f_name.lower():
                    if not sym.IsActive:
                        sym.Activate()
                        document.Regenerate()
                    return sym
        except Exception:
            pass

    return None

def extract_paths_from_element(elem, document):
    """
    Trich xuat toan dien cac duong dan 3D Polyline, Curve, Spline, CAD Import
    hoac Dynamo PolyCurve thanh danh sach doi tuong PolylinePath3D kem theo ten Layer CAD.
    Uu tien tuyet doi GetInstanceGeometry() de lay dung 100% toa do Revit World hien thi tren man hinh!
    """
    paths = []
    if elem is None:
        return paths

    # Giai nen danh sach phang an toan cho PythonNET
    raw_list = []
    if isinstance(elem, (list, tuple)):
        for x in elem:
            if isinstance(x, (list, tuple)):
                for y in x:
                    if y is not None: raw_list.append(y)
            elif x is not None:
                raw_list.append(x)
    else:
        raw_list.append(elem)

    for item in raw_list:
        if item is None:
            continue

        revit_elem = item
        if hasattr(item, "InternalElement") and item.InternalElement is not None:
            revit_elem = item.InternalElement

        # Neu la ElementId
        if isinstance(revit_elem, ElementId):
            try:
                revit_elem = document.GetElement(revit_elem)
            except Exception:
                pass

        # 1. Dynamo PolyCurve
        if hasattr(item, "Curves"):
            try:
                sub_c = item.Curves() if callable(item.Curves) else item.Curves
                pts = []
                for sc in sub_c:
                    p = sc.StartPoint
                    pts.append(XYZ(p.X, p.Y, p.Z))
                p_end = sub_c[-1].EndPoint
                pts.append(XYZ(p_end.X, p_end.Y, p_end.Z))
                if len(pts) >= 2:
                    paths.append(PolylinePath3D(pts, "DynamoPolyCurve"))
                continue
            except Exception:
                pass

        # 1b. Dynamo Curve don le (Line, NurbsCurve...)
        if hasattr(item, "StartPoint") and hasattr(item, "EndPoint"):
            try:
                p0 = item.StartPoint
                p1 = item.EndPoint
                pts = [XYZ(p0.X, p0.Y, p0.Z), XYZ(p1.X, p1.Y, p1.Z)]
                paths.append(PolylinePath3D(pts, "DynamoCurve"))
                continue
            except Exception:
                pass

        # 2. Revit DB PolyLine truc tiep
        is_poly = False
        try:
            if isinstance(revit_elem, PolyLine) or (hasattr(revit_elem, "GetType") and revit_elem.GetType().Name == "PolyLine"):
                is_poly = True
        except Exception:
            pass

        if is_poly:
            try:
                coords = revit_elem.GetCoordinates()
                if coords:
                    pts = [p for p in coords]
                    if len(pts) >= 2:
                        paths.append(PolylinePath3D(pts, "RevitPolyLine"))
                continue
            except Exception:
                pass

        # 3. Revit DB Curve
        is_curve = False
        try:
            if isinstance(revit_elem, Curve):
                is_curve = True
        except Exception:
            pass

        if is_curve:
            try:
                tess = revit_elem.Tessellate()
                if tess:
                    pts = [p for p in tess]
                    if len(pts) >= 2:
                        paths.append(PolylinePath3D(pts, "RevitCurve"))
                continue
            except Exception:
                pass

        # 4. ModelCurve / DetailCurve / CurveElement
        if hasattr(revit_elem, "GeometryCurve") and revit_elem.GeometryCurve:
            try:
                tess = revit_elem.GeometryCurve.Tessellate()
                if tess:
                    pts = [p for p in tess]
                    if len(pts) >= 2:
                        paths.append(PolylinePath3D(pts, "ModelCurve"))
                continue
            except Exception:
                pass

        # 5. LocationCurve
        if hasattr(revit_elem, "Location") and hasattr(revit_elem.Location, "Curve") and revit_elem.Location.Curve:
            try:
                tess = revit_elem.Location.Curve.Tessellate()
                if tess:
                    pts = [p for p in tess]
                    if len(pts) >= 2:
                        paths.append(PolylinePath3D(pts, "LocationCurve"))
                continue
            except Exception:
                pass

        # 6. Trich xuat Geometry tu Element (ImportInstance CAD, DirectShape, Solids...)
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
                        if g_obj is None: return

                        # Lay ten Layer CAD neu co tu GraphicsStyle
                        layer = cur_layer
                        if hasattr(g_obj, "GraphicsStyleId") and g_obj.GraphicsStyleId != ElementId.InvalidElementId:
                            try:
                                gs = document.GetElement(g_obj.GraphicsStyleId)
                                if gs and gs.GraphicsStyleCategory:
                                    layer = gs.GraphicsStyleCategory.Name
                            except Exception:
                                pass

                        # A. GeometryInstance (Khoi CAD link/import hoac block long)
                        if isinstance(g_obj, GeometryInstance):
                            # Uu tien 1: GetInstanceGeometry() de lay dung 100% toa do Revit World va cao do 3D thuc te
                            inst_geom = None
                            try:
                                inst_geom = g_obj.GetInstanceGeometry()
                            except Exception:
                                pass

                            count_before = len(paths)
                            if inst_geom:
                                for sub_g in inst_geom:
                                    parse_geom(sub_g, layer, None)

                            if len(paths) > count_before:
                                return

                            # Uu tien 2: Fallback sang GetSymbolGeometry() kem transform
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

                        # B. PolyLine trong CAD / Revit
                        is_sub_poly = False
                        try:
                            if isinstance(g_obj, PolyLine) or (hasattr(g_obj, "GetType") and g_obj.GetType().Name == "PolyLine"):
                                is_sub_poly = True
                        except Exception:
                            pass

                        if is_sub_poly:
                            try:
                                coords = g_obj.GetCoordinates()
                                if coords:
                                    pts = []
                                    for p in coords:
                                        pts.append(transform.OfPoint(p) if transform else p)
                                    if len(pts) >= 2:
                                        paths.append(PolylinePath3D(pts, layer))
                                return
                            except Exception:
                                pass

                        # C. Curve (Line, Arc, NurbSpline, HermiteSpline) trong CAD / Revit
                        is_sub_curve = False
                        try:
                            if isinstance(g_obj, Curve):
                                is_sub_curve = True
                        except Exception:
                            pass

                        if is_sub_curve:
                            try:
                                tess = g_obj.Tessellate()
                                if tess:
                                    pts = []
                                    for p in tess:
                                        pts.append(transform.OfPoint(p) if transform else p)
                                    if len(pts) >= 2:
                                        paths.append(PolylinePath3D(pts, layer))
                                return
                            except Exception:
                                pass

                        # D. Solid
                        if isinstance(g_obj, Solid) and g_obj.Volume > 0:
                            try:
                                for edge in g_obj.Edges:
                                    c = edge.AsCurve()
                                    if c:
                                        tess = c.Tessellate()
                                        if tess:
                                            pts = []
                                            for p in tess:
                                                pts.append(transform.OfPoint(p) if transform else p)
                                            if len(pts) >= 2:
                                                paths.append(PolylinePath3D(pts, layer))
                                return
                            except Exception:
                                pass

                        # E. Container GeometryElement
                        if hasattr(g_obj, "GetEnumerator") and not isinstance(g_obj, (PolyLine, Curve, Solid)):
                            try:
                                for sub in g_obj:
                                    parse_geom(sub, layer, transform)
                                return
                            except Exception:
                                pass

                    for g in geom:
                        parse_geom(g, "", None)
            except Exception:
                pass

    return paths

def remove_parallel_duplicate_paths(paths, min_separation_feet=12.0):
    """
    Neu co 2 duong Polyline chay song song rat gan nhau (< 3.5m) nhu 2 mep trai-phai
    cua cung mot dai phan cach, chi giu lai 1 duong duy nhat (duong dai nhat)
    de tranh rai 2 hang de len nhau.
    """
    if len(paths) <= 1:
        return paths

    sorted_paths = sorted(paths, key=lambda p: p.total_length, reverse=True)
    filtered = []
    for p in sorted_paths:
        if len(p.points) < 2 or p.total_length < 1.0:
            continue
        is_dup = False
        p_len = p.total_length
        sample_fracs = [0.1, 0.3, 0.5, 0.7, 0.9]
        sample_pts = [p.evaluate(f * p_len)[0] for f in sample_fracs]

        for kept in filtered:
            dists = [kept.min_distance_to(sp) for sp in sample_pts]
            avg_d = sum(dists) / float(len(dists))
            close_count = sum(1 for d in dists if d < min_separation_feet)
            if avg_d < min_separation_feet and close_count >= 3:
                is_dup = True
                break

        if not is_dup:
            filtered.append(p)

    return filtered if filtered else paths

def cleanup_existing_instances_along_paths(document, paths, fam_name, max_dist_feet=60.0):
    """
    Quet va xoa 100% cac doi tuong ATGT cu da ton tai doc theo tuyen
    de tranh hien tuong bi trung lap / chong doi tuong khi chay Dynamo nhieu lan.
    """
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

        # Quet tat ca FamilyInstance trong project
        collector = FilteredElementCollector(document).OfClass(FamilyInstance).WhereElementIsNotElementType().ToElements()
        to_delete = []
        f_target = fam_name.lower().strip() if fam_name else ""

        atgt_keywords = [
            "dpc", "dai phan cach", "ton", "song", "guard", "barrier", "hang rao", 
            "fence", "q2p", "km52", "luoi", "chong choi", "bien bao", "vach son"
        ]

        for inst in collector:
            try:
                pt = None
                try:
                    loc = inst.Location
                    if hasattr(loc, "Point") and loc.Point is not None:
                        pt = loc.Point
                    elif hasattr(loc, "Curve") and loc.Curve is not None:
                        pt = loc.Curve.GetEndPoint(0)
                except Exception:
                    pass

                if pt is None:
                    try:
                        bb = inst.get_BoundingBox(None)
                        if bb is not None:
                            pt = XYZ((bb.Min.X + bb.Max.X) * 0.5, (bb.Min.Y + bb.Max.Y) * 0.5, (bb.Min.Z + bb.Max.Z) * 0.5)
                    except Exception:
                        pass

                if pt is None:
                    continue

                # Loc nhanh theo bounding box XY
                if pt.X < min_x or pt.X > max_x or pt.Y < min_y or pt.Y > max_y:
                    continue

                # Kiem tra xem co phai doi tuong ATGT can don dep khong
                s_fam_name = ""
                s_type_name = ""
                try:
                    type_id = inst.GetTypeId()
                    if type_id != ElementId.InvalidElementId:
                        elem_type = document.GetElement(type_id)
                        if elem_type:
                            s_type_name = str(elem_type.Name).lower()
                            if hasattr(elem_type, "FamilyName"):
                                s_fam_name = str(elem_type.FamilyName).lower()
                            elif hasattr(elem_type, "Family") and elem_type.Family:
                                s_fam_name = str(elem_type.Family.Name).lower()
                except Exception:
                    pass

                if not s_fam_name:
                    try:
                        sym = getattr(inst, "Symbol", None)
                        if sym:
                            s_type_name = str(sym.Name).lower()
                            if sym.Family:
                                s_fam_name = str(sym.Family.Name).lower()
                    except Exception:
                        pass

                mark_str = ""
                try:
                    mark_p = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                    if mark_p: mark_str = mark_p.AsString() or ""
                except Exception:
                    pass

                comm_str = ""
                try:
                    comm_p = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    if comm_p: comm_str = comm_p.AsString() or ""
                except Exception:
                    pass

                is_atgt = False
                if f_target and (f_target in s_fam_name or s_fam_name in f_target or f_target in s_type_name or s_type_name in f_target):
                    is_atgt = True
                elif any(k in s_fam_name for k in atgt_keywords):
                    is_atgt = True
                elif any(k in s_type_name for k in atgt_keywords):
                    is_atgt = True
                elif mark_str and any(k in mark_str for k in ["DPC-", "TS-", "HR-", "BB-", "VS-"]):
                    is_atgt = True
                elif comm_str and "[LOI BIM]" in comm_str:
                    is_atgt = True

                if is_atgt:
                    for p in paths:
                        if p.min_distance_to(pt) <= max_dist_feet:
                            to_delete.append(inst.Id)
                            break
            except Exception:
                pass

        if len(to_delete) > 0:
            try:
                from System.Collections.Generic import List
                del_list = List[ElementId]()
                for eid in set(to_delete):
                    del_list.Add(eid)
                del_res = document.Delete(del_list)
                deleted_count = len(del_res)
            except Exception:
                for eid in set(to_delete):
                    try:
                        document.Delete(eid)
                        deleted_count += 1
                    except Exception:
                        pass
            try:
                document.Regenerate()
            except Exception:
                pass
            write_debug_log("Da don dep {0} doi tuong cu tren tuyen de tranh trung lap.".format(deleted_count))
    except Exception as ex_clean:
        write_debug_log("Loi don dep: " + str(ex_clean))

    return deleted_count
def filter_relevant_paths(paths, fam_name, user_layer=""):
    """
    Loc cac duong Polyline phu hop voi loai Family duoc chon tu file CAD:
    - Neu chi co 1 duong duy nhat: Su dung ngay lap tuc ma khong can loc.
    - Neu co user_layer: Uu tien layer duoc chi dinh boi nguoi dung.
    - Uu tien tuyet doi cac duong co cao do 3D thuc te (|Z| > 0.05 feet hoac Z bien thien doc tuyen).
    - Tu dong loc theo keyword Family & CAD layer: DPC, TS, HR, C-TOPO-FEAT, TOPO, TIM, TUYEN...
    - Chon chuoi tuyen dai nhat de rai.
    """
    if len(paths) <= 1:
        return paths

    def clean_layer(l_str):
        if not l_str: return ""
        s = l_str.lower().strip()
        if ":" in s:
            s = s.split(":")[-1].strip()
        return s

    # 1. Neu nguoi dung chi dinh ten Layer CAD cu the (Lá»†NH 9)
    if user_layer and str(user_layer).strip():
        u_layer_clean = clean_layer(str(user_layer))
        matched = [p for p in paths if u_layer_clean in clean_layer(p.layer_name)]
        if len(matched) > 0:
            stitched = stitch_connected_paths(matched, tol_feet=2.0)
            return remove_parallel_duplicate_paths(stitched, min_separation_feet=12.0)

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
        stitched_3d = stitch_connected_paths(paths_with_elevation, tol_feet=2.0)
        if len(stitched_3d) > 0:
            stitched_3d = remove_parallel_duplicate_paths(stitched_3d, min_separation_feet=12.0)
            stitched_3d.sort(key=lambda p: p.total_length, reverse=True)
            return stitched_3d

    # 3. Tu dong loc theo keyword Family va cac Layer CAD tieu bieu trong khao sat - thiet ke duong
    fam_lower = fam_name.lower()
    target_keywords = []
    if "dpc" in fam_lower or "dai" in fam_lower or "phan cach" in fam_lower:
        target_keywords = [
            "ranh giua", "0_ranh giua", "dpc", "dai phan cach", "median", 
            "vsi_marking_3.1a", "cntr", "c-road-cntr", "c-road", "tim", "tuyen", "3d",
            "c-topo-feat", "topo", "feat", "feature", "civil", "survey", "polyline"
        ]
    elif "ts" in fam_lower or "ton" in fam_lower or "song" in fam_lower or "guard" in fam_lower:
        target_keywords = [
            "ts", "ton", "song", "guard", "ho lan", "c-road", 
            "c-topo-feat", "topo", "feat", "feature", "civil", "survey", "polyline"
        ]
    elif "hr" in fam_lower or "rao" in fam_lower or "fence" in fam_lower:
        target_keywords = [
            "hr", "rao", "fence", "b40", "thep gai", 
            "c-topo-feat", "topo", "feat", "feature", "civil", "survey", "polyline"
        ]
    else:
        target_keywords = [
            "c-topo-feat", "topo", "feat", "ranh giua", "dpc", "ts", "hr", "c-road", "tim", "tuyen"
        ]

    layer_matched = []
    for p in paths:
        l_clean = clean_layer(p.layer_name)
        if any(kw in l_clean for kw in target_keywords):
            layer_matched.append(p)

    if len(layer_matched) > 0:
        stitched_candidates = stitch_connected_paths(layer_matched, tol_feet=2.0)
        if len(stitched_candidates) > 0:
            stitched_candidates = remove_parallel_duplicate_paths(stitched_candidates, min_separation_feet=12.0)
            stitched_candidates.sort(key=lambda p: p.total_length, reverse=True)
            return stitched_candidates

    # 4. Neu khong tim thay layer phu hop, loc cac duong dai va lay chuoi dai nhat
    all_stitched = stitch_connected_paths(paths, tol_feet=2.0)
    if len(all_stitched) > 0:
        all_stitched = remove_parallel_duplicate_paths(all_stitched, min_separation_feet=12.0)
        all_stitched.sort(key=lambda p: p.total_length, reverse=True)
        top_long = [p for p in all_stitched if (p.total_length / METERS_TO_FEET) >= 5.0]
        if len(top_long) > 0:
            return top_long
        return all_stitched[:1]

    return paths

def set_param_value(target_obj, param_candidates, val_meters):
    """Tim kiem va gan gia tri cho tham so trong Revit"""
    if target_obj is None or val_meters is None:
        return False

    val_feet = float(val_meters) * METERS_TO_FEET
    for p_name in param_candidates:
        try:
            param = target_obj.LookupParameter(p_name)
            if param and not param.IsReadOnly:
                if param.StorageType == StorageType.Double:
                    param.Set(val_feet)
                    return True
                elif param.StorageType == StorageType.String:
                    param.Set(str(val_meters))
                    return True
                elif param.StorageType == StorageType.Integer:
                    param.Set(int(round(float(val_meters))))
                    return True
        except Exception:
            pass

    try:
        norm_kw = [k.lower().replace("_", "").replace(" ", "").replace("-", "") for k in param_candidates]
        for p in target_obj.Parameters:
            if p and not p.IsReadOnly and p.Definition:
                p_norm = p.Definition.Name.lower().replace("_", "").replace(" ", "").replace("-", "")
                if p_norm in norm_kw:
                    if p.StorageType == StorageType.Double:
                        p.Set(val_feet)
                        return True
                    elif p.StorageType == StorageType.String:
                        p.Set(str(val_meters))
                        return True
                    elif p.StorageType == StorageType.Integer:
                        p.Set(int(round(float(val_meters))))
                        return True
    except Exception:
        pass

    return False

def apply_dimensions(inst, length_m, height_m, width_m):
    """Gan kich thuoc L, H, W cho doi tuong"""
    applied = []
    l_candidates = ["Length", "Chiá»u dÃ i", "Chieu dai", "L", "L_dot", "L_Ä‘á»‘t", "Chiá»u dÃ i Ä‘á»‘t", 
                    "Chieu dai dot", "Segment Length", "Barrier Length", "DPC_Length", "L_dpc"]
    h_candidates = ["Height", "Chiá»u cao", "Chieu cao", "H", "H_dot", "H_Ä‘á»‘t", "Chiá»u cao Ä‘á»‘t", 
                    "Chieu cao dot", "Segment Height", "Barrier Height", "DPC_Height", "H_dpc"]
    w_candidates = ["Width", "Chiá»u rá»™ng", "Chieu rong", "Bá» rá»™ng", "Be rong", "B", "W", 
                    "Bá» rá»™ng Ä‘Ã¡y", "Be rong day", "Segment Width", "Barrier Width", "DPC_Width", "W_dot"]

    if length_m is not None and float(length_m) > 0:
        if set_param_value(inst, l_candidates, length_m):
            applied.append("L=" + str(length_m) + "m")
    if height_m is not None and float(height_m) > 0:
        if set_param_value(inst, h_candidates, height_m):
            applied.append("H=" + str(height_m) + "m")
    if width_m is not None and float(width_m) > 0:
        if set_param_value(inst, w_candidates, width_m):
            applied.append("W=" + str(width_m) + "m")

    sym = getattr(inst, "Symbol", None)
    if sym:
        if length_m is not None and float(length_m) > 0 and not any(x.startswith("L=") for x in applied):
            if set_param_value(sym, l_candidates, length_m):
                applied.append("Type L=" + str(length_m) + "m")
        if height_m is not None and float(height_m) > 0 and not any(x.startswith("H=") for x in applied):
            if set_param_value(sym, h_candidates, height_m):
                applied.append("Type H=" + str(height_m) + "m")
        if width_m is not None and float(width_m) > 0 and not any(x.startswith("W=") for x in applied):
            if set_param_value(sym, w_candidates, width_m):
                applied.append("Type W=" + str(width_m) + "m")

    return applied

def apply_loi_info(inst, index, dist_m, fam_name, prefix_input="", package_input="", material_input="", contractor_input=""):
    """
    Tu dong gan bo thong tin LOI (Level of Information) phi hinh hoc chuan BIM Ha tang Giao thong:
    1. Ma dinh danh cau kien (Mark / BIM_Code): Danh so lien tuc tang dan theo ly trinh doc tuyen (0001, 0002...).
    2. Thong tin Goi thau & Ly trinh (Package & Station).
    3. Thong tin Vat lieu & Tieu chuan ky thuat (Material & Standards).
    4. Thong tin Nha thau & Nghiem thu thi cong (Contractor & Acceptance).
    5. Gan dong thoi vao cac Project/Shared Parameters (neu co) va Parameter co san cua Revit (Mark, Comments).
    """
    if inst is None:
        return ""

    fam_lower = fam_name.lower() if fam_name else ""
    auto_prefix = "DPC-KM52-"
    auto_mat = "BTXM M300 (C25/30) - TCVN 12681:2019"
    auto_item = "Dai phan cach giua be tong xi mang"

    if "ts" in fam_lower or "ton" in fam_lower or "song" in fam_lower or "guard" in fam_lower:
        auto_prefix = "TS-KM52-"
        auto_mat = "Thep ma kem nhung nong - 22 TCN 237-01"
        auto_item = "Ho lan ton song ma kem"
    elif "hr" in fam_lower or "rao" in fam_lower or "fence" in fam_lower:
        auto_prefix = "HR-KM52-"
        auto_mat = "Luoi thep ma kem boc nhua / Thep gai"
        auto_item = "Hang rao bao ve duong cao toc"
    elif "bien" in fam_lower or "sign" in fam_lower:
        auto_prefix = "BB-KM52-"
        auto_mat = "Mang phan quang 3M Series 3900/4000 - QCVN 41:2019"
        auto_item = "Bien bao hieu giao thong duong bo"
    elif "vach" in fam_lower or "son" in fam_lower:
        auto_prefix = "VS-KM52-"
        auto_mat = "Son deo nhiet phan quang - TCVN 8791:2011"
        auto_item = "Vach son ke duong phan quang"

    prefix = prefix_input.strip() if prefix_input and prefix_input.strip() else auto_prefix
    package_str = package_input.strip() if package_input and package_input.strip() else "Goi thau XL01 | Km52+000 - Km60+000"
    material_str = material_input.strip() if material_input and material_input.strip() else auto_mat
    contractor_str = contractor_input.strip() if contractor_input and contractor_input.strip() else "Lien danh XL01 | Cho nghiem thu"

    # Ma cau kien danh so 4 chu so lien tuc: DPC-KM52-0001, DPC-KM52-0002...
    mark_code = "{0}{1:04d}".format(prefix, index + 1)
    chainage_approx = "+{0:03d}m (s={1:.1f}m)".format(int(dist_m % 1000), dist_m)

    # A. Gan BuiltInParameter.ALL_MODEL_MARK (Mark - Chuan Revit)
    try:
        p_mark = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if p_mark and not p_mark.IsReadOnly:
            p_mark.Set(mark_code)
    except Exception:
        pass

    # B. Gan BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS (Comments - Bang tong hop LOI)
    loi_summary = "[LOI BIM] Ma: {0} | Hang muc: {1} | {2} | {3} | {4} | Vi tri: s={5:.1f}m".format(
        mark_code, auto_item, package_str, material_str, contractor_str, dist_m
    )
    try:
        p_comm = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p_comm and not p_comm.IsReadOnly:
            p_comm.Set(loi_summary)
    except Exception:
        pass

    # C. Quet va gan cac Project Parameters / Shared Parameters tuy chinh cua duan
    mapping = [
        (["Ma cau kien", "MÃ£ cáº¥u kiá»‡n", "Ma_Cau_Kien", "BIM_Code", "Code_Cau_Kien", "So hieu", "Element_Code", "Mark_Code"], mark_code),
        (["Goi thau", "GÃ³i tháº§u", "Goi_Thau", "Package", "Subproject", "Du an", "Project_Name"], package_str),
        (["Ly trinh", "LÃ½ trÃ¬nh", "Ly_Trinh", "Station", "Chainage", "Phan doan", "Station_Range"], package_str + " | " + chainage_approx),
        (["Hang muc", "Háº¡ng má»¥c", "Hang_Muc", "Item", "Category_Item", "Work_Item"], auto_item),
        (["Vat lieu", "Váº­t liá»‡u", "Vat_Lieu", "Material", "Mac be tong", "Lop phu"], material_str),
        (["Tieu chuan", "TiÃªu chuáº©n", "Tieu_Chuan", "Specification", "Standard", "Tieu chuan ky thuat"], material_str),
        (["Nha thau", "NhÃ  tháº§u", "Nha_Thau", "Contractor", "Don vi thi cong", "Nha_Thau_Thi_Cong"], contractor_str),
        (["Tinh trang", "TÃ¬nh tráº¡ng", "Tinh_Trang", "Status", "Nghiem thu", "Acceptance_Status", "Tinh trang nghiem thu"], contractor_str),
    ]

    for candidates, val in mapping:
        for c_name in candidates:
            try:
                p = inst.LookupParameter(c_name)
                if p and not p.IsReadOnly and p.StorageType == StorageType.String:
                    p.Set(str(val))
                    break
            except Exception:
                pass

    return mark_code


def distribute_along_paths(document, paths, symbol, length_m, height_m, width_m, gap_m, z_offset_m, rot_offset_deg=0.0,
                           lateral_offset_m=0.0,
                           loi_prefix="", loi_package="", loi_material="", loi_contractor=""):
    """
    Rai Family doc theo danh sach duong dan 3D Polyline:
    - THUAT TOAN DAY CUNG CHUAN (CHORD-BASED SEQUENTIAL PLACEMENT):
      Cac dot tiep giap nhau 100% tai diem dau/cuoi (s_start -> s_end)
      Khac phuc triet de loi chong doi tuong (khong can phan bo goc xoay sai lech)
      Cac dot nam 100% dung tim polyline ca ve cao do Z va huong tuyen
    - Ho tro DO LECH TIM MAT BANG (Lateral Offset): Cho phep nguoi dung offset sang trai (<0) hoac phai (>0)
    - Ho tro ca Curve-Based (Line-Based) Family va Point-Based Family
    - Tu dong can chinh chieu dai Family chay song song voi tim tuyen
    - Chuan xac 100% cao do 3D cua Polyline thuc dia
    - Tu dong don dep doi tuong cu de tranh trung lap
    """
    block_len_feet = float(length_m) * METERS_TO_FEET
    gap_feet = float(gap_m) * METERS_TO_FEET
    eff_spacing_feet = block_len_feet + gap_feet
    if eff_spacing_feet <= 0.1:
        eff_spacing_feet = 5.0 * METERS_TO_FEET

    z_offset_feet = float(z_offset_m) * METERS_TO_FEET
    lat_offset_feet = float(lateral_offset_m) * METERS_TO_FEET
    user_rot_offset = (float(rot_offset_deg) * math.pi / 180.0) if rot_offset_deg is not None else 0.0
    created_count = 0
    errors = []
    param_applied_summary = None
    first_mark_code = ""
    last_mark_code = ""

    levels = FilteredElementCollector(document).OfClass(Level).ToElements()
    default_level = levels[0] if len(levels) > 0 else None

    # Kiem tra loai placement cua Family (CurveBased vs PointBased)
    is_curve_based = False
    try:
        if hasattr(symbol, "Family") and symbol.Family:
            is_curve_based = (symbol.Family.FamilyPlacementType == FamilyPlacementType.CurveBased)
    except Exception:
        pass

    # Loc va noi cac duong dan
    stitched_paths = stitch_connected_paths(paths)
    valid_paths = [p for p in stitched_paths if (p.total_length / METERS_TO_FEET) >= 0.5]
    if len(valid_paths) == 0 and len(stitched_paths) > 0:
        valid_paths = stitched_paths

    total_path_len_m = sum(p.total_length for p in valid_paths) / METERS_TO_FEET

    write_debug_log("distribute_along_paths: valid_paths={0}, total_len_m={1:.2f}".format(len(valid_paths), total_path_len_m))
    if len(valid_paths) > 0:
        p0 = valid_paths[0].points[0]
        p_end = valid_paths[0].points[-1]
        write_debug_log("  Path start: ({0:.2f}, {1:.2f}, {2:.2f}) -> end: ({3:.2f}, {4:.2f}, {5:.2f})".format(
            p0.X, p0.Y, p0.Z, p_end.X, p_end.Y, p_end.Z
        ))

    fam_name = ""
    try:
        if hasattr(symbol, "Family") and symbol.Family:
            fam_name = symbol.Family.Name
        elif hasattr(symbol, "Name"):
            fam_name = symbol.Name
    except Exception:
        pass

    # 0. Tu dong don dep cac doi tuong ATGT cu tren cung duong dan de tranh loi trung lap khi chay lai nhieu lan
    cleaned_old_count = cleanup_existing_instances_along_paths(document, valid_paths, fam_name, max_dist_feet=60.0)

    # Bo nho toa do tam cac dot da rai de chong trung lap / de len nhau 100%
    placed_centers = []

    for path in valid_paths:
        try:
            path_len = path.total_length
            if path_len < 0.2:
                continue

            current_s = 0.0

            # Vong lap rai theo doan day cung noi tiep (Chord-Based)
            while current_s + (block_len_feet * 0.88) <= path_len:
                s_start = current_s
                s_end = min(path_len, s_start + block_len_feet)

                # 1. Lay toa do 3D diem dau va diem cuoi cua dot tren duong 3D Polyline
                p_start_eval, _ = path.evaluate(s_start)
                p_end_eval, _   = path.evaluate(s_end)

                p1 = XYZ(p_start_eval.X, p_start_eval.Y, p_start_eval.Z + z_offset_feet)
                p2 = XYZ(p_end_eval.X,   p_end_eval.Y,   p_end_eval.Z   + z_offset_feet)

                # Vector day cung 3D
                chord_dx = p2.X - p1.X
                chord_dy = p2.Y - p1.Y
                chord_dz = p2.Z - p1.Z
                chord_len_2d = math.sqrt(chord_dx * chord_dx + chord_dy * chord_dy)

                if chord_len_2d < 1e-4:
                    current_s += eff_spacing_feet
                    continue

                # 2. Tinh do lech tim mat bang (Lateral Offset) vuong goc voi huong day cung
                # Phap tuyen mat bang: Chieu duong = Lech sang PHAI, Chieu am = Lech sang TRAI
                offset_dx = 0.0
                offset_dy = 0.0
                if abs(lat_offset_feet) > 1e-5:
                    offset_dx = ( chord_dy / chord_len_2d) * lat_offset_feet
                    offset_dy = (-chord_dx / chord_len_2d) * lat_offset_feet

                p1_off = XYZ(p1.X + offset_dx, p1.Y + offset_dy, p1.Z)
                p2_off = XYZ(p2.X + offset_dx, p2.Y + offset_dy, p2.Z)

                if is_curve_based:
                    # ==========================================================
                    # TRUONG HOP A: Family la CurveBased (Line-Based Family)
                    # ==========================================================
                    if p1_off.DistanceTo(p2_off) < 0.05:
                        current_s += eff_spacing_feet
                        continue

                    curve_mid = XYZ((p1_off.X + p2_off.X) * 0.5, (p1_off.Y + p2_off.Y) * 0.5, (p1_off.Z + p2_off.Z) * 0.5)
                    is_clash = False
                    for pc in placed_centers:
                        if curve_mid.DistanceTo(pc) < (block_len_feet * 0.85):
                            is_clash = True
                            break
                    if is_clash:
                        current_s += eff_spacing_feet
                        continue

                    inst = None
                    try:
                        line_3d = Line.CreateBound(p1_off, p2_off)
                        inst = document.Create.NewFamilyInstance(line_3d, symbol, default_level, StructuralType.NonStructural)
                    except Exception:
                        pass

                    if inst is None and default_level:
                        try:
                            line_horiz = Line.CreateBound(
                                XYZ(p1_off.X, p1_off.Y, default_level.Elevation),
                                XYZ(p2_off.X, p2_off.Y, default_level.Elevation)
                            )
                            inst = document.Create.NewFamilyInstance(line_horiz, symbol, default_level, StructuralType.NonStructural)
                            mid_z = (p1_off.Z + p2_off.Z) / 2.0
                            set_instance_elevation(inst, mid_z, default_level)
                        except Exception as ex_c:
                            if len(errors) < 3:
                                errors.append("Loi CurveBased: " + str(ex_c))
                            current_s += eff_spacing_feet
                            continue

                    if inst is not None:
                        placed_centers.append(curve_mid)
                        res_params = apply_dimensions(inst, length_m, height_m, width_m)
                        if res_params and param_applied_summary is None:
                            param_applied_summary = ", ".join(res_params)
                        mk = apply_loi_info(inst, created_count, s_start / METERS_TO_FEET, fam_name, loi_prefix, loi_package, loi_material, loi_contractor)
                        if not first_mark_code: first_mark_code = mk
                        last_mark_code = mk
                        created_count += 1

                else:
                    # ==========================================================
                    # TRUONG HOP B: Family la Point-Based (Generic Model, DPC, TS...)
                    # DAT TAI TRUNG DIEM DAY CUNG 3D (CHORD MIDPOINT)
                    # KHOP KHIT 100% MOI NOI, KHONG HO, KHONG CHONG LAN
                    # ==========================================================
                    mid_pt = XYZ(
                        (p1_off.X + p2_off.X) * 0.5,
                        (p1_off.Y + p2_off.Y) * 0.5,
                        (p1_off.Z + p2_off.Z) * 0.5
                    )

                    # Kiem tra chong trung bang khoang cach tam
                    is_clash = False
                    for pc in placed_centers:
                        if mid_pt.DistanceTo(pc) < (block_len_feet * 0.85):
                            is_clash = True
                            break
                    if is_clash:
                        current_s += eff_spacing_feet
                        continue

                    # Goc xoay mat bang (Yaw) CHUAN XAC theo huong day cung noi tu p1 sang p2
                    chord_yaw = math.atan2(chord_dy, chord_dx)
                    final_yaw_rot = chord_yaw + user_rot_offset

                    # Goc doc doc (Pitch)
                    pitch_angle = math.atan2(chord_dz, chord_len_2d)

                    # Khoi tao FamilyInstance
                    inst = None
                    try:
                        inst = document.Create.NewFamilyInstance(mid_pt, symbol, StructuralType.NonStructural)
                    except Exception:
                        pass

                    if inst is None and default_level:
                        try:
                            inst = document.Create.NewFamilyInstance(mid_pt, symbol, default_level, StructuralType.NonStructural)
                        except Exception:
                            pass

                    if inst is None and default_level:
                        try:
                            inst = document.Create.NewFamilyInstance(mid_pt, symbol, default_level, StructuralType.Beam)
                        except Exception as ex_create:
                            if len(errors) < 3:
                                errors.append("Loi tao instance: " + str(ex_create))
                            current_s += eff_spacing_feet
                            continue

                    if inst is None:
                        current_s += eff_spacing_feet
                        continue

                    placed_centers.append(mid_pt)

                    # Dong bo cao do Z 3D
                    set_instance_elevation(inst, mid_pt.Z, default_level)

                    # Xoay mat bang (Yaw) song song theo dung huong doan day cung
                    if abs(final_yaw_rot) > 1e-5:
                        try:
                            center_pt = inst.Location.Point
                            axis_yaw = Line.CreateBound(center_pt, XYZ(center_pt.X, center_pt.Y, center_pt.Z + 10.0))
                            ElementTransformUtils.RotateElement(document, inst.Id, axis_yaw, final_yaw_rot)
                        except Exception:
                            pass

                    # Xoay doc doc (Pitch) neu can
                    if abs(pitch_angle) > 1e-6:
                        try:
                            center_pt = inst.Location.Point
                            v_pitch_x = math.sin(chord_yaw)
                            v_pitch_y = -math.cos(chord_yaw)
                            axis_pitch_end = XYZ(
                                center_pt.X + 10.0 * v_pitch_x,
                                center_pt.Y + 10.0 * v_pitch_y,
                                center_pt.Z
                            )
                            axis_pitch = Line.CreateBound(center_pt, axis_pitch_end)
                            ElementTransformUtils.RotateElement(document, inst.Id, axis_pitch, pitch_angle)
                        except Exception as ex_pitch:
                            write_debug_log("Khong the xoay pitch: " + str(ex_pitch))

                    # Gan tham so kich thuoc L, H, W
                    res_params = apply_dimensions(inst, length_m, height_m, width_m)
                    if res_params and param_applied_summary is None:
                        param_applied_summary = ", ".join(res_params)

                    # Gan thong tin LOI BIM
                    mk = apply_loi_info(inst, created_count, s_start / METERS_TO_FEET, fam_name, loi_prefix, loi_package, loi_material, loi_contractor)
                    if not first_mark_code: first_mark_code = mk
                    last_mark_code = mk

                    if created_count == 0:
                        write_debug_log("  First instance placed at: ({0:.2f}, {1:.2f}, {2:.2f}), chord_yaw={3:.2f} deg, final_yaw={4:.2f} deg".format(
                            inst.Location.Point.X, inst.Location.Point.Y, inst.Location.Point.Z,
                            chord_yaw * 180.0 / math.pi, final_yaw_rot * 180.0 / math.pi
                        ))

                    created_count += 1

                # BUOC NHAY CHUAN XAC: Diem dau dot sau = Diem cuoi dot truoc + khe ho (gap)
                current_s = s_end + gap_feet

        except Exception as ex:
            if len(errors) < 3:
                errors.append(str(ex))

    loi_range = "{0} -> {1}".format(first_mark_code, last_mark_code) if first_mark_code else ""
    return created_count, total_path_len_m, param_applied_summary, loi_range, errors, cleaned_old_count

# ------------------------------------------------------------------------------
# ENTRY POINT DYNAMO
# ------------------------------------------------------------------------------
if IS_DYNAMO:
    # IN[0]: Doi tuong duoc chon (3D Polyline, Curve, ImportInstance CAD, Model Line)
    selected_elem = IN[0] if len(IN) > 0 else None

    # IN[1]: Family Type
    fam_input = IN[1] if len(IN) > 1 and IN[1] else "DPC_L=5M"

    # IN[2] -> IN[6]
    length_val     = float(IN[2]) if len(IN) > 2 and IN[2] else 5.0
    height_val     = float(IN[3]) if len(IN) > 3 and IN[3] else 0.9
    width_val      = float(IN[4]) if len(IN) > 4 and IN[4] else 0.6
    gap_val        = float(IN[5]) if len(IN) > 5 and IN[5] else 0.0
    z_offset_val   = float(IN[6]) if len(IN) > 6 and IN[6] else 0.0

    rot_offset_val = 0.0
    lateral_offset_val = 0.0

    # IN[7]: Goc xoay bu (Do) - Ho tro cu phap mo rong nhu "0.0; offset=0.25"
    if len(IN) > 7 and IN[7] is not None and str(IN[7]).strip() != "":
        raw_rot_str = str(IN[7]).strip()
        if ";" in raw_rot_str or "offset" in raw_rot_str.lower() or "," in raw_rot_str:
            parts = raw_rot_str.replace(";", ",").split(",")
            for part in parts:
                p_trim = part.strip()
                if "offset" in p_trim.lower() or "lech" in p_trim.lower():
                    try:
                        lateral_offset_val = float(p_trim.split("=")[-1].strip())
                    except Exception:
                        pass
                else:
                    try:
                        rot_offset_val = float(p_trim)
                    except Exception:
                        pass
        else:
            try:
                rot_offset_val = float(raw_rot_str)
            except Exception:
                pass

    cad_layer_val  = str(IN[8]).strip() if len(IN) > 8 and IN[8] else ""

    # IN[9]: Khoang lech tim mat bang (m) HOAC Tien to LOI neu la chuoi text
    loi_prefix     = ""
    if len(IN) > 9 and IN[9] is not None and str(IN[9]).strip() != "":
        val_str_9 = str(IN[9]).strip()
        try:
            lateral_offset_val = float(val_str_9)
        except ValueError:
            loi_prefix = val_str_9

    # IN[10] -> IN[13]: Thong tin LOI BIM
    loi_package    = str(IN[10]).strip() if len(IN) > 10 and IN[10] is not None and str(IN[10]).strip() != "" else "Goi thau XL01 | Km52+000 - Km60+000"
    loi_material   = str(IN[11]).strip() if len(IN) > 11 and IN[11] is not None and str(IN[11]).strip() != "" else "BTXM M300 (C25/30) - TCVN 12681:2019"
    loi_contractor = str(IN[12]).strip() if len(IN) > 12 and IN[12] is not None and str(IN[12]).strip() != "" else "Lien danh XL01 | Cho nghiem thu"

    # Ghi log chan doan
    write_debug_log("=== EXECUTION (CHORD-BASED NO-OVERLAP) ===")
    write_debug_log("selected_elem: " + str(selected_elem))
    write_debug_log("fam_input: " + str(fam_input))
    write_debug_log("params: L={0}, H={1}, W={2}, Gap={3}, Z_off={4}, Rot={5}, Lat_off={6}".format(
        length_val, height_val, width_val, gap_val, z_offset_val, rot_offset_val, lateral_offset_val
    ))

    effective_spacing = length_val + gap_val

    # Tu dong phat hien duong dan Family RFA mac dinh neu chua load vao project
    default_rfa = ""
    candidate_rfa_paths = [
        r"H:\My Drive\1.Work\ATGT\Tool ATGT\Data\01_DPC\Family\DPC_L=5M.rfa",
        r"G:\My Drive\1.Work\ATGT\Tool ATGT\Data\01_DPC\Family\DPC_L=5M.rfa",
        r"H:\My Drive\1.Work\ATGT\Tool ATGT\Data\01_DPC\Family\DPC_L=3M.rfa",
        r"G:\My Drive\1.Work\ATGT\Tool ATGT\Data\01_DPC\Family\DPC_L=3M.rfa",
    ]
    for r_path in candidate_rfa_paths:
        if r_path and os.path.exists(r_path):
            default_rfa = r_path
            break

    TransactionManager.Instance.EnsureInTransaction(doc)
    symbol = resolve_symbol(doc, fam_input, default_rfa)

    if not symbol:
        TransactionManager.Instance.TransactionTaskDone()
        OUT = "ERROR: Khong tim thay FamilyType duoc chon: " + str(fam_input) + ". Vui long kiem tra dropdown Family Types!"
    else:
        fam_name = symbol.Family.Name if symbol.Family else symbol.Name

        dim_desc = "Kich thuoc: L={0}m, H={1}m, W={2}m, Khe ho={3}m (Buoc rai={4}m)".format(
            length_val, height_val, width_val, gap_val, effective_spacing
        )

        if selected_elem is not None:
            raw_paths = extract_paths_from_element(selected_elem, doc)
            write_debug_log("raw_paths count: " + str(len(raw_paths)))
            
            # Loc dung layer va chuoi duong tim dai nhat cua tuyen co cao do 3D
            paths = filter_relevant_paths(raw_paths, fam_name, cad_layer_val)
            write_debug_log("filtered paths count: " + str(len(paths)))

            if len(paths) > 0:
                count, total_len_m, p_summary, loi_range, errs, cleaned_cnt = distribute_along_paths(
                    doc, paths, symbol, length_val, height_val, width_val, gap_val, z_offset_val, rot_offset_val,
                    lateral_offset_val,
                    loi_prefix, loi_package, loi_material, loi_contractor
                )
                TransactionManager.Instance.TransactionTaskDone()
                if count > 0:
                    param_msg = (" | Tham so: [" + p_summary + "]") if p_summary else ""
                    layer_info = (" (Layer: " + paths[0].layer_name + ")") if (paths and paths[0].layer_name) else ""
                    clean_msg = (" | Da tu dong xoa {0} doi tuong cu trung lap doc tuyen".format(cleaned_cnt)) if cleaned_cnt > 0 else ""
                    lat_info = (" | Lech tim: {0:+.2f}m".format(lateral_offset_val)) if abs(lateral_offset_val) > 1e-4 else " | Chuan 100% tim polyline"
                    
                    # Thong tin cao do 3D kiem chung
                    z_sample_m = (paths[0].points[0].Z / METERS_TO_FEET) if len(paths[0].points) > 0 else 0.0
                    elev_info = " | Cao do Z ~ {0:.2f}m (Z Offset={1}m)".format(z_sample_m, z_offset_val)
                    
                    loi_info = " | [LOI BIM]: Da gan ma [{0}], {1}, {2}, {3}".format(loi_range, loi_package, loi_material, loi_contractor) if loi_range else ""
                    OUT = "THANH CONG: Da rai {0} doi tuong [{1}] bam theo 3D Polyline theo day cung noi tiep (KHONG CHONG LAN){2}! (Tong L = {3:.1f}m){4}{5}{6}{7}{8}{9}".format(
                        count, fam_name, layer_info, total_len_m, dim_desc, lat_info, elev_info, param_msg, loi_info, clean_msg
                    )
                else:
                    OUT = "ERROR: Khong rai duoc tren 3D Polyline da chon. " + ("; ".join(errs) if errs else "Vui long kiem tra lai doi tuong.")
            else:
                TransactionManager.Instance.TransactionTaskDone()
                elem_name_str = getattr(selected_elem, "Name", str(selected_elem))
                OUT = "ERROR: Khong tim thay duong Polyline/Curve hop le trong doi tuong da chon [{0}] (Tim thay {1} duong tho). Vui long kiem tra Layer CAD hoac chon duong Model Line!".format(
                    elem_name_str, len(raw_paths)
                )
        else:
            TransactionManager.Instance.TransactionTaskDone()
            OUT = "HUONG DAN: Vui long click 'Select' o BUOC 1 de chon duong 3D Polyline / CAD Import / Model Line tren man hinh Revit!"
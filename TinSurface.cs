using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using System.Globalization;

public class Point3D {
    public double X, Y, Z;
    public Point3D(double x, double y, double z) { X = x; Y = y; Z = z; }
}

public class Triangle {
    public int P1, P2, P3;
    public double MinX, MaxX, MinY, MaxY;
    public double A, B, C, D;
}

public class TinSurface {
    public string Name;
    public Dictionary<int, Point3D> Points = new Dictionary<int, Point3D>();
    public List<Triangle> Triangles = new List<Triangle>();
    
    private double cellSize = 20.0; // 20m cells
    private Dictionary<long, List<int>> triGrid = new Dictionary<long, List<int>>();
    private Dictionary<long, List<int>> ptGrid = new Dictionary<long, List<int>>();

    public static List<TinSurface> LoadAllFromXml(string xmlPath) {
        List<TinSurface> surfaces = new List<TinSurface>();
        XmlDocument doc = new XmlDocument();
        doc.Load(xmlPath);
        XmlNamespaceManager nsmgr = new XmlNamespaceManager(doc.NameTable);
        nsmgr.AddNamespace("lx", doc.DocumentElement.NamespaceURI);

        XmlNodeList sNodes = doc.SelectNodes("//lx:Surface", nsmgr);
        foreach (XmlNode sn in sNodes) {
            TinSurface ts = new TinSurface();
            ts.Name = sn.Attributes["name"] != null ? sn.Attributes["name"].Value : "Unknown";
            
            XmlNodeList pNodes = sn.SelectNodes(".//lx:P", nsmgr);
            foreach (XmlNode pn in pNodes) {
                int id = int.Parse(pn.Attributes["id"].Value);
                string[] parts = pn.InnerText.Trim().Split(new char[]{' '}, StringSplitOptions.RemoveEmptyEntries);
                // LandXML: Northing (Y), Easting (X), Elevation (Z)
                double n = double.Parse(parts[0], CultureInfo.InvariantCulture);
                double e = double.Parse(parts[1], CultureInfo.InvariantCulture);
                double z = double.Parse(parts[2], CultureInfo.InvariantCulture);
                ts.Points[id] = new Point3D(e, n, z);
                ts.IndexPoint(id, e, n);
            }

            XmlNodeList fNodes = sn.SelectNodes(".//lx:F", nsmgr);
            int triIdx = 0;
            foreach (XmlNode fn in fNodes) {
                string[] parts = fn.InnerText.Trim().Split(new char[]{' '}, StringSplitOptions.RemoveEmptyEntries);
                int p1 = int.Parse(parts[0]);
                int p2 = int.Parse(parts[1]);
                int p3 = int.Parse(parts[2]);

                if (!ts.Points.ContainsKey(p1) || !ts.Points.ContainsKey(p2) || !ts.Points.ContainsKey(p3)) continue;

                Point3D pt1 = ts.Points[p1];
                Point3D pt2 = ts.Points[p2];
                Point3D pt3 = ts.Points[p3];

                Triangle tri = new Triangle();
                tri.P1 = p1; tri.P2 = p2; tri.P3 = p3;
                tri.MinX = Math.Min(pt1.X, Math.Min(pt2.X, pt3.X));
                tri.MaxX = Math.Max(pt1.X, Math.Max(pt2.X, pt3.X));
                tri.MinY = Math.Min(pt1.Y, Math.Min(pt2.Y, pt3.Y));
                tri.MaxY = Math.Max(pt1.Y, Math.Max(pt2.Y, pt3.Y));

                // Plane normal (pt2 - pt1) x (pt3 - pt1)
                double v1x = pt2.X - pt1.X, v1y = pt2.Y - pt1.Y, v1z = pt2.Z - pt1.Z;
                double v2x = pt3.X - pt1.X, v2y = pt3.Y - pt1.Y, v2z = pt3.Z - pt1.Z;
                tri.A = v1y * v2z - v1z * v2y;
                tri.B = v1z * v2x - v1x * v2z;
                tri.C = v1x * v2y - v1y * v2x;
                tri.D = -(tri.A * pt1.X + tri.B * pt1.Y + tri.C * pt1.Z);

                ts.Triangles.Add(tri);
                ts.IndexTriangle(tri, triIdx++);
            }
            surfaces.Add(ts);
        }
        return surfaces;
    }

    private void IndexPoint(int id, double x, double y) {
        int gx = (int)Math.Floor(x / cellSize);
        int gy = (int)Math.Floor(y / cellSize);
        long key = (((long)gx) << 32) ^ (long)(uint)gy;
        List<int> list;
        if (!ptGrid.TryGetValue(key, out list)) {
            list = new List<int>();
            ptGrid[key] = list;
        }
        list.Add(id);
    }

    private void IndexTriangle(Triangle tri, int idx) {
        int minGx = (int)Math.Floor(tri.MinX / cellSize);
        int maxGx = (int)Math.Floor(tri.MaxX / cellSize);
        int minGy = (int)Math.Floor(tri.MinY / cellSize);
        int maxGy = (int)Math.Floor(tri.MaxY / cellSize);

        for (int gx = minGx; gx <= maxGx; gx++) {
            for (int gy = minGy; gy <= maxGy; gy++) {
                long key = (((long)gx) << 32) ^ (long)(uint)gy;
                List<int> list;
                if (!triGrid.TryGetValue(key, out list)) {
                    list = new List<int>();
                    triGrid[key] = list;
                }
                list.Add(idx);
            }
        }
    }

    public double? GetElevation(double x, double y) {
        int gx = (int)Math.Floor(x / cellSize);
        int gy = (int)Math.Floor(y / cellSize);
        long key = (((long)gx) << 32) ^ (long)(uint)gy;

        List<int> candidateIdxs;
        if (!triGrid.TryGetValue(key, out candidateIdxs)) return null;

        foreach (int idx in candidateIdxs) {
            Triangle tri = Triangles[idx];
            if (x < tri.MinX - 1e-4 || x > tri.MaxX + 1e-4 || y < tri.MinY - 1e-4 || y > tri.MaxY + 1e-4) continue;

            Point3D p1 = Points[tri.P1];
            Point3D p2 = Points[tri.P2];
            Point3D p3 = Points[tri.P3];

            // Determinant
            double d = (p2.Y - p3.Y) * (p1.X - p3.X) + (p3.X - p2.X) * (p1.Y - p3.Y);
            if (Math.Abs(d) < 1e-11) continue;

            double w1 = ((p2.Y - p3.Y) * (x - p3.X) + (p3.X - p2.X) * (y - p3.Y)) / d;
            double w2 = ((p3.Y - p1.Y) * (x - p3.X) + (p1.X - p3.X) * (y - p3.Y)) / d;
            double w3 = 1.0 - w1 - w2;

            if (w1 >= -1e-4 && w2 >= -1e-4 && w3 >= -1e-4) {
                if (Math.Abs(tri.C) > 1e-9) {
                    return -(tri.A * x + tri.B * y + tri.D) / tri.C;
                }
            }
        }
        return null;
    }

    public double? GetElevationRobust(double x, double y, double maxDistance = 80.0) {
        // 1. Exact triangle test
        double? exact = GetElevation(x, y);
        if (exact.HasValue) return exact.Value;

        // 2. Expand search rings for nearby surface points (IDW)
        int centerGx = (int)Math.Floor(x / cellSize);
        int centerGy = (int)Math.Floor(y / cellSize);
        int maxR = (int)Math.Ceiling(maxDistance / cellSize);

        double bestDist1 = double.MaxValue, bestDist2 = double.MaxValue, bestDist3 = double.MaxValue;
        Point3D bestPt1 = null, bestPt2 = null, bestPt3 = null;

        for (int r = 0; r <= maxR; r++) {
            for (int gx = centerGx - r; gx <= centerGx + r; gx++) {
                for (int gy = centerGy - r; gy <= centerGy + r; gy++) {
                    if (Math.Abs(gx - centerGx) != r && Math.Abs(gy - centerGy) != r) continue;
                    long key = (((long)gx) << 32) ^ (long)(uint)gy;
                    List<int> ptIds;
                    if (ptGrid.TryGetValue(key, out ptIds)) {
                        foreach (int id in ptIds) {
                            Point3D p = Points[id];
                            double dist = Math.Sqrt((p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y));
                            if (dist > maxDistance) continue;

                            if (dist < bestDist1) {
                                bestDist3 = bestDist2; bestPt3 = bestPt2;
                                bestDist2 = bestDist1; bestPt2 = bestPt1;
                                bestDist1 = dist; bestPt1 = p;
                            } else if (dist < bestDist2) {
                                bestDist3 = bestDist2; bestPt3 = bestPt2;
                                bestDist2 = dist; bestPt2 = p;
                            } else if (dist < bestDist3) {
                                bestDist3 = dist; bestPt3 = p;
                            }
                        }
                    }
                }
            }
            if (bestPt3 != null && r >= 1) break;
        }

        if (bestPt1 == null) return null;
        if (bestDist1 < 0.05 || bestPt2 == null) return bestPt1.Z;

        // Inverse distance weighted interpolation (IDW)
        double w1 = 1.0 / (bestDist1 * bestDist1);
        double w2 = 1.0 / (bestDist2 * bestDist2);
        double totalW = w1 + w2;
        double totalZ = w1 * bestPt1.Z + w2 * bestPt2.Z;

        if (bestPt3 != null) {
            double w3 = 1.0 / (bestDist3 * bestDist3);
            totalW += w3;
            totalZ += w3 * bestPt3.Z;
        }

        return totalZ / totalW;
    }
}

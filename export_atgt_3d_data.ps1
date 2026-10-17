# ==============================================================================
# Script: export_atgt_3d_data.ps1
# Muc dich: Doc binh do CAD 2D va be mat LandXML, noi suy cao do 3D va goc xoay,
#          xuat toan bo du lieu ATGT chuan bi cho dung mo hinh trong Autodesk Revit.
# ==============================================================================

param(
    [string]$CadTsvPath = "H:\My Drive\1.Work\ATGT\Tool ATGT\cad_extracted_data.tsv",
    [string]$XmlPath = "H:\My Drive\1.Work\ATGT\Tool ATGT\Data\XML\TOP CAC CAU.xml",
    [string]$OutputDir = "H:\My Drive\1.Work\ATGT\Tool ATGT\output_3d"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> BUOC 1: NAP THU VIEN TIN SURFACE VA BE MAT LANDXML <<<" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$tinCsPath = "H:\My Drive\1.Work\ATGT\Tool ATGT\TinSurface.cs"
Add-Type -Path $tinCsPath -ReferencedAssemblies "System.Xml"

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$surfaces = [TinSurface]::LoadAllFromXml($XmlPath)
$sw.Stop()
Write-Host "-> Da nap $($surfaces.Count) be mat tu LandXML trong $($sw.ElapsedMilliseconds) ms." -ForegroundColor Green
foreach ($s in $surfaces) {
    Write-Host "   + Be mat: '$($s.Name)' (Diem: $($s.Points.Count), Tam giac: $($s.Triangles.Count))"
}

# Ham lay cao do tu danh sach be mat
function Get-SurfaceZ ([double]$x, [double]$y, [double]$maxDist = 100.0) {
    foreach ($s in $surfaces) {
        $e = $s.GetElevationRobust($x, $y, $maxDist)
        if ($null -ne $e) { return [Math]::Round([double]$e, 3) }
    }
    return $null
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host ">>> BUOC 2: DOC DU LIEU CAD DA TRICH XUAT <<<" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$cadLines = Get-Content $CadTsvPath
$rawBlocks = @()
$rawPolylines = @()
$currentSection = ""

foreach ($line in $cadLines) {
    if ($line -eq "[BLOCK_INSERTS]") { $currentSection = "BLOCKS"; continue }
    if ($line -eq "[POLYLINES]") { $currentSection = "POLYLINES"; continue }
    if ($line -eq "[LAYERS]") { $currentSection = "LAYERS"; continue }

    if ($currentSection -eq "BLOCKS" -and -not $line.StartsWith("Name`t")) {
        $rawBlocks += $line
    } elseif ($currentSection -eq "POLYLINES" -and -not $line.StartsWith("Handle`t")) {
        $rawPolylines += $line
    }
}
Write-Host "-> Tong so Block CAD: $($rawBlocks.Count)" -ForegroundColor Green
Write-Host "-> Tong so Polyline CAD: $($rawPolylines.Count)" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host ">>> BUOC 3: XU LY BIEN BAO (BLOCK INSERTS) SANG 3D <<<" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$signRecords = @()
$signId = 1
$ci = [System.Globalization.CultureInfo]::InvariantCulture

foreach ($bStr in $rawBlocks) {
    $parts = $bStr.Split("`t")
    if ($parts.Count -lt 7) { continue }

    $effName = $parts[0].Trim('"')
    $bName = $parts[1].Trim('"')
    $layer = $parts[2]
    $x = [double]::Parse($parts[3], $ci)
    $y = [double]::Parse($parts[4], $ci)
    $cadZ = [double]::Parse($parts[5], $ci)
    $rotRad = [double]::Parse($parts[6], $ci)
    $attStr = if ($parts.Count -ge 11) { $parts[10] } else { "" }

    # Bo qua cac block khong thuoc toa do thuc dia
    if ($x -lt 100000 -or $y -lt 1000000) { continue }

    # Tinh goc xoay (do)
    $rotDeg = [Math]::Round(($rotRad * 180.0 / [Math]::PI), 2)

    # Noi suy cao do Z tu be mat LandXML
    $z = Get-SurfaceZ -x $x -y $y -maxDist 120.0
    if ($null -eq $z) { $z = $cadZ }

    # Phan loai nhom doi tuong
    $category = "KHAC"
    if ($layer -match "TruBienBao|TRU3D" -or $effName -match "TRU3D") {
        $category = "COT_BIEN_BAO_3D"
    } elseif ($layer -match "BienBao|QC41" -or $effName -match "^(P\.|W\.|R\.|I\.|IE\.|S\.|BB)") {
        $category = "BIEN_BAO"
    } elseif ($effName -match "VS9\.3|VSI_MARKING") {
        $category = "VACH_SON_MUI_TEN"
    }

    # Boc tach ma hieu thuoc tinh bien bao
    $signCode = ""
    if ($attStr -match "CODE=([^;]+)") {
        $signCode = $matches[1]
    } elseif ($effName -match "^(P\.[0-9A-Za-z\-]+|W\.[0-9A-Za-z\-]+|R\.[0-9A-Za-z\-]+|I\.[0-9A-Za-z\-]+|IE\.[0-9A-Za-z\-]+|S\.[0-9A-Za-z\-]+)") {
        $signCode = $matches[1]
    } else {
        $signCode = $effName
    }

    $signRecords += [PSCustomObject]@{
        Id = $signId++
        Category = $category
        EffectiveName = $effName
        BlockName = $bName
        SignCode = $signCode
        Layer = $layer
        X = [Math]::Round($x, 4)
        Y = [Math]::Round($y, 4)
        Z_Elev = $z
        RotationRad = [Math]::Round($rotRad, 6)
        RotationDeg = $rotDeg
        Attributes = $attStr
    }
}

$signCsvPath = Join-Path $OutputDir "atgt_bien_bao_3d.csv"
$signRecords | Export-Csv -Path $signCsvPath -NoTypeInformation -Encoding UTF8
Write-Host "-> Da xuat $($signRecords.Count) doi tuong Bien bao / Cot 3D ra file: [atgt_bien_bao_3d.csv]" -ForegroundColor Green

# Thong ke phan loai bien bao
Write-Host "   Phan loai nhom bien bao:"
$signRecords | Group-Object Category | Select-Object Name, Count | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host ">>> BUOC 4: XU LY DAI PHAN CACH (DPC L=5M) SANG 3D <<<" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$dpcPolys = @()
$tsPolys = @()
$hrPolys = @()
$vachSonPolys = @()

foreach ($pStr in $rawPolylines) {
    $parts = $pStr.Split("`t")
    if ($parts.Count -lt 4) { continue }
    $handle = $parts[0]
    $layer = $parts[1]
    $closed = $parts[2]
    $vStr = $parts[3]

    if ($layer -eq "0_Ranh giua") {
        $dpcPolys += [PSCustomObject]@{ Handle=$handle; Vertices=$vStr; Layer=$layer }
    } elseif ($layer -eq "TS") {
        $tsPolys += [PSCustomObject]@{ Handle=$handle; Vertices=$vStr; Layer=$layer }
    } elseif ($layer -eq "HR") {
        $hrPolys += [PSCustomObject]@{ Handle=$handle; Vertices=$vStr; Layer=$layer }
    } elseif ($layer -like "VSI_MARKING*") {
        $vachSonPolys += [PSCustomObject]@{ Handle=$handle; Vertices=$vStr; Layer=$layer }
    }
}

Write-Host "-> Tim thay Polyline: DPC: $($dpcPolys.Count), Ton song: $($tsPolys.Count), Hang rao: $($hrPolys.Count), Vach son: $($vachSonPolys.Count)"

# Ham chia deu polyline thanh cac doan L co dinh (kem bo loc chong trung lap & dao khep kin)
function Discretize-Polyline ([string]$vertString, [double]$stepM = 5.0, [double]$maxIslandWidthM = 4.5) {
    $vList = $vertString.Split(";", [StringSplitOptions]::RemoveEmptyEntries)
    $pts = @()
    $localCi = [System.Globalization.CultureInfo]::InvariantCulture
    foreach ($v in $vList) {
        $coords = $v.Split(",")
        if ($coords.Count -ge 2) {
            $pts += [PSCustomObject]@{
                X = [double]::Parse($coords[0], $localCi)
                Y = [double]::Parse($coords[1], $localCi)
            }
        }
    }
    if ($pts.Count -lt 2) { return @() }

    # Tu dong unloop neu polyline la vong khep kin bao quanh dao dai phan cach
    $pStart = $pts[0]
    $pEnd = $pts[$pts.Count - 1]
    $startEndDist = [Math]::Sqrt([Math]::Pow($pEnd.X - $pStart.X, 2) + [Math]::Pow($pEnd.Y - $pStart.Y, 2))
    if ($startEndDist -lt $maxIslandWidthM -and $pts.Count -ge 4) {
        $totalD = 0.0
        for ($k = 0; $k -lt ($pts.Count - 1); $k++) {
            $totalD += [Math]::Sqrt([Math]::Pow($pts[$k+1].X - $pts[$k].X, 2) + [Math]::Pow($pts[$k+1].Y - $pts[$k].Y, 2))
        }
        $halfD = $totalD / 2.0
        $cum = 0.0
        $midIdx = [int]($pts.Count / 2)
        for ($k = 0; $k -lt ($pts.Count - 1); $k++) {
            $segD = [Math]::Sqrt([Math]::Pow($pts[$k+1].X - $pts[$k].X, 2) + [Math]::Pow($pts[$k+1].Y - $pts[$k].Y, 2))
            $cum += $segD
            if ($cum -ge $halfD) {
                $midIdx = $k
                break
            }
        }
        $pts = $pts[0..$midIdx]
    }
    if ($pts.Count -lt 2) { return @() }

    $segments = @()
    $minDist = $stepM * 0.85

    for ($i = 0; $i -lt ($pts.Count - 1); $i++) {
        $p1 = $pts[$i]
        $p2 = $pts[$i+1]
        $dx = $p2.X - $p1.X
        $dy = $p2.Y - $p1.Y
        $len = [Math]::Sqrt($dx*$dx + $dy*$dy)
        if ($len -lt 0.001) { continue }

        $angleRad = [Math]::Atan2($dy, $dx)
        $angleDeg = [Math]::Round(($angleRad * 180.0 / [Math]::PI), 2)

        # Rai tung buoc stepM tren doan p1->p2
        $curD = 0.0
        while ($curD -lt $len) {
            $remLen = $len - $curD
            if ($remLen -lt ($stepM * 0.85)) { break }

            $t = ($curD + [Math]::Min($stepM / 2.0, $remLen / 2.0)) / $len
            $mx = $p1.X + ($dx * $t)
            $my = $p1.Y + ($dy * $t)

            # Loc chong trung lap toa do tam giua cac dot
            $isClash = $false
            foreach ($s in $segments) {
                $dist = [Math]::Sqrt([Math]::Pow($mx - $s.X, 2) + [Math]::Pow($my - $s.Y, 2))
                if ($dist -lt $minDist) {
                    $isClash = $true
                    break
                }
            }

            if (-not $isClash) {
                $segments += [PSCustomObject]@{
                    X = [Math]::Round($mx, 4)
                    Y = [Math]::Round($my, 4)
                    Length = [Math]::Round([Math]::Min($stepM, $remLen), 3)
                    RotationRad = [Math]::Round($angleRad, 6)
                    RotationDeg = $angleDeg
                }
            }
            $curD += $stepM
        }
    }
    return $segments
}

# 4.1 Xu ly DPC L=5M
$dpcRecords = @()
$dpcId = 1
foreach ($p in $dpcPolys) {
    $segs = Discretize-Polyline -vertString $p.Vertices -stepM 5.0
    foreach ($s in $segs) {
        $z = Get-SurfaceZ -x $s.X -y $s.Y -maxDist 100.0
        $dpcRecords += [PSCustomObject]@{
            Id = $dpcId++
            PolyHandle = $p.Handle
            FamilyName = "DPC_L=5M"
            X = $s.X
            Y = $s.Y
            Z_Elev = $z
            RotationRad = $s.RotationRad
            RotationDeg = $s.RotationDeg
            Length = $s.Length
        }
    }
}
$dpcCsvPath = Join-Path $OutputDir "atgt_dai_phan_cach_5m_3d.csv"
$dpcRecords | Export-Csv -Path $dpcCsvPath -NoTypeInformation -Encoding UTF8
Write-Host "-> Da xuat $($dpcRecords.Count) dot dai phan cach 5m ra: [atgt_dai_phan_cach_5m_3d.csv]" -ForegroundColor Green

# 4.2 Xu ly Ton song (Buoc coc 4m)
$tsRecords = @()
$tsId = 1
foreach ($p in $tsPolys) {
    $segs = Discretize-Polyline -vertString $p.Vertices -stepM 4.0
    foreach ($s in $segs) {
        $z = Get-SurfaceZ -x $s.X -y $s.Y -maxDist 100.0
        $tsRecords += [PSCustomObject]@{
            Id = $tsId++
            PolyHandle = $p.Handle
            FamilyName = "TS-ZZ-GUA"
            X = $s.X
            Y = $s.Y
            Z_Elev = $z
            RotationRad = $s.RotationRad
            RotationDeg = $s.RotationDeg
            SpanLength = $s.Length
        }
    }
}
$tsCsvPath = Join-Path $OutputDir "atgt_ton_song_3d.csv"
$tsRecords | Export-Csv -Path $tsCsvPath -NoTypeInformation -Encoding UTF8
Write-Host "-> Da xuat $($tsRecords.Count) dot ton song ra: [atgt_ton_song_3d.csv]" -ForegroundColor Green

# 4.3 Xu ly Hang rao (Buoc coc 2.5m)
$hrRecords = @()
$hrId = 1
foreach ($p in $hrPolys) {
    $segs = Discretize-Polyline -vertString $p.Vertices -stepM 2.5
    foreach ($s in $segs) {
        $z = Get-SurfaceZ -x $s.X -y $s.Y -maxDist 150.0
        $hrRecords += [PSCustomObject]@{
            Id = $hrId++
            PolyHandle = $p.Handle
            FamilyName = "HANG_RAO"
            X = $s.X
            Y = $s.Y
            Z_Elev = $z
            RotationRad = $s.RotationRad
            RotationDeg = $s.RotationDeg
            SpanLength = $s.Length
        }
    }
}
$hrCsvPath = Join-Path $OutputDir "atgt_hang_rao_3d.csv"
$hrRecords | Export-Csv -Path $hrCsvPath -NoTypeInformation -Encoding UTF8
Write-Host "-> Da xuat $($hrRecords.Count) vi tri coc hang rao ra: [atgt_hang_rao_3d.csv]" -ForegroundColor Green

# 4.4 Xu ly Vach son (Toan bo cac dinh 3D Polyline)
$vsRecords = @()
$vsId = 1
foreach ($p in $vachSonPolys) {
    $vList = $p.Vertices.Split(";", [StringSplitOptions]::RemoveEmptyEntries)
    $vIdx = 0
    foreach ($v in $vList) {
        $coords = $v.Split(",")
        if ($coords.Count -ge 2) {
            $vx = [double]::Parse($coords[0], $ci)
            $vy = [double]::Parse($coords[1], $ci)
            $vz = Get-SurfaceZ -x $vx -y $vy -maxDist 100.0
            $vsRecords += [PSCustomObject]@{
                Id = $vsId++
                PolyHandle = $p.Handle
                Layer = $p.Layer
                VertexIndex = $vIdx++
                X = [Math]::Round($vx, 4)
                Y = [Math]::Round($vy, 4)
                Z_Elev = $vz
            }
        }
    }
}
$vsCsvPath = Join-Path $OutputDir "atgt_vach_son_3d.csv"
$vsRecords | Export-Csv -Path $vsCsvPath -NoTypeInformation -Encoding UTF8
Write-Host "-> Da xuat $($vsRecords.Count) dinh vach son 3D ra: [atgt_vach_son_3d.csv]" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host ">>> TONG HOP KET QUA XUAT DU LIEU ATGT 3D HOAN TAT <<<" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "1. Bien bao va Cot 3D:       $($signRecords.Count) doi tuong"
Write-Host "2. Dai phan cach L=5m:       $($dpcRecords.Count) dot"
Write-Host "3. Ton song ho lan L=4m:     $($tsRecords.Count) dot"
Write-Host "4. Hang rao L=2.5m:          $($hrRecords.Count) coc"
Write-Host "5. Dinh vach son 3D:         $($vsRecords.Count) diem"
Write-Host "Toan bo file luu tai thu muc: $OutputDir" -ForegroundColor Yellow

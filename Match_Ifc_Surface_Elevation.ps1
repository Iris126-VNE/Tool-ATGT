param(
    [string]$IfcPath = ".\Data\Input\Top tuyến chính.ifc",
    [string]$ElementsJsonPath = "",
    [double]$EastWestOffset = 546494.089011,
    [double]$NorthSouthOffset = 1247657.403996,
    [string]$OutputJsonPath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -TypeDefinition (Get-Content "$PSScriptRoot\TinSurface.cs" -Raw) -ReferencedAssemblies "System.Xml"

Write-Host "Loading IFC TIN surface: $IfcPath ..."
$tin = [TinSurface]::LoadFromIfc($IfcPath)
Write-Host ("Loaded '{0}': {1} points, {2} triangles" -f $tin.Name, $tin.Points.Count, $tin.Triangles.Count)

if ($ElementsJsonPath -and (Test-Path $ElementsJsonPath)) {
    $items = Get-Content $ElementsJsonPath -Raw | ConvertFrom-Json
    $changes = @()
    foreach ($it in $items) {
        $sx = [double]$it.LocationPoint.XMeter + $EastWestOffset
        $sy = [double]$it.LocationPoint.YMeter + $NorthSouthOffset
        $z = $tin.GetElevation($sx, $sy)
        if ($null -ne $z) {
            $changes += [PSCustomObject]@{
                element_id     = $it.ElementId
                parameter_name = "Elevation from Level"
                new_value      = ("{0:F4} m" -f $z)
                family_name    = $it.FamilyName
                x_survey       = [math]::Round($sx, 3)
                y_survey       = [math]::Round($sy, 3)
                old_z          = [math]::Round([double]$it.LocationPoint.ZMeter, 4)
                new_z          = [math]::Round([double]$z, 4)
            }
        }
    }
    Write-Host ("Matched {0} / {1} elements on surface '{2}'" -f $changes.Count, $items.Count, $tin.Name)
    if ($OutputJsonPath) {
        $changes | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputJsonPath -Encoding UTF8
        Write-Host "Saved parameter changes to: $OutputJsonPath"
    }
}

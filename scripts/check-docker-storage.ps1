$ErrorActionPreference = "Stop"

$driver = & docker info --format '{{.Driver}}'
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read the Docker storage driver."
}

$driverStatus = & docker info --format '{{.DriverStatus}}'
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read Docker driver status."
}

Write-Output "Docker storage driver: $driver"
Write-Output "Docker driver status: $driverStatus"

if ($driver.Trim() -eq "overlayfs") {
    Write-Warning "overlayfs indicates the containerd image store is active. cAdvisor v0.49.2 cannot read container layers with this store. The configured cAdvisor v0.60.6 adds containerd snapshotter support. Confirm named container metrics before relying on resource panels or alerts."
}

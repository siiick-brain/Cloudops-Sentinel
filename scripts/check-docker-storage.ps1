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
    Write-Warning "The containerd image store is active. cAdvisor v0.49.2 cannot read container layer IDs with this store. Container resource metrics can be empty."
}

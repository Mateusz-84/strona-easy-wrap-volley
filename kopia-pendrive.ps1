# =====================================================================
#  KOPIA STRONY NA PENDRIVE
#  Kopiuje caly folder strony (razem z historia zmian .git) na pendrive
#  oznaczony plikiem ".kopia-volleykobylka" w glownym katalogu.
#  Uruchamia sie samo po wlozeniu pendrive'a (zadanie w Harmonogramie zadan).
#
#  Na pendrivie powstaje:
#    Kopia strony volleykobylka\aktualna\         - zawsze najnowsza kopia
#    Kopia strony volleykobylka\archiwum\*.zip    - 1 kopia dziennie, 14 ostatnich
#    Kopia strony volleykobylka\ostatnia-kopia.txt
# =====================================================================
param([switch]$Ustaw, [string]$Dysk = '')

$ErrorActionPreference = 'Stop'
$Zrodlo  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Znacznik = '.kopia-volleykobylka'
$Folder  = 'Kopia strony volleykobylka'

function Pendrivy {
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=2' | Where-Object { $_.FreeSpace -ne $null }
}

if ($Ustaw) {
    $p = @(Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -ne $env:SystemDrive -and $_.DriveType -in 2,3 })
    if ($Dysk) { $p = @($p | Where-Object { $_.DeviceID -eq $Dysk.TrimEnd('\') }) } else { $p = @(Pendrivy) }
    if ($p.Count -eq 0) { Write-Host 'Nie widze zadnego pendrive. Wloz go i uruchom ponownie.'; exit 1 }
    foreach ($d in $p) {
        $plik = Join-Path ($d.DeviceID + '\') $Znacznik
        if (-not (Test-Path $plik)) {
            "Ten pendrive dostaje automatyczna kopie strony volleykobylka.pl. Nie usuwaj tego pliku." | Set-Content -Path $plik -Encoding UTF8
            (Get-Item $plik -Force).Attributes = 'Hidden'
        }
        Write-Host ("Oznaczono pendrive " + $d.DeviceID + " (" + $d.VolumeName + ")")
    }
    $vbs = Join-Path $Zrodlo 'kopia-pendrive-ukryta.vbs'
    $uzytkownik = "$env:USERDOMAIN\$env:USERNAME"
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Kopia strony volleykobylka.pl na pendrive po jego wlozeniu</Description></RegistrationInfo>
  <Triggers>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-Partition/Diagnostic"&gt;&lt;Select Path="Microsoft-Windows-Partition/Diagnostic"&gt;*[System[(EventID=1006)]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
      <Delay>PT15S</Delay>
    </EventTrigger>
    <LogonTrigger><Enabled>true</Enabled><UserId>$uzytkownik</UserId><Delay>PT2M</Delay></LogonTrigger>
    <TimeTrigger>
      <Repetition><Interval>PT1H</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
      <StartBoundary>2026-01-01T00:05:00</StartBoundary><Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals><Principal id="Author"><UserId>$uzytkownik</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>wscript.exe</Command><Arguments>"$vbs"</Arguments></Exec>
  </Actions>
</Task>
"@
    $tmp = Join-Path $env:TEMP 'kopia-volleykobylka.xml'
    $xml | Set-Content -Path $tmp -Encoding Unicode
    schtasks /Create /TN 'Kopia strony volleykobylka na pendrive' /XML $tmp /F | Out-Host
    if ($LASTEXITCODE -ne 0) {
        # bez uprawnien do dziennika zdarzen: sprawdzanie co 5 minut (gdy pendrive'a nie ma, skrypt od razu konczy)
        Write-Host 'Wariant zapasowy: sprawdzanie co 5 minut.'
        $xml2 = $xml -replace '(?s)<EventTrigger>.*?</EventTrigger>', '' -replace '<Interval>PT1H</Interval>', '<Interval>PT5M</Interval>'
        $xml2 | Set-Content -Path $tmp -Encoding Unicode
        schtasks /Create /TN 'Kopia strony volleykobylka na pendrive' /XML $tmp /F | Out-Host
    }
    Remove-Item $tmp -ErrorAction SilentlyContinue
    Write-Host 'Zadanie ustawione. Robie pierwsza kopie...'
}

# --- kopia -----------------------------------------------------------
if (-not ((Test-Path (Join-Path $Zrodlo 'build.py')) -and (Test-Path (Join-Path $Zrodlo 'content.py')))) {
    Write-Host 'Folder strony wyglada na niekompletny - nie robie kopii (zeby nie nadpisac dobrej kopii pusta).'
    exit 2
}
$cele = @(Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -ne $env:SystemDrive -and $_.DriveType -in 2,3 } | Where-Object { Test-Path (Join-Path ($_.DeviceID + '\') $Znacznik) })
if ($cele.Count -eq 0) { exit 0 }   # brak oznaczonego pendrive'a - nic do zrobienia

foreach ($d in $cele) {
    $baza = Join-Path ($d.DeviceID + '\') $Folder
    $info = Join-Path $baza 'ostatnia-kopia.txt'
    # po wlozeniu Windows zglasza kilka zdarzen - nie kopiuj czesciej niz co 3 minuty
    if ((Test-Path $info) -and ((Get-Date) - (Get-Item $info).LastWriteTime).TotalMinutes -lt 3 -and -not $Ustaw) { continue }
    New-Item -ItemType Directory -Force -Path (Join-Path $baza 'archiwum') | Out-Null
    $akt = Join-Path $baza 'aktualna'
    $log = Join-Path $baza 'robocopy-log.txt'
    robocopy "$Zrodlo" "$akt" /MIR /R:1 /W:1 /XD __pycache__ /XF '*.pyc' /NP /NDL /NFL /LOG:"$log" | Out-Null
    $kod = $LASTEXITCODE
    # jedna kopia archiwalna dziennie (zip), 14 ostatnich
    $zip = Join-Path $baza ("archiwum\strona-" + (Get-Date -Format 'yyyy-MM-dd') + '.zip')
    if (-not (Test-Path $zip) -and $kod -lt 8) {
        try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::CreateFromDirectory($akt, $zip) } catch {}
    }
    Get-ChildItem (Join-Path $baza 'archiwum') -Filter 'strona-*.zip' | Sort-Object Name -Descending | Select-Object -Skip 14 | Remove-Item -Force
    $stan = if ($kod -lt 8) { 'OK' } else { "BLAD (kod robocopy $kod) - zobacz robocopy-log.txt" }
    @(
        "Ostatnia kopia: $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
        "Stan: $stan",
        "Skad: $Zrodlo",
        '',
        'JAK PRZYWROCIC STRONE:',
        '1. Skopiuj folder "aktualna" na komputer (np. do Dokumentow) i zmien nazwe na strona-easy-wrap-volley.',
        '2. Jest tam cala strona razem z historia zmian (.git) - mozna od razu wyslac ja na GitHub',
        '   plikiem "WYSLIJ NA GITHUB.bat" albo zbudowac od nowa (build.py). Gotowa strona jest w podfolderze "strona".',
        '3. Starsze wersje: archiwum\strona-RRRR-MM-DD.zip (jedna na dzien, 14 ostatnich).'
    ) | Set-Content -Path $info -Encoding UTF8
    if ($Ustaw) { Write-Host ("Kopia na " + $d.DeviceID + ": " + $stan) }
}

param(
    [ValidateSet("codex", "claude", "both")]
    [string]$Agent = "both",
    [string]$Repo = "Lengcangr/Buffett",
    [string]$Ref = "main",
    [string[]]$SkillName = @("buffett-investing-coach", "investment-research-pipeline"),
    [string]$CodexSkillsDir,
    [string]$ClaudeSkillsDir,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Get-DefaultSkillsDir {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("codex", "claude")]
        [string]$Target
    )

    if ($Target -eq "codex") {
        if ($env:CODEX_HOME) {
            return Join-Path $env:CODEX_HOME "skills"
        }

        return Join-Path $HOME ".codex\skills"
    }

    return Join-Path $HOME ".claude\skills"
}

function Get-LocalSkillSource {
    param([Parameter(Mandatory = $true)][string]$Name)

    $candidate = Join-Path $PSScriptRoot "skills\$Name"
    $skillFile = Join-Path $candidate "SKILL.md"

    if (Test-Path -LiteralPath $skillFile) {
        return $candidate
    }

    return $null
}

function Get-DownloadedRepo {
    $tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("buffett-skills-" + [System.Guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $tmpRoot "repo.zip"
    $extractRoot = Join-Path $tmpRoot "extract"
    $downloadUrl = "https://github.com/$Repo/archive/refs/heads/$Ref.zip"

    New-Item -ItemType Directory -Path $tmpRoot | Out-Null

    try {
        Invoke-WebRequest -UseBasicParsing $downloadUrl -OutFile $zipPath
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractRoot -Force

        $repoRoot = Get-ChildItem -LiteralPath $extractRoot -Directory | Select-Object -First 1
        if (-not $repoRoot) {
            throw "Could not locate extracted repository root."
        }

        return @{
            Root = $tmpRoot
            RepoRoot = $repoRoot.FullName
        }
    }
    catch {
        if (Test-Path -LiteralPath $tmpRoot) {
            Remove-Item -LiteralPath $tmpRoot -Recurse -Force
        }

        throw
    }
}

function Resolve-SkillSource {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [hashtable]$Downloaded
    )

    $local = Get-LocalSkillSource -Name $Name
    if ($local) {
        return $local
    }

    if (-not $Downloaded) {
        throw "Skill '$Name' is not present locally and no downloaded repository is available."
    }

    $skillPath = Join-Path $Downloaded.RepoRoot "skills\$Name"
    if (-not (Test-Path -LiteralPath (Join-Path $skillPath "SKILL.md"))) {
        throw "Could not locate skills\$Name\SKILL.md in downloaded repository."
    }

    return $skillPath
}

function Install-SkillToTarget {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("codex", "claude")]
        [string]$Target,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$SourcePath,

        [string]$CustomSkillsDir
    )

    $skillsDir = if ($CustomSkillsDir) { $CustomSkillsDir } else { Get-DefaultSkillsDir -Target $Target }
    $destination = Join-Path $skillsDir $Name

    New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null

    if (Test-Path -LiteralPath $destination) {
        if (-not $Force) {
            throw "Destination already exists: $destination . Re-run with -Force to overwrite."
        }

        Remove-Item -LiteralPath $destination -Recurse -Force
    }

    Copy-Item -LiteralPath $SourcePath -Destination $destination -Recurse -Force
    Write-Host "Installed $Name to $destination"
}

$downloaded = $null

try {
    $missingLocal = @()
    foreach ($name in $SkillName) {
        if (-not (Get-LocalSkillSource -Name $name)) {
            $missingLocal += $name
        }
    }

    if ($missingLocal.Count -gt 0) {
        $downloaded = Get-DownloadedRepo
    }

    $targets = switch ($Agent) {
        "codex" { @("codex") }
        "claude" { @("claude") }
        "both" { @("codex", "claude") }
    }

    foreach ($name in $SkillName) {
        $sourcePath = Resolve-SkillSource -Name $name -Downloaded $downloaded

        foreach ($target in $targets) {
            if ($target -eq "codex") {
                Install-SkillToTarget -Target "codex" -Name $name -SourcePath $sourcePath -CustomSkillsDir $CodexSkillsDir
            }
            else {
                Install-SkillToTarget -Target "claude" -Name $name -SourcePath $sourcePath -CustomSkillsDir $ClaudeSkillsDir
            }
        }
    }

    Write-Host ""
    Write-Host "Next step: restart Codex or Claude Code so the new skills are loaded."
}
finally {
    if ($downloaded -and (Test-Path -LiteralPath $downloaded.Root)) {
        Remove-Item -LiteralPath $downloaded.Root -Recurse -Force
    }
}

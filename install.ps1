param(
    [ValidateSet("codex", "claude", "both")]
    [string]$Agent = "both",
    [string]$Repo = "Lengcangr/Buffett",
    [string]$Ref = "main",
    [string]$SkillName = "buffett-investing-coach",
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
    $candidate = Join-Path $PSScriptRoot "skills\$SkillName"
    $skillFile = Join-Path $candidate "SKILL.md"

    if (Test-Path -LiteralPath $skillFile) {
        return $candidate
    }

    return $null
}

function Get-DownloadedSkillSource {
    $tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("buffett-skill-" + [System.Guid]::NewGuid().ToString("N"))
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

        $skillPath = Join-Path $repoRoot.FullName "skills\$SkillName"
        if (-not (Test-Path -LiteralPath (Join-Path $skillPath "SKILL.md"))) {
            throw "Could not locate skills\$SkillName\SKILL.md in downloaded repository."
        }

        return @{
            Root = $tmpRoot
            SkillPath = $skillPath
        }
    }
    catch {
        if (Test-Path -LiteralPath $tmpRoot) {
            Remove-Item -LiteralPath $tmpRoot -Recurse -Force
        }

        throw
    }
}

function Install-SkillToTarget {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("codex", "claude")]
        [string]$Target,

        [Parameter(Mandatory = $true)]
        [string]$SourcePath,

        [string]$CustomSkillsDir
    )

    $skillsDir = if ($CustomSkillsDir) { $CustomSkillsDir } else { Get-DefaultSkillsDir -Target $Target }
    $destination = Join-Path $skillsDir $SkillName

    New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null

    if (Test-Path -LiteralPath $destination) {
        if (-not $Force) {
            throw "Destination already exists: $destination . Re-run with -Force to overwrite."
        }

        Remove-Item -LiteralPath $destination -Recurse -Force
    }

    Copy-Item -LiteralPath $SourcePath -Destination $destination -Recurse -Force
    Write-Host "Installed $SkillName to $destination"
}

$downloaded = $null

try {
    $sourcePath = Get-LocalSkillSource
    if (-not $sourcePath) {
        $downloaded = Get-DownloadedSkillSource
        $sourcePath = $downloaded.SkillPath
    }

    switch ($Agent) {
        "codex" {
            Install-SkillToTarget -Target "codex" -SourcePath $sourcePath -CustomSkillsDir $CodexSkillsDir
        }
        "claude" {
            Install-SkillToTarget -Target "claude" -SourcePath $sourcePath -CustomSkillsDir $ClaudeSkillsDir
        }
        "both" {
            Install-SkillToTarget -Target "codex" -SourcePath $sourcePath -CustomSkillsDir $CodexSkillsDir
            Install-SkillToTarget -Target "claude" -SourcePath $sourcePath -CustomSkillsDir $ClaudeSkillsDir
        }
    }

    Write-Host ""
    Write-Host "Next step: restart Codex or Claude Code so the new skill is loaded."
}
finally {
    if ($downloaded -and (Test-Path -LiteralPath $downloaded.Root)) {
        Remove-Item -LiteralPath $downloaded.Root -Recurse -Force
    }
}

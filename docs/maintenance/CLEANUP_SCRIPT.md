# Cleanup Script - Files Safe to Delete

## ✅ Definitely Safe to Delete

### 1. Build Artifacts (Already in .gitignore)
```powershell
# Delete build artifacts
Remove-Item -Recurse -Force src/upbit_quant_system.egg-info -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force upbit_quant_system.egg-info -ErrorAction SilentlyContinue
```

### 2. Old README Backup
```powershell
# Delete old README backup
Remove-Item README_OLD.md -ErrorAction SilentlyContinue
```

### 3. Deprecated filters.py (Not Used)
**Status**: ✅ Safe to delete - No imports found in src/ or tests/  
**Reason**: Fully replaced by `conditions.py`, backward compatibility handled via aliases

```powershell
# Delete deprecated filters.py
Remove-Item src/strategies/volatility_breakout/filters.py -ErrorAction SilentlyContinue
```

## ⚠️ Review Before Deleting

### 4. pyproject.toml.example
**Status**: Template file - check if referenced in docs  
**Recommendation**: Keep for now (might be useful as template)

### 5. legacy/ Folder
**Status**: Old code, but useful for portfolio (shows migration)  
**Recommendation**: **KEEP** for portfolio - shows evolution of codebase

## 🚀 Complete Cleanup Script

```powershell
# Safe deletions
Write-Host "Cleaning up unnecessary files..."

# Build artifacts
if (Test-Path "src/upbit_quant_system.egg-info") {
    Remove-Item -Recurse -Force src/upbit_quant_system.egg-info
    Write-Host "✓ Deleted src/upbit_quant_system.egg-info"
}

if (Test-Path "upbit_quant_system.egg-info") {
    Remove-Item -Recurse -Force upbit_quant_system.egg-info
    Write-Host "✓ Deleted upbit_quant_system.egg-info"
}

# Old README
if (Test-Path "README_OLD.md") {
    Remove-Item README_OLD.md
    Write-Host "✓ Deleted README_OLD.md"
}

# Deprecated filters.py (not used anywhere)
if (Test-Path "src/strategies/volatility_breakout/filters.py") {
    Remove-Item src/strategies/volatility_breakout/filters.py
    Write-Host "✓ Deleted deprecated filters.py"
}

# Check nested notebooks
if (Test-Path "notebooks/notebooks") {
    Write-Host "⚠ Found nested notebooks/notebooks directory - review before deleting"
    Get-ChildItem notebooks/notebooks -Recurse | Select-Object FullName
}

Write-Host "`nCleanup complete!"
```

## 📊 Summary

**Files to Delete**:
1. ✅ `src/upbit_quant_system.egg-info/` - Build artifact
2. ✅ `upbit_quant_system.egg-info/` - Build artifact  
3. ✅ `README_OLD.md` - Old backup
4. ✅ `src/strategies/volatility_breakout/filters.py` - Deprecated, not used

**Files to Keep**:
- `legacy/` - Useful for portfolio (shows migration)
- `pyproject.toml.example` - Template file (might be useful)

**Estimated Space Saved**: ~2-5 MB

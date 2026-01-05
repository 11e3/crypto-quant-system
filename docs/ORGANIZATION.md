# Documentation Organization

This document describes the organization structure of all markdown files in the repository.

## 📁 Directory Structure

```
docs/
├── portfolio/          # Portfolio publication documentation
│   ├── README.md
│   ├── PORTFOLIO_PUBLICATION_GUIDE.md
│   ├── PUBLICATION_CHECKLIST.md
│   ├── PORTFOLIO_CHECKLIST.md
│   └── PORTFOLIO_PUBLICATION_PLAN.md
│
├── maintenance/        # Maintenance and cleanup documentation
│   ├── README.md
│   ├── CLEANUP_RECOMMENDATIONS.md
│   ├── CLEANUP_SCRIPT.md
│   ├── FILES_TO_DELETE.md
│   └── GITIGNORE_AUDIT.md
│
├── guides/             # User guides
│   ├── getting_started.md
│   ├── configuration.md
│   ├── strategy_customization.md
│   └── deprecation_guide.md
│
├── planning/           # Project planning documents
│   ├── TEST_COVERAGE_PLAN.md
│   ├── COVERAGE_PROGRESS.md
│   ├── COVERAGE_90_PERCENT_PLAN.md
│   ├── CONFIGURATION_STANDARD.md
│   └── comparison_legacy_vs_new_bot.md
│
├── refactoring/        # Refactoring documentation
│   ├── REFACTORING_SUMMARY.md
│   ├── MODERN_PYTHON_STANDARDS_MIGRATION.md
│   └── STANDARDS_COMPLIANCE_REPORT.md
│
├── archive/            # Historical/archived documents
│   └── [21 phase completion documents]
│
├── api/                # API documentation
│   └── README.md
│
├── architecture.md     # System architecture
└── README.md           # Documentation index
```

## 📄 Root-Level Files

Essential documentation files that remain in the root:

- `README.md` - Main project README
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy

## 🎯 Quick Reference

### For Users
- **Getting Started**: `docs/guides/getting_started.md`
- **Configuration**: `docs/guides/configuration.md`
- **Strategy Customization**: `docs/guides/strategy_customization.md`
- **Architecture**: `docs/architecture.md`

### For Portfolio Publication
- **Main Guide**: `docs/portfolio/PORTFOLIO_PUBLICATION_GUIDE.md`
- **Quick Checklist**: `docs/portfolio/PUBLICATION_CHECKLIST.md`

### For Maintenance
- **Cleanup Guide**: `docs/maintenance/CLEANUP_RECOMMENDATIONS.md`
- **Files to Delete**: `docs/maintenance/FILES_TO_DELETE.md`

## 📝 Organization Principles

1. **Root Level**: Only essential files (README, CONTRIBUTING, SECURITY)
2. **docs/portfolio/**: All portfolio publication related documents
3. **docs/maintenance/**: Cleanup, audit, and maintenance guides
4. **docs/guides/**: User-facing guides and tutorials
5. **docs/planning/**: Project planning and tracking documents
6. **docs/archive/**: Historical/archived documents
7. **docs/refactoring/**: Refactoring documentation

## 🔄 Migration Summary

**Moved to `docs/portfolio/`:**
- `PORTFOLIO_PUBLICATION_GUIDE.md`
- `PUBLICATION_CHECKLIST.md`
- `docs/planning/PORTFOLIO_CHECKLIST.md`
- `docs/planning/PORTFOLIO_PUBLICATION_PLAN.md`

**Moved to `docs/maintenance/`:**
- `CLEANUP_RECOMMENDATIONS.md`
- `CLEANUP_SCRIPT.md`
- `FILES_TO_DELETE.md`
- `GITIGNORE_AUDIT.md`

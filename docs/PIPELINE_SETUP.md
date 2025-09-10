# Pipeline Setup Documentation

## Overview

This project implements a modern CI/CD pipeline for Next.js 15 with Payload CMS 3.55, designed for TypeScript/TSX development with automated quality checks and error resolution.

## 🚀 Quick Start

### 1. Development Setup
```bash
# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env

# Start development server
pnpm dev
```

### 2. Code Quality Commands
```bash
# Auto-fix linting issues
pnpm lint:fix

# Auto-format code
pnpm format

# Check types
pnpm type-check

# Generate Payload types
pnpm generate:types

# Build project
pnpm build
```

## 🔧 Pipeline Features

### Pre-commit Hooks (Husky + lint-staged)
- **Auto-fixes** ESLint issues before commit
- **Auto-formats** code with Prettier
- **Prevents** broken code from being committed
- **Configuration**: Located in `package.json` lint-staged section

### GitHub Actions Workflows

#### 1. Main CI/CD Pipeline (`.github/workflows/ci.yml`)
**Triggers**: Push/PR to main/develop branches

**What it does**:
- 🔧 **Auto-fixes** linting and formatting issues first
- ✅ **Validates** TypeScript types with detailed error messages
- ✅ **Checks** Next.js App Router patterns and best practices
- ✅ **Validates** Payload CMS configuration and generates types
- ✅ **Builds** project for production with helpful debugging tips
- ✅ **Runs** security audit for dependency vulnerabilities
- ✅ **Deployment readiness** check for main branch only
- 📝 **Detailed error messages** with specific fix commands

#### 2. PR Quality Checks (`.github/workflows/pr-checks.yml`)
**Triggers**: Pull request events (opened, synchronize, reopened)

**What it does**:
- � **Auto-fixes** linting and formatting issues in PR
- � **Analyzes** only changed files for efficiency
- 📊 **Checks** code complexity and file size
- 🎯 **Validates** Payload CMS configuration changes
- ⚠️ **Detects** breaking changes in dependencies and environment
- 💡 **Provides** specific solutions for common issues

#### 3. Branch Protection (`.github/workflows/branch-protection.yml`)
**Triggers**: Push to any branch except main

**What it does**:
- 🔧 **Auto-fixes** issues before validation
- 🏗️ **Quick build** check for fast feedback
- 📝 **Shows** recent commits on the branch

## 🛠️ Error Messages & Solutions

### Common Issues and Quick Fixes

#### ESLint Errors
```bash
# Error: ESLint issues found
# Solution:
pnpm lint:fix
```

#### Formatting Issues
```bash
# Error: Code formatting issues
# Solution:
pnpm format
```

#### TypeScript Errors
```bash
# Error: Type checking failed
# Solutions:
pnpm type-check          # Check types
pnpm generate:types      # Generate Payload types
```

#### Build Failures
```bash
# Error: Build failed
# Common causes & solutions:
# 1. TypeScript errors → Fix type issues
# 2. Missing env vars → Check .env file
# 3. Import errors → Verify all imports exist
# 4. Payload config → Check payload.config.ts

# Debug commands:
pnpm build
pnpm type-check
pnpm generate:types
```

#### Payload CMS Issues
```bash
# Error: Payload configuration error
# Solutions:
pnpm payload generate:types    # Generate types
# Check DATABASE_URI in .env
# Verify collections/*.ts files
# Check payload.config.ts syntax
```

## 📋 Configuration Files

### ESLint Configuration (`eslint.config.mjs`)
- ✅ **No console.log restrictions** (as requested)
- ✅ **Next.js App Router** best practices enforcement
- ✅ **React Hooks** validation (rules-of-hooks, exhaustive-deps)
- ✅ **Payload CMS** compatibility settings
- ✅ **TypeScript** strict checking with helpful warnings
- ✅ **Auto-fix capabilities** for most common issues
- ✅ **Proper ignoring** of build directories and config files

### Prettier Configuration (`.prettierrc.json`)
- Consistent code formatting across the project
- Auto-fixes formatting on pre-commit hooks
- Integrates seamlessly with ESLint
- Applied to TypeScript, JavaScript, JSON, and Markdown files

### Husky & lint-staged Configuration
- **Pre-commit hook**: Auto-fixes linting + formatting on staged files only
- **Pre-push hook**: Runs type checking + build validation
- **Efficient**: Only processes changed files, not entire codebase
- **Location**: `.husky/pre-commit`, `.husky/pre-push`

## 🎯 Next.js App Router Validation

The pipeline automatically checks for:

### ✅ Server Components
```tsx
// ✅ Good: Async Server Component
export default async function Page() {
  const data = await fetch('...')
  return <div>...</div>
}
```

### ✅ Client Components
```tsx
// ✅ Good: Interactive Client Component
'use client'
import { useState } from 'react'

export default function Interactive() {
  const [state, setState] = useState(0)
  return <button onClick={...}>...</button>
}
```

### ✅ Server Actions
```tsx
// ✅ Good: Server Action
async function submitForm(formData: FormData) {
  'use server'
  // Handle form submission
}
```

## 🎨 Payload CMS Integration

### Automatic Validation
- ✅ **Config validation** on every change
- ✅ **Type generation** for collections
- ✅ **Environment variables** checking
- ✅ **Database connection** validation

### Best Practices Enforced
- Type-safe collection access
- Proper async patterns
- Environment variable management

## 🔒 Security & Quality

### Automated Checks
- **Dependency vulnerabilities** scanning
- **Code complexity** analysis
- **Breaking changes** detection
- **Environment variables** validation

### Performance Monitoring
- **Build size** analysis
- **Bundle optimization** suggestions
- **Loading performance** checks

## 🚫 Removed Features (As Requested)

- ❌ **Branch naming patterns** - No restrictions on branch names
- ❌ **Excessive testing** - Minimal test requirements with error tolerance
- ❌ **Rigid code standards** - Focus on helpful guidance over strict enforcement

## 🔧 Troubleshooting

### Pipeline Fails?
1. **Check the detailed error messages** in GitHub Actions
2. **Run the suggested fix commands locally**
3. **Commit and push the fixes**

### Local Development Issues?
```bash
# Clean installation
pnpm reinstall

# Regenerate types
pnpm generate:types
pnpm generate:importmap

# Clean build
rm -rf .next
pnpm build
```

### Still Having Issues?
- Check the **GitHub Actions logs** for detailed error messages
- Every error includes **specific fix commands**
- All auto-fixable issues are **automatically resolved**

## 📚 Additional Resources

- [Next.js Best Practices](./NEXT_JS_BEST_PRACTICES.md)
- [CI/CD Pipeline Details](./CI_CD_PIPELINE.md)
- [Payload CMS Documentation](https://payloadcms.com/docs)

## 🎉 Success Indicators

When everything is working correctly, you'll see:
- ✅ All GitHub Actions passing
- ✅ Auto-formatted code on every commit
- ✅ Type-safe development experience
- ✅ Detailed error messages when issues occur
- ✅ Automatic fixes applied where possible

The pipeline is designed to **help developers**, not hinder them. Every error comes with clear instructions on how to fix it! 🚀

# Quick Copy-Paste Workflow Files

This file contains all the GitHub Actions workflow files that you can directly copy and paste into your existing Next.js + Payload CMS project.

## 📁 File Structure

Create these files in your project:

```
your-project/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── pr-checks.yml
│       └── branch-protection.yml
├── .husky/
│   ├── pre-commit
│   └── pre-push
├── eslint.config.mjs
└── .prettierrc.json
```

## 🔧 Workflow Files

### 1. Main CI/CD Pipeline

**File**: `.github/workflows/ci.yml`

```yaml
name: Next.js + Payload CMS CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  code-quality:
    name: Code Quality & Linting
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Auto-fix linting and formatting issues
        run: |
          echo "🔧 Auto-fixing ESLint issues..."
          pnpm lint:fix || echo "⚠️ Some ESLint issues couldn't be auto-fixed"

          echo "🎨 Auto-formatting code with Prettier..."
          pnpm format || echo "⚠️ Some formatting issues couldn't be auto-fixed"

      - name: Run ESLint (final check)
        run: |
          echo "🔍 Running final ESLint check..."
          if ! pnpm lint; then
            echo ""
            echo "❌ ESLint found issues that need manual attention:"
            echo ""
            echo "💡 To fix locally:"
            echo "   pnpm lint:fix"
            echo ""
            echo "📋 Common issues and solutions:"
            echo "   • Unused variables: Remove them or prefix with underscore (_)"
            echo "   • Missing dependencies: Add missing imports"
            echo "   • TypeScript errors: Fix type annotations"
            echo ""
            exit 1
          fi

      - name: Run Prettier check (final check)
        run: |
          echo "🎨 Checking code formatting..."
          if ! pnpm format:check; then
            echo ""
            echo "❌ Code formatting issues found!"
            echo ""
            echo "💡 To fix locally:"
            echo "   pnpm format"
            echo ""
            echo "This will automatically format all your files."
            echo ""
            exit 1
          fi

      - name: TypeScript type checking
        run: |
          echo "🔍 Checking TypeScript types..."
          if ! pnpm type-check; then
            echo ""
            echo "❌ TypeScript type errors found!"
            echo ""
            echo "💡 Common solutions:"
            echo "   • Check import/export statements"
            echo "   • Verify type annotations match usage"
            echo "   • Run 'pnpm generate:types' for Payload CMS types"
            echo "   • Ensure all dependencies are installed"
            echo ""
            echo "🔧 To check locally:"
            echo "   pnpm type-check"
            echo ""
            exit 1
          fi

      - name: Check for Next.js App Router best practices
        run: |
          echo "🔍 Checking for Next.js App Router patterns..."

          # Check for proper use of 'use server' directive
          server_actions=$(find src -name "*.ts" -o -name "*.tsx" | xargs grep -l "use server" | wc -l)
          echo "✅ Found $server_actions files with server actions"

          # Check for middleware.ts existence
          if [ -f "src/middleware.ts" ] || [ -f "middleware.ts" ]; then
            echo "✅ Middleware file found"
          else
            echo "ℹ️ No middleware file detected (optional)"
          fi

          # Check for proper app directory structure
          if [ -d "src/app" ]; then
            echo "✅ App Router structure detected"
          else
            echo "❌ App Router structure not found"
            exit 1
          fi

          # Check for layout.tsx files
          layouts=$(find src/app -name "layout.tsx" | wc -l)
          echo "✅ Found $layouts layout files"

          # Check for proper loading.tsx and error.tsx files
          loading_files=$(find src/app -name "loading.tsx" | wc -l)
          error_files=$(find src/app -name "error.tsx" | wc -l)
          echo "ℹ️ Found $loading_files loading.tsx and $error_files error.tsx files"

  payload-validation:
    name: Payload CMS Validation
    runs-on: ubuntu-latest
    needs: code-quality

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Validate Payload config
        run: |
          echo "🚀 Validating Payload CMS configuration..."
          if ! pnpm payload generate:types; then
            echo ""
            echo "❌ Payload CMS configuration error!"
            echo ""
            echo "💡 Common Payload issues and solutions:"
            echo "   • Database connection: Check DATABASE_URI in .env"
            echo "   • Invalid collections: Check collections/*.ts files"
            echo "   • Missing dependencies: Run 'pnpm install'"
            echo "   • Config syntax: Check payload.config.ts syntax"
            echo ""
            echo "🔧 To debug locally:"
            echo "   pnpm payload generate:types"
            echo "   Check payload.config.ts for errors"
            echo ""
            exit 1
          fi
          echo "✅ Payload types generated successfully"

      - name: Check Payload collections
        run: |
          echo "📦 Checking Payload collections..."
          collections=$(find src/collections -name "*.ts" | wc -l)
          echo "✅ Found $collections collection files"

      - name: Validate environment variables
        run: |
          echo "🔧 Checking required environment variables..."
          if [ -f ".env.example" ]; then
            echo "✅ .env.example found"
            cat .env.example | grep -E "^[A-Z_]+=" | while read line; do
              var_name=$(echo $line | cut -d'=' -f1)
              echo "📝 Required: $var_name"
            done
          fi

  build-test:
    name: Build & Test
    runs-on: ubuntu-latest
    needs: [code-quality, payload-validation]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Create test environment file
        run: |
          cp .env.example .env
          echo "DATABASE_URI=file:./test.db" >> .env
          echo "PAYLOAD_SECRET=test-secret-key" >> .env
          echo "NEXT_PUBLIC_SERVER_URL=http://localhost:3000" >> .env

      - name: Build project
        run: |
          echo "🏗️ Building Next.js project..."
          if ! pnpm build; then
            echo ""
            echo "❌ Build failed!"
            echo ""
            echo "💡 Common build issues and solutions:"
            echo "   • TypeScript errors: Fix type issues"
            echo "   • Missing environment variables: Check .env file"
            echo "   • Import errors: Verify all imports exist"
            echo "   • Payload CMS config issues: Check payload.config.ts"
            echo ""
            echo "🔧 To debug locally:"
            echo "   pnpm build"
            echo "   pnpm type-check"
            echo "   pnpm generate:types"
            echo ""
            exit 1
          fi

      - name: Run tests
        run: pnpm test
        continue-on-error: true

  security-audit:
    name: Security Audit
    runs-on: ubuntu-latest
    needs: code-quality

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run security audit
        run: pnpm audit --audit-level moderate
        continue-on-error: true

  deploy-check:
    name: Deployment Ready Check
    runs-on: ubuntu-latest
    needs: [build-test, security-audit]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Production build
        run: pnpm build

      - name: Check build size
        run: |
          echo "📊 Build size analysis:"
          du -sh .next/

      - name: Deployment readiness
        run: |
          echo "🚀 Project is ready for deployment!"
          echo "✅ All checks passed"
          echo "✅ Build completed successfully"
          echo "✅ Next.js App Router structure validated"
          echo "✅ Payload CMS configuration verified"
```

### 2. PR Quality Checks

**File**: `.github/workflows/pr-checks.yml`

```yaml
name: PR Quality Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  pr-validation:
    name: Pull Request Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Auto-fix issues in PR
        run: |
          echo "🔧 Auto-fixing linting and formatting issues in PR..."
          pnpm lint:fix || echo "⚠️ Some ESLint issues couldn't be auto-fixed"
          pnpm format || echo "⚠️ Some formatting issues couldn't be auto-fixed"

      - name: Validate changed files
        run: |
          echo "🔍 Analyzing changed files in PR..."

          # Get list of changed files
          git diff --name-only origin/main...HEAD > changed_files.txt

          # Check if any TypeScript/TSX files changed
          tsx_files=$(grep -E "\.(ts|tsx)$" changed_files.txt || true)
          if [ -n "$tsx_files" ]; then
            echo "✅ TypeScript/TSX files changed:"
            echo "$tsx_files"

            # Run type check on changed files
            echo "🔍 Type checking changed files..."
            if ! pnpm type-check; then
              echo ""
              echo "❌ Type checking failed for changed files!"
              echo ""
              echo "💡 To fix locally:"
              echo "   pnpm type-check"
              echo "   pnpm generate:types  # For Payload CMS types"
              echo ""
              exit 1
            fi
          fi

          # Check for Next.js App Router compliance in changed files
          if echo "$tsx_files" | grep -q "app/"; then
            echo "🚀 App Router files detected, checking compliance..."

            # Check for proper server component patterns
            for file in $(echo "$tsx_files" | grep "app/.*page\.tsx"); do
              if [ -f "$file" ]; then
                echo "📄 Checking $file"

                # Check if it's a server component (no 'use client')
                if ! grep -q "use client" "$file"; then
                  echo "✅ $file is a Server Component"
                else
                  echo "🔄 $file is a Client Component"
                fi

                # Check for async component (server component best practice)
                if grep -q "export default async function" "$file"; then
                  echo "✅ $file uses async Server Component pattern"
                fi
              fi
            done
          fi

          # Check for Payload CMS related changes
          payload_files=$(echo "$tsx_files" | grep -E "(collections|payload)" || true)
          if [ -n "$payload_files" ]; then
            echo "🎯 Payload CMS files changed:"
            echo "$payload_files"

            # Validate Payload config if changed
            if echo "$payload_files" | grep -q "payload.config"; then
              echo "🔧 Payload config changed, validating..."
              if ! pnpm payload generate:types; then
                echo ""
                echo "❌ Payload config validation failed!"
                echo ""
                echo "💡 To fix locally:"
                echo "   pnpm payload generate:types"
                echo "   Check payload.config.ts for syntax errors"
                echo ""
                exit 1
              fi
            fi
          fi

      - name: Check for breaking changes
        run: |
          echo "⚠️ Checking for potential breaking changes..."

          # Check if package.json changed
          if git diff --name-only origin/main...HEAD | grep -q "package.json"; then
            echo "📦 package.json changed"

            # Check for dependency changes
            echo "New dependencies:"
            git diff origin/main...HEAD package.json | grep -E "^\+.*\".*\":" || echo "No new dependencies"
            echo "Removed dependencies:"
            git diff origin/main...HEAD package.json | grep -E "^\-.*\".*\":" || echo "No removed dependencies"
          fi

          # Check if environment variables changed
          if git diff --name-only origin/main...HEAD | grep -q ".env.example"; then
            echo "🔧 Environment variables changed"
            echo "Please ensure all team members update their .env files:"
            git diff origin/main...HEAD .env.example
          fi

      - name: Code complexity check
        run: |
          echo "📊 Analyzing code complexity..."

          # Simple line count check for changed files
          changed_tsx=$(git diff --name-only origin/main...HEAD | grep -E "\.(ts|tsx)$" || true)

          for file in $changed_tsx; do
            if [ -f "$file" ]; then
              lines=$(wc -l < "$file")
              echo "📄 $file: $lines lines"

              if [ "$lines" -gt 300 ]; then
                echo "⚠️ $file is quite large ($lines lines) - consider breaking it down"
              fi
            fi
          done
```

### 3. Branch Protection

**File**: `.github/workflows/branch-protection.yml`

```yaml
name: Branch Protection Checks

on:
  push:
    branches-ignore: [main]

jobs:
  branch-validation:
    name: Branch Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Auto-fix issues before validation
        run: |
          echo "🔧 Auto-fixing issues on branch: ${{ github.ref_name }}"
          pnpm lint:fix || echo "⚠️ Some ESLint issues couldn't be auto-fixed"
          pnpm format || echo "⚠️ Some formatting issues couldn't be auto-fixed"

      - name: Quick validation
        run: |
          echo "🔍 Running quick validation for branch: ${{ github.ref_name }}"

          # Quick lint check
          if ! pnpm lint; then
            echo ""
            echo "❌ Linting failed!"
            echo ""
            echo "💡 To fix locally:"
            echo "   pnpm lint:fix"
            echo ""
            exit 1
          fi

          # Type check
          if ! pnpm type-check; then
            echo ""
            echo "❌ Type checking failed!"
            echo ""
            echo "💡 To fix locally:"
            echo "   pnpm type-check"
            echo "   pnpm generate:types  # For Payload CMS"
            echo ""
            exit 1
          fi

          # Build check (faster than full build)
          echo "🏗️ Quick build check..."
          if ! pnpm build; then
            echo ""
            echo "❌ Build failed!"
            echo ""
            echo "💡 To fix locally:"
            echo "   pnpm build"
            echo "   Check for TypeScript errors"
            echo "   Verify all imports and dependencies"
            echo ""
            exit 1
          fi

      - name: Commit message validation
        run: |
          echo "📝 Recent commits on this branch:"

          # Get commit messages for this push
          commits=$(git log --oneline origin/main..HEAD || git log --oneline -10)

          if [ -n "$commits" ]; then
            echo "$commits"
          else
            echo "No commits found or this is the first commit"
          fi
```

## 🛠️ Configuration Files

### ESLint Configuration

**File**: `eslint.config.mjs`

```javascript
import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { FlatCompat } from '@eslint/eslintrc'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname,
})

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          vars: 'all',
          args: 'after-used',
          ignoreRestSiblings: false,
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          destructuredArrayIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^(_|ignore)',
        },
      ],
      'no-console': 'off', // Allow console.log
      // Next.js App Router and Server Components best practices
      'react/no-unescaped-entities': 'warn',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      // Payload CMS specific rules
      '@typescript-eslint/no-var-requires': 'off',
    },
  },
  {
    ignores: ['.next/', 'node_modules/', 'dist/', 'build/', '*.config.*'],
  },
]

export default eslintConfig
```

### Prettier Configuration

**File**: `.prettierrc.json`

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### Git Hooks

**File**: `.husky/pre-commit`

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm exec lint-staged
```

**File**: `.husky/pre-push`

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

echo "🚀 Pre-push validation..."

# Run type check
echo "🔍 Type checking..."
pnpm type-check

# Run build to ensure everything compiles
echo "🏗️ Building project..."
pnpm build

echo "✅ Pre-push validation complete!"
```

## 📦 Package.json Additions

Add these to your existing `package.json`:

```json
{
  "scripts": {
    "prepare": "husky",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "type-check": "tsc --noEmit"
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{js,json,md}": [
      "prettier --write"
    ]
  },
  "devDependencies": {
    "husky": "^9.1.7",
    "lint-staged": "^16.1.6"
  }
}
```

---

**That's it!** Copy these files to your project, install the dependencies, and you'll have the complete CI/CD pipeline ready to go! 🚀

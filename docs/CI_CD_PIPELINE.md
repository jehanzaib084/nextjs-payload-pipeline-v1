# CI/CD Pipeline Documentation

## Overview

This project implements a comprehensive CI/CD pipeline for a Next.js application with Payload CMS, focusing on TypeScript/TSX support and modern development practices.

## Pipeline Components

### 1. Pre-commit Hooks (Husky + lint-staged)

**Location**: `.husky/pre-commit`

**What it does**:
- Runs ESLint with auto-fix on staged TypeScript/TSX files
- Formats code with Prettier
- Ensures code quality before commits

**Configuration**: `package.json` lint-staged section

```json
"lint-staged": {
  "*.{ts,tsx}": [
    "eslint --fix",
    "prettier --write"
  ],
  "*.{js,json,md}": [
    "prettier --write"
  ]
}
```

### 2. Pre-push Hooks

**Location**: `.husky/pre-push`

**What it does**:
- Type checking with TypeScript
- Full project build to ensure compilation
- Prevents broken code from being pushed

### 3. GitHub Actions Workflows

#### Main CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs**:

1. **Code Quality & Linting**
   - Auto-fixes ESLint issues before validation
   - Auto-formats code with Prettier
   - TypeScript type checking with detailed error messages
   - Next.js App Router best practices validation
   - Specific fix commands provided for each error type

2. **Payload CMS Validation**
   - Payload config validation with error handling
   - Automatic type generation
   - Collections structure validation
   - Environment variables verification
   - Database connection testing

3. **Build & Test**
   - Full project build with helpful debugging tips
   - Test execution (with error tolerance for minimal testing)
   - Environment file creation for testing

4. **Security Audit**
   - Dependency vulnerability scanning
   - Moderate security level enforcement
   - Continues on error to avoid blocking development

5. **Deployment Ready Check** (main branch only)
   - Production build verification
   - Build size analysis and reporting
   - Final deployment readiness confirmation

#### PR Quality Checks (`.github/workflows/pr-checks.yml`)

**What it checks**:
- Auto-fixes linting and formatting issues in PR code
- Changed files analysis for focused validation
- TypeScript/TSX file validation with proper error handling
- Next.js App Router compliance checking
- Payload CMS changes validation and type generation
- Breaking changes detection in dependencies and environment
- Code complexity analysis with file size warnings

#### Branch Protection (`.github/workflows/branch-protection.yml`)

**For non-main branches**:
- Auto-fixes issues before validation for immediate resolution
- Quick validation on push for fast feedback
- Commit message display for transparency
- Focused on helpful guidance rather than strict enforcement

## Next.js App Router Best Practices Validation

The pipeline automatically checks for:

### 1. Server Components
- Validates proper use of `async` Server Components
- Checks for appropriate `'use server'` directives
- Ensures Server Component patterns are followed

### 2. App Router Structure
- Validates app directory structure
- Checks for proper `layout.tsx` files
- Verifies `loading.tsx` and `error.tsx` patterns

### 3. Middleware Usage
- Detects middleware implementation
- Validates middleware patterns

## Payload CMS Specific Checks

### 1. Configuration Validation
- Payload config file validation
- Type generation verification
- Collections structure validation

### 2. Environment Variables
- Required environment variables check
- Database connection validation

## ESLint Configuration

**Key rules for Next.js + Payload CMS**:

```javascript
{
  'no-console': 'off', // Allows console.log as requested
  'react/no-unescaped-entities': 'warn',
  'react-hooks/rules-of-hooks': 'error',
  'react-hooks/exhaustive-deps': 'warn',
  '@typescript-eslint/no-var-requires': 'off', // For Payload CMS compatibility
}
```

## Package Scripts

```json
{
  "lint": "next lint",
  "lint:fix": "eslint . --ext .ts,.tsx --fix",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "type-check": "tsc --noEmit"
}
```

## Environment Setup

### Required Environment Variables

- `DATABASE_URI`: Database connection string
- `PAYLOAD_SECRET`: JWT encryption secret
- `NEXT_PUBLIC_SERVER_URL`: Public server URL
- `CRON_SECRET`: Cron job authentication
- `PREVIEW_SECRET`: Preview request validation

## Running Locally

### 1. Install Dependencies
```bash
pnpm install
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Development
```bash
pnpm dev
```

### 4. Manual Quality Checks
```bash
# Lint check
pnpm lint

# Format check
pnpm format:check

# Type check
pnpm type-check

# Build
pnpm build
```

## Industry Standards Compliance

This pipeline follows industry best practices:

### 1. **Continuous Integration**
- Automated testing on every push/PR
- Multi-stage validation
- Parallel job execution for efficiency

### 2. **Code Quality**
- Automated linting and formatting
- Type safety enforcement
- Security vulnerability scanning

### 3. **Next.js Specific**
- App Router pattern validation
- Server/Client Component best practices
- Performance optimization checks

### 4. **Payload CMS Integration**
- CMS configuration validation
- Type safety for collections
- Environment variable management

### 5. **Development Workflow**
- Pre-commit quality gates
- PR validation
- Branch protection
- Automated reviewer assignment

## Troubleshooting

### Common Issues

1. **Pre-commit hook fails**
   - Run `pnpm lint:fix` manually
   - Check for TypeScript errors

2. **Build fails in CI**
   - Verify environment variables
   - Check Payload CMS configuration

3. **Type checking fails**
   - Run `pnpm generate:types` for Payload
   - Check for missing type definitions

### Getting Help

- Check the GitHub Actions logs for detailed error messages
- Ensure all environment variables are properly set
- Verify that your code follows Next.js App Router patterns

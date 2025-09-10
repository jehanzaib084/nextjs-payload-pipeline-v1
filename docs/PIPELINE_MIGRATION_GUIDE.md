# Pipeline Migration Guide

## How to Copy This CI/CD Pipeline to Your Existing Next.js + Payload CMS Project

This guide will help you migrate this comprehensive CI/CD pipeline to your existing Next.js project with Payload CMS. The process is designed to be simple and non-disruptive.

## 📋 Prerequisites

Before starting, ensure your existing project has:
- ✅ **Next.js 13+** with App Router
- ✅ **Payload CMS 3.x**
- ✅ **TypeScript** configuration
- ✅ **pnpm** as package manager (or we'll help you migrate)
- ✅ **Git repository** with GitHub

## 🚀 Step-by-Step Migration

### Step 1: Copy GitHub Actions Workflows

1. **Create the workflows directory** in your project:
```bash
mkdir -p .github/workflows
```

2. **Copy the workflow files** from this project:
```bash
# Copy all three workflow files
cp /path/to/this/project/.github/workflows/ci.yml .github/workflows/
cp /path/to/this/project/.github/workflows/pr-checks.yml .github/workflows/
cp /path/to/this/project/.github/workflows/branch-protection.yml .github/workflows/
```

Or manually create each file with the content provided below.

### Step 2: Install Required Dependencies

Add the necessary dev dependencies to your project:

```bash
# Install Husky and lint-staged for Git hooks
pnpm add -D husky lint-staged

# Install ESLint and Prettier if not already installed
pnpm add -D eslint prettier @eslint/eslintrc

# Initialize Husky
pnpm exec husky init
```

### Step 3: Update package.json Scripts

Add these scripts to your `package.json`:

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
  }
}
```

### Step 4: Configure ESLint

Create or update your `eslint.config.mjs`:

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

### Step 5: Configure Prettier

Create `.prettierrc.json` (if not exists):

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

### Step 6: Set Up Git Hooks

Create the pre-commit hook:

```bash
# Create pre-commit hook
cat > .husky/pre-commit << 'EOF'
pnpm exec lint-staged
EOF

# Make it executable
chmod +x .husky/pre-commit
```

Create the pre-push hook:

```bash
# Create pre-push hook
cat > .husky/pre-push << 'EOF'
echo "🚀 Pre-push validation..."

# Run type check
echo "🔍 Type checking..."
pnpm type-check

# Run build to ensure everything compiles
echo "🏗️ Building project..."
pnpm build

echo "✅ Pre-push validation complete!"
EOF

# Make it executable
chmod +x .husky/pre-push
```

### Step 7: Package Manager Migration (If Needed)

If your project uses `npm` or `yarn`, migrate to `pnpm`:

```bash
# Remove existing lock files
rm package-lock.json yarn.lock

# Install pnpm globally
npm install -g pnpm

# Install dependencies with pnpm
pnpm install
```

**Update workflow files** if you want to use a different package manager:
- Replace `pnpm` with `npm` or `yarn` in all workflow files
- Update cache settings in GitHub Actions

### Step 8: Environment Variables

Ensure your `.env.example` includes all required variables:

```bash
# Database connection string
DATABASE_URI=your-database-connection

# Used to encrypt JWT tokens  
PAYLOAD_SECRET=your-secret-here

# Used to configure CORS, format links and more
NEXT_PUBLIC_SERVER_URL=http://localhost:3000

# Secret used to authenticate cron jobs
CRON_SECRET=your-cron-secret

# Used to validate preview requests
PREVIEW_SECRET=your-preview-secret
```

## 📁 Required Files Checklist

After migration, ensure these files exist in your project:

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
├── .prettierrc.json
├── package.json (with updated scripts)
└── .env.example
```

## 🔧 Customization Options

### Workflow Triggers
Modify the branch names in workflow files if needed:

```yaml
on:
  push:
    branches: [main, develop]  # Change to your branch names
  pull_request:
    branches: [main, develop]  # Change to your branch names
```

### Node.js Version
Update Node.js version if your project requires a different version:

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18'  # Change to your preferred version
```

### Package Manager
If you prefer npm or yarn, update all occurrences in workflow files:

```yaml
# For npm
- run: npm ci
- run: npm run lint

# For yarn  
- run: yarn install --frozen-lockfile
- run: yarn lint
```

### Database Configuration
If using PostgreSQL instead of SQLite:

```yaml
- name: Create test environment file
  run: |
    cp .env.example .env
    echo "DATABASE_URI=postgresql://localhost:5432/test" >> .env
```

## 🧪 Testing Your Migration

After completing the migration:

1. **Test pre-commit hooks**:
```bash
# Make a small change and commit
echo "// test" >> src/test.ts
git add src/test.ts
git commit -m "test: commit hook"
```

2. **Test workflows locally** (if you have `act` installed):
```bash
# Install act (GitHub Actions local runner)
# Then test workflows
act push
```

3. **Push to trigger workflows**:
```bash
git push origin your-branch-name
```

4. **Check GitHub Actions tab** in your repository to see results

## 🔍 Verification Steps

✅ **Pre-commit hooks working**: Code gets auto-formatted on commit  
✅ **Pre-push hooks working**: Type checking runs before push  
✅ **CI pipeline running**: GitHub Actions execute on push/PR  
✅ **Error messages helpful**: Clear guidance when issues occur  
✅ **Auto-fixes working**: Linting and formatting issues resolved automatically  

## 🚨 Common Migration Issues

### Issue: Pre-commit hook not running
**Solution**: 
```bash
# Ensure Husky is properly installed
pnpm dlx husky install
# Make hooks executable
chmod +x .husky/pre-commit .husky/pre-push
```

### Issue: ESLint configuration errors
**Solution**: 
```bash
# Check ESLint config syntax
pnpm eslint --print-config src/test.ts
# Fix any syntax errors in eslint.config.mjs
```

### Issue: Workflow fails with "command not found"
**Solution**: 
- Ensure all scripts exist in `package.json`
- Check package manager installation
- Verify script names match workflow references

### Issue: Type checking fails
**Solution**: 
```bash
# Generate Payload types
pnpm payload generate:types
# Check TypeScript configuration
pnpm type-check
```

### Issue: Build fails in CI
**Solution**: 
- Verify environment variables in GitHub Settings > Secrets
- Check Payload CMS configuration
- Ensure all dependencies are properly installed

## 🎯 Next Steps

After successful migration:

1. **Configure GitHub branch protection rules**
2. **Set up deployment workflows** (if needed)
3. **Add team members** to repository
4. **Document project-specific changes**
5. **Train team** on new workflow processes

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Husky Documentation](https://typicode.github.io/husky/)
- [lint-staged Documentation](https://github.com/okonet/lint-staged)
- [Next.js Documentation](https://nextjs.org/docs)
- [Payload CMS Documentation](https://payloadcms.com/docs)

## 💡 Pro Tips

1. **Start with a feature branch** when migrating to test everything works
2. **Migrate one workflow at a time** to isolate any issues
3. **Keep your existing CI/CD** running until new pipeline is verified
4. **Test on a small PR first** to ensure everything works correctly
5. **Document any customizations** you make for your team

---

This pipeline is designed to be **developer-friendly** and **non-disruptive**. Every error includes specific fix commands, and most issues are automatically resolved! 🚀

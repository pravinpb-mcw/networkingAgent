# Package Manager Support: Bun vs NPM

## Overview

All Linux scripts now support **both bun and npm** as package managers. The scripts automatically detect which one is available and use it.

## Why Bun?

**Bun** is a modern JavaScript runtime and package manager that's significantly faster than npm:

- ⚡ **3-10x faster** than npm
- 📦 **Drop-in replacement** - works with package.json
- 🔄 **Compatible** with npm packages
- 💾 **Smaller** disk footprint
- 🚀 **Built-in** bundler and test runner

## Installation

### Install Bun (Recommended)

```bash
# One-line install
curl -fsSL https://bun.sh/install | bash

# Reload shell
source ~/.bashrc  # or ~/.zshrc

# Verify
bun --version
```

**Or use the helper script:**
```bash
chmod +x install_bun.sh
./install_bun.sh
```

### Install NPM (Traditional)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install npm

# CentOS/RHEL
sudo yum install npm

# Arch Linux
sudo pacman -S npm

# Verify
npm --version
```

## How Scripts Choose

All scripts follow this logic:

1. **Check for bun first** (preferred)
2. **Fall back to npm** if bun not found
3. **Error if neither** is available

Example from `start_react_dashboard.sh`:
```bash
if command -v bun &> /dev/null; then
    PKG_MANAGER="bun"
elif command -v npm &> /dev/null; then
    PKG_MANAGER="npm"
else
    echo "Error: Neither bun nor npm found!"
    exit 1
fi
```

## Commands Comparison

| Task | Bun | NPM |
|------|-----|-----|
| **Install dependencies** | `bun install` | `npm install` |
| **Run dev server** | `bun run dev` | `npm run dev` |
| **Add package** | `bun add package` | `npm install package` |
| **Remove package** | `bun remove package` | `npm uninstall package` |
| **Update packages** | `bun update` | `npm update` |
| **Run script** | `bun run script` | `npm run script` |

## Performance Comparison

**Installing dependencies (react_dashboard):**
- **bun:** ~2-5 seconds
- **npm:** ~15-30 seconds

**Starting dev server:**
- **bun:** ~1-2 seconds
- **npm:** ~3-5 seconds

## Which Should You Use?

### Use Bun if:
- ✅ You want **maximum speed**
- ✅ You're starting a **new project**
- ✅ You want **modern tooling**
- ✅ You're on **Linux or macOS**

### Use NPM if:
- ✅ You have **existing npm workflows**
- ✅ You need **maximum compatibility**
- ✅ Your team **uses npm**
- ✅ You're on **Windows** (bun support is experimental)

## Switching Between Them

You can switch at any time:

### From NPM to Bun:
```bash
cd react_dashboard
rm -rf node_modules package-lock.json
bun install
```

### From Bun to NPM:
```bash
cd react_dashboard
rm -rf node_modules bun.lockb
npm install
```

## Scripts That Use Package Managers

All these scripts auto-detect bun/npm:

- `start_react_dashboard.sh`
- `start_complete_system.sh`
- `start_full_a2a_system.sh`
- `setup_linux.sh`

## Troubleshooting

### Bun Not Found After Install

```bash
# Reload shell configuration
source ~/.bashrc
# or
source ~/.zshrc

# Or restart terminal
```

### NPM Permission Errors

```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Package Manager Not Found

```bash
# Install bun
curl -fsSL https://bun.sh/install | bash

# Or install npm
sudo apt install npm  # Ubuntu/Debian
```

### Both Installed - Which is Used?

Scripts prioritize **bun over npm**. To force npm:

```bash
# Temporarily remove bun from PATH
export PATH=$(echo $PATH | tr ':' '\n' | grep -v ".bun" | tr '\n' ':')

# Or uninstall bun temporarily
rm ~/.bun/bin/bun
```

## Migration Guide

### Existing NPM Project → Bun

```bash
# 1. Install bun
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc

# 2. Remove npm artifacts
cd react_dashboard
rm -rf node_modules package-lock.json

# 3. Install with bun
bun install

# 4. Run project
bun run dev
```

### Testing Both

```bash
# Test with bun
cd react_dashboard
bun install
bun run dev

# Test with npm (in different terminal)
cd react_dashboard
rm -rf node_modules bun.lockb
npm install
npm run dev
```

## Additional Resources

- **Bun Docs:** https://bun.sh/docs
- **NPM Docs:** https://docs.npmjs.com/
- **Comparison:** https://bun.sh/docs/cli/install

## Summary

- 🚀 **Scripts auto-detect** which package manager to use
- ⚡ **Bun is faster** but npm is more established
- 🔄 **Both work** with our scripts
- 🎯 **Choose based** on your needs
- 🛠️ **Easy to switch** between them

---

**Recommendation:** Start with bun for speed, fall back to npm if you encounter compatibility issues.

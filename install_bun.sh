#!/bin/bash
# Quick script to install bun package manager
# Bun is faster than npm and compatible with Node.js packages

echo "================================================================================"
echo "   Installing Bun Package Manager"
echo "================================================================================"
echo
echo "Bun is a fast all-in-one JavaScript runtime and package manager."
echo "It's a drop-in replacement for npm/yarn with significantly better performance."
echo
echo "Installing bun..."
echo

curl -fsSL https://bun.sh/install | bash

echo
echo "================================================================================"
echo "   Installation Complete!"
echo "================================================================================"
echo
echo "To use bun in your current terminal session, run:"
echo "  source ~/.bashrc"
echo "  # or"
echo "  source ~/.zshrc"
echo
echo "Or simply open a new terminal window."
echo
echo "Verify installation:"
echo "  bun --version"
echo
echo "You can now run the setup:"
echo "  ./setup_linux.sh"
echo
echo "================================================================================"

# Packster

A cross-OS package migration helper that automates the transition from Ubuntu/WSL to macOS using AI-powered analysis and intelligent package mapping.

## What Packster Does

Packster analyzes your Ubuntu/WSL system and generates a complete migration plan for macOS using both traditional mapping and AI-powered analysis:

> **🚀 Recent Updates**: Packster now features AI-powered migration using Claude AI, optimized batch processing, and improved script generation for better reliability and performance.

1. **Detects** your source environment (Ubuntu/WSL)
2. **Collects** installed packages from:
   - `apt` (manually installed packages)
   - `pip` (global and user packages)
   - `npm` (global packages)
   - `cargo` (Rust packages)
   - `gem` (Ruby gems)
3. **Maps** Ubuntu packages to macOS equivalents using:
   - Traditional registry-based mapping + heuristics
   - **AI-powered analysis** using Claude AI for intelligent package mapping
4. **Validates** suggested targets exist in Homebrew
5. **Generates** a complete migration toolkit:
   - `Brewfile` for Homebrew packages and casks
   - Language-specific package lists
   - `bootstrap.sh` script for automated installation
   - **AI-generated installation script** with copy-paste ready commands
   - Detailed HTML and JSON reports
   - **Unavailable packages report** with alternatives and explanations

## Installation

### Using uv (recommended)
```bash
uv pip install packster
```

### Using pipx
```bash
pipx install packster
```

### From source
```bash
git clone https://github.com/packster/packster.git
cd packster
pip install -e .
```

## Usage

### Basic Usage
```bash
# Generate migration files with traditional mapping
packster generate --target=macos --out ./packster-out

# Navigate to output directory and run bootstrap
cd packster-out
./bootstrap.sh

# Or use AI-powered migration for better results
packster generate --llm-migrate --api-key YOUR_CLAUDE_API_KEY
```

### Advanced Usage
```bash
# Use custom registry
packster generate --target=macos --out ./packster-out \
    --registry registry/custom-mappings.yaml

# Skip validation (faster, but less accurate)
packster generate --target=macos --out ./packster-out --no-verify

# Output format options
packster generate --target=macos --out ./packster-out --format json

# AI-powered migration with Claude (recommended)
packster generate --llm-migrate --api-key YOUR_CLAUDE_API_KEY

# Combined generation + LLM migration with custom batch size
packster generate --llm-migrate --api-key YOUR_CLAUDE_API_KEY --llm-batch-size 50

# Run LLM migration separately on existing report
packster llm-migrate --api-key YOUR_CLAUDE_API_KEY --report ./packster-out/report.json
```

### AI-Powered Migration (Recommended)

Packster's AI-powered migration using Claude AI provides superior package mapping and generates ready-to-run installation scripts:

```bash
# Generate migration files with AI assistance (recommended)
packster generate --llm-migrate --api-key YOUR_CLAUDE_API_KEY

# Or run LLM migration separately on existing report
packster llm-migrate --api-key YOUR_CLAUDE_API_KEY

# Customize batch processing for large package lists
packster llm-migrate --api-key YOUR_CLAUDE_API_KEY --batch-size 50
```

**Key Features:**
- **Intelligent Analysis**: Claude AI analyzes each package for macOS compatibility
- **Multi-Method Support**: Determines best installation method (Homebrew, Cask, MacPorts, direct download, etc.)
- **Ready-to-Run Scripts**: Generates copy-paste ready installation commands
- **Comprehensive Reports**: Detailed analysis of unavailable packages with alternatives
- **Batch Processing**: Efficiently handles large package lists (170+ packages) in configurable batches
- **Error Handling**: Robust fallback mechanisms and progress tracking

**Performance Optimizations:**
- **66% faster processing** with optimized batch sizes (50 packages per batch)
- **Automatic streaming fallback** for large requests
- **Individual package installation** to avoid malformed commands
- **Progress indicators** for each batch

**Example AI Migration Output:**
```bash
# AI-generated installation script
#!/bin/bash
echo '🚀 Starting macOS package migration...'

echo '📦 Installing Homebrew packages...'
brew install git
brew install sl
brew install docker

echo '🍺 Installing Homebrew casks...'
brew install --cask docker

echo '🔗 Direct installations:'
pip3 install anthropic
pip3 install httpx

echo '✅ Package migration completed!'
```

## Output Structure

```
packster-out/
├── Brewfile                    # Homebrew packages and casks
├── bootstrap.sh                # Automated installation script
├── lang/
│   ├── requirements.txt        # Python packages
│   ├── global-node.txt         # npm global packages
│   ├── cargo.txt              # Rust packages
│   └── gems.txt               # Ruby gems
├── report.json                # Detailed migration report
├── report.html                # Human-readable report
├── llm-migration-install.sh   # AI-generated installation script (if using AI)
├── llm-migration-unavailable.md  # Unavailable packages report (if using AI)
└── llm-migration-response.json   # Full AI response (if using AI)
```

## Understanding the Reports

### Traditional Mapping Report
The generated report categorizes packages into four sections:

- **Auto**: High-confidence mappings that will be installed automatically
- **Verify**: Medium-confidence mappings that should be reviewed
- **Manual**: Packages that couldn't be automatically mapped
- **Skipped**: Packages that were intentionally excluded

### AI-Powered Migration Reports
When using AI-powered migration, you'll get additional reports:

- **Installation Script**: Copy-paste ready commands organized by installation method
- **Unavailable Packages Report**: Detailed analysis of packages that can't be migrated with alternatives
- **Full AI Response**: Complete JSON response from Claude AI for debugging

## Limitations

- **No app settings**: Only package names are migrated, not configurations
- **Linux-specific packages**: Some Ubuntu packages have no macOS equivalent (AI migration provides better alternatives)
- **GUI applications**: Limited support for desktop applications
- **Version pinning**: Exact version matching is not yet supported
- **API dependency**: AI-powered migration requires a Claude API key

## Roadmap

- [ ] Windows/Winget target support
- [ ] Arch Linux (pacman) collector
- [x] AI-powered mapping suggestions
- [x] Batch processing for large package lists
- [x] Optimized script generation
- [ ] Interactive TUI for package selection
- [ ] Configuration file migration
- [ ] Version-aware mapping
- [ ] Docker container support

## Development

### Setup
```bash
git clone https://github.com/packster/packster.git
cd packster
pip install -e ".[dev]"
```

### Running Tests
```bash
make test
# or
pytest
```

### Linting
```bash
make lint
# or
ruff check .
```

### Building
```bash
make build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

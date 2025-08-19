# Packster

A cross-OS package migration helper that automates the transition from Ubuntu/WSL to macOS Homebrew.

## What Packster Does

Packster analyzes your Ubuntu/WSL system and generates a complete migration plan for macOS:

1. **Detects** your source environment (Ubuntu/WSL)
2. **Collects** installed packages from:
   - `apt` (manually installed packages)
   - `pip` (global and user packages)
   - `npm` (global packages)
   - `cargo` (Rust packages)
   - `gem` (Ruby gems)
3. **Maps** Ubuntu packages to Homebrew equivalents using a registry + heuristics
4. **Validates** suggested targets exist in Homebrew
5. **Generates** a complete migration toolkit:
   - `Brewfile` for Homebrew packages and casks
   - Language-specific package lists
   - `bootstrap.sh` script for automated installation
   - Detailed HTML and JSON reports

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
# Generate migration files
packster generate --target=macos --out ./packster-out

# Navigate to output directory and run bootstrap
cd packster-out
./bootstrap.sh
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
```

## Output Structure

```
packster-out/
├── Brewfile              # Homebrew packages and casks
├── bootstrap.sh          # Automated installation script
├── lang/
│   ├── requirements.txt  # Python packages
│   ├── global-node.txt   # npm global packages
│   ├── cargo.txt         # Rust packages
│   └── gems.txt          # Ruby gems
├── report.json           # Detailed migration report
└── report.html           # Human-readable report
```

## Understanding the Report

The generated report categorizes packages into four sections:

- **Auto**: High-confidence mappings that will be installed automatically
- **Verify**: Medium-confidence mappings that should be reviewed
- **Manual**: Packages that couldn't be automatically mapped
- **Skipped**: Packages that were intentionally excluded

## Limitations

- **No app settings**: Only package names are migrated, not configurations
- **Linux-specific packages**: Some Ubuntu packages have no macOS equivalent
- **GUI applications**: Limited support for desktop applications
- **Version pinning**: Exact version matching is not yet supported

## Roadmap

- [ ] Windows/Winget target support
- [ ] Arch Linux (pacman) collector
- [ ] LLM-powered mapping suggestions
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

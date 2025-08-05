# MetaMCP Documentation

This directory contains the complete documentation for the MetaMCP project. The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install mkdocs mkdocs-material mkdocs-autorefs mkdocs-section-index

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Docker Development
```bash
# Build and serve using Docker
docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material
```

## 📁 Structure

The documentation is organized into logical sections:

- **`getting-started/`** - New user guides and quick starts
- **`user-guide/`** - End-user documentation and feature guides
- **`developer-guide/`** - Developer documentation and technical guides
- **`development/`** - Development resources and analysis documents
- **`api/`** - API documentation and reference
- **`oauth/`** - OAuth-specific documentation
- **`monitoring/`** - Operations and monitoring guides
- **`reference/`** - Technical reference materials

## 📝 Contributing

### Adding New Documentation

1. **Choose the right location**: Place new documentation in the appropriate section
2. **Follow the structure**: Use the standard document structure (see `development/documentation-structure.md`)
3. **Update navigation**: Add new pages to `mkdocs.yml`
4. **Test locally**: Build and test documentation before submitting

### Documentation Standards

- **Clear headings**: Use descriptive, hierarchical headings
- **Code examples**: Include working, tested code examples
- **Cross-references**: Link to related documentation
- **Progressive disclosure**: Start simple, build complexity
- **Consistent formatting**: Follow the established style guide

### Quality Checklist

Before submitting documentation changes:

- [ ] Documentation builds without errors
- [ ] All links work correctly
- [ ] Code examples are tested and working
- [ ] Content follows style guidelines
- [ ] Navigation is updated in `mkdocs.yml`
- [ ] No broken references or images

## 🔧 Configuration

### MkDocs Configuration

The main configuration file is `mkdocs.yml` in the project root. Key settings:

- **Theme**: Material for MkDocs with custom styling
- **Plugins**: Search, minification, and auto-references
- **Extensions**: Comprehensive markdown extensions for rich content
- **Navigation**: Hierarchical navigation structure

### Build Process

The documentation is automatically built and deployed using GitHub Actions:

1. **Trigger**: Changes to documentation files or code
2. **Build**: Generate static HTML from markdown
3. **Deploy**: Deploy to GitHub Pages (main branch only)
4. **Quality Checks**: Link validation and markdown quality

## 🎨 Styling

### Material Theme Features

- **Dark/Light Mode**: Automatic theme switching
- **Search**: Full-text search with highlighting
- **Navigation**: Expandable navigation with sections
- **Code Highlighting**: Syntax highlighting for all languages
- **Admonitions**: Callout boxes for notes, warnings, etc.
- **Tabs**: Tabbed content for multiple examples

### Custom Styling

- **Primary Color**: Indigo theme
- **Icons**: Material Design and FontAwesome icons
- **Typography**: Optimized for readability
- **Responsive**: Mobile-friendly design

## 📊 Analytics

Documentation usage is tracked through:

- **GitHub Pages Analytics**: Page views and user behavior
- **Search Analytics**: What users are searching for
- **Feedback**: GitHub issues and discussions

## 🔗 Resources

- **MkDocs Documentation**: https://www.mkdocs.org/
- **Material for MkDocs**: https://squidfunk.github.io/mkdocs-material/
- **GitHub Pages**: https://pages.github.com/
- **Markdown Guide**: https://www.markdownguide.org/

## 🐛 Troubleshooting

### Common Issues

**Build Errors**
```bash
# Check for syntax errors
mkdocs build --strict

# Validate configuration
mkdocs --version
```

**Missing Pages**
- Ensure pages are listed in `mkdocs.yml` navigation
- Check file paths are correct
- Verify markdown syntax

**Broken Links**
- Use relative links within the documentation
- Test external links regularly
- Use the link checker in CI/CD

### Getting Help

- **GitHub Issues**: Report documentation bugs
- **Discord**: Ask questions in the community
- **Pull Requests**: Submit improvements directly

---

*For detailed information about the documentation structure and guidelines, see [Documentation Structure](development/documentation-structure.md).*
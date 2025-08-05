# MetaMCP Documentation

Welcome to the MetaMCP documentation! This comprehensive guide will help you understand, install, configure, and use the Meta Model Context Protocol system.

## 🚀 Quick Navigation

### For New Users
- **[Quick Start Guide](getting-started/quick-start.md)** - Get up and running in minutes
- **[Proxy Quick Start](getting-started/proxy-quick-start.md)** - Learn about proxy functionality
- **[User Guide](user-guide/api-reference.md)** - Complete user documentation

### For Developers
- **[Development Setup](developer-guide/development-setup.md)** - Set up your development environment
- **[Architecture Overview](developer-guide/architecture.md)** - Understand the system design
- **[Contributing Guidelines](development/contributing.md)** - How to contribute to the project

### For System Administrators
- **[Configuration Reference](configuration.md)** - Complete configuration options
- **[Production Setup](monitoring/production-setup.md)** - Deploy to production
- **[Security Features](security.md)** - Security best practices

## 📚 Documentation Sections

### Getting Started
Essential guides to get you started with MetaMCP:
- **Quick Start**: Basic installation and first steps
- **Proxy Quick Start**: Understanding and using proxy functionality
- **Configuration**: Setting up your environment

### User Guide
Complete user documentation for all features:
- **API Reference**: Complete API documentation
- **Proxy Wrapper**: Advanced proxy usage
- **Security**: Security features and best practices

### Developer Guide
Comprehensive development documentation:
- **Development Setup**: Environment setup for developers
- **Code Structure**: Understanding the codebase
- **Architecture**: System design and components
- **Proxy Development**: Building custom proxies
- **Testing**: Testing strategies and guidelines

### API Documentation
Complete API reference:
- **REST API**: HTTP API endpoints
- **WebSocket API**: Real-time communication
- **MCP Protocol**: Model Context Protocol implementation

### Monitoring & Operations
Production deployment and monitoring:
- **Overview**: Monitoring architecture
- **Production Setup**: Production deployment guide
- **Telemetry**: Metrics and observability

### Reference
Technical reference materials:
- **Configuration**: All configuration options
- **Environment Variables**: Environment variable reference
- **Proxy API**: Proxy-specific API documentation

## 🔧 Key Features

### MCP Transport Support
- **WebSocket**: Full MCP protocol over WebSocket
- **HTTP**: REST-based MCP communication
- **stdio**: Standard I/O for containers and CLI tools

### Advanced Features
- **OAuth Integration**: Multi-provider authentication
- **API Versioning**: Comprehensive version management
- **Security**: Enterprise-grade security features
- **Monitoring**: Built-in observability and telemetry

### Developer Experience
- **Comprehensive Testing**: Unit, integration, and performance tests
- **CI/CD Pipeline**: Automated testing and deployment
- **Documentation**: Auto-generated API documentation

## 🛠️ Installation Options

### Local Development
```bash
git clone https://github.com/lichtbaer/MetaMCP.git
cd MetaMCP
pip install -r requirements.txt
```

### Docker Deployment
```bash
docker-compose up -d
```

### Production Deployment
See the [Production Setup Guide](monitoring/production-setup.md) for detailed instructions.

## 📖 Additional Resources

- **[Composition Improvements](composition-improvements.md)**: Advanced composition features
- **[Roadmap](roadmap.md)**: Future development plans
- **[Development Analysis](development/analysis/DOCUMENTATION_WORKFLOW_CHANGES.md)**: Technical analysis and implementation details

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](development/contributing.md) for details on how to get involved.

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/lichtbaer/MetaMCP/issues)
- **Discord**: [Join our community](https://discord.gg/metamcp)
- **Documentation**: This site is always up to date with the latest features

---

*Last updated: {{ git.date }}* 
# 🤝 Contributing to X-Plane Dataref Bridge

First off, thank you for considering contributing to X-Plane Dataref Bridge! 🎉 It's people like you that make open source such a great community.

## 📋 Table of Contents
- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Submitting Changes](#-submitting-changes)
- [Style Guidelines](#-style-guidelines)
- [Commit Message Guidelines](#-commit-message-guidelines)
- [Issue and Pull Request Labels](#-issue-and-pull-request-labels)
- [Community](#-community)

## 🤝 Code of Conduct
This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 💡 How Can I Contribute?

### Reporting Bugs
- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/Rororo098/Xplane-Dataref-Bridge/issues)
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/Rororo098/Xplane-Dataref-Bridge/issues/new)
- Use the **Bug Report** template and provide as much detail as possible

### Suggesting Enhancements
- **Check existing feature requests** to avoid duplicates
- **Open a new feature request** using the **Feature Request** template
- **Provide detailed use cases** and technical specifications if possible

### Contributing Code
- **Fork the repository** and create your branch from `main`
- **Follow the style guidelines** described below
- **Write tests** for new functionality
- **Update documentation** if your changes affect user-facing features
- **Submit a pull request** with a clear description of your changes

### Improving Documentation
- **Fix typos and grammatical errors**
- **Add missing documentation** for features
- **Improve existing documentation** for clarity
- **Add examples and tutorials**

### Helping Others
- **Answer questions** in discussions and issues
- **Review pull requests** from other contributors
- **Help test new features** and provide feedback

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/Xplane-Dataref-Bridge.git
   cd Xplane-Dataref-Bridge
   ```
3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/Rororo098/Xplane-Dataref-Bridge.git
   ```
4. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- Git
- X-Plane 11 or 12 (for testing)
- Arduino IDE (for hardware testing)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

### Running Tests
```bash
# Run unit tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_module.py
```

## 📤 Submitting Changes

1. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. **Open a Pull Request** against the `main` branch
3. **Use the Pull Request template** and fill out all sections
4. **Wait for review** and address any feedback
5. **Celebrate!** 🎉 Your contribution will be merged once approved

## 🎨 Style Guidelines

### Python Code
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation
- Limit lines to 88 characters
- Use descriptive variable and function names
- Add docstrings to all public functions and classes

### Arduino Code
- Follow Arduino style conventions
- Use clear comments for complex logic
- Organize code into logical sections
- Use consistent naming for pins and variables

### Documentation
- Use Markdown for all documentation
- Keep sentences clear and concise
- Use lists and tables for complex information
- Include code examples where helpful

### Commit Messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally

## 📝 Commit Message Guidelines

### Format
```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

### Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Example
```
feat(arduino): add support for ESP32-S2 boards

- Implement new serial protocol for ESP32-S2
- Add example sketch for ESP32-S2
- Update documentation with wiring instructions

Closes #42
```

## 🏷️ Issue and Pull Request Labels

| Label | Description |
|-------|-------------|
| `bug` | Confirmed bugs or issues |
| `enhancement` | Feature requests |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `question` | Questions and discussions |
| `wontfix` | Will not be worked on |
| `duplicate` | Duplicate of another issue |

## 🤗 Community

### Communication Channels
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and ideas
- **Pull Requests**: For code contributions

### Community Guidelines
- Be respectful and inclusive
- Provide constructive feedback
- Help others when you can
- Follow the Code of Conduct

### Recognition
All contributors will be recognized in the project's CONTRIBUTORS.md file and in release notes.

---

Thank you for contributing to X-Plane Dataref Bridge! Your efforts help make this project better for everyone in the flight simulation community. 🛩️🚀

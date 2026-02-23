# Contributing to Loan Underwriter AI

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/loan-underwriter.git
   cd loan-underwriter
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio black isort mypy
   ```

3. Set up your `.env` file with your Google API key

4. Run in development mode:
   ```bash
   python run.py
   ```

## 🧪 Testing

Run tests before submitting:
```bash
pytest tests/
```

## 📝 Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting

Format your code before committing:
```bash
black loan_underwriter/
isort loan_underwriter/
```

## 📁 Project Structure

```
loan_underwriter/
├── agents/          # AI agents (add new agents here)
├── api/             # API routes and schemas
├── templates/       # HTML templates
└── static/          # Static files (CSS, JS)
```

## 🆕 Adding a New Agent

1. Create a new file in `loan_underwriter/agents/`:
   ```python
   # loan_underwriter/agents/my_agent.py
   from .base_agent import BaseAgent
   
   class MyAgent(BaseAgent):
       def _define_tools(self):
           # Define agent tools
           pass
       
       def _get_system_instruction(self):
           return "Your agent instructions..."
       
       async def analyze(self, data):
           # Implement analysis logic
           pass
   ```

2. Register in `loan_underwriter/agents/__init__.py`

3. Add to the aggregator in `aggregator_agent.py`

## 🔄 Pull Request Process

1. **Update documentation** if you change functionality
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update the README** if needed
5. **Create a descriptive PR** explaining your changes

## 📜 Commit Messages

Use clear commit messages:
- `feat: Add income verification agent`
- `fix: Correct DTI calculation`
- `docs: Update setup instructions`
- `refactor: Simplify risk score calculation`

## 🐛 Reporting Issues

When reporting issues, include:
1. Python version (`python --version`)
2. Operating system
3. Error messages (full traceback)
4. Steps to reproduce

## 💡 Feature Requests

We welcome feature requests! Please:
1. Check existing issues first
2. Describe the use case
3. Explain the expected behavior

## 📧 Questions?

- Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup help
- Read the [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for architecture details
- Review the [Visual Diagrams](docs/) for system understanding
- Review existing issues for similar questions
- Create a new issue with the "question" label

## 📚 Documentation Resources

- **[README.md](README.md)** - Quick start guide
- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Full technical documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation and configuration
- **[docs/](docs/)** - Visual SVG diagrams:
  - `architecture.svg` - Fan-Out/Fan-In pattern
  - `data-flow.svg` - Processing pipeline
  - `tech-stack.svg` - Technology layers
  - `api-integrations.svg` - External APIs

---

Thank you for contributing! 🎉

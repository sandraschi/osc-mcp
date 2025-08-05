# Contributing to OSCMCP

Thank you for your interest in contributing to OSCMCP! We welcome contributions from everyone, regardless of experience level. This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before making any contributions.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** to your local machine:
   ```bash
   git clone https://github.com/yourusername/oscmcp.git
   cd oscmcp
   ```
3. **Set up a development environment**:
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   .\venv\Scripts\activate
   
   # Install the package in development mode with all dependencies
   pip install -e ".[dev]"
   ```
4. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Making Changes

1. **Write tests** for any new functionality or bug fixes.
2. **Run the tests** to make sure they pass:
   ```bash
   pytest
   ```
3. **Format your code** using Black and isort:
   ```bash
   black src tests
   isort src tests
   ```
4. **Lint your code** to catch any potential issues:
   ```bash
   flake8 src tests
   mypy src
   ```
5. **Update the documentation** if your changes affect the API or behavior.

## Submitting a Pull Request

1. **Commit your changes** with a clear and descriptive commit message:
   ```bash
   git commit -m "Add feature: brief description of the change"
   ```
2. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Open a Pull Request** from your fork to the main repository.
4. **Wait for review** and address any feedback from the maintainers.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. When reporting a bug, please include:

- A clear description of the issue
- Steps to reproduce the problem
- Expected vs. actual behavior
- Any relevant error messages or logs
- Your environment (OS, Python version, etc.)

## Development Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
- Write docstrings for all public functions, classes, and methods following [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Keep commits small and focused on a single feature or fix.
- Write meaningful commit messages that explain the "why" not just the "what".
- Update the documentation when adding new features or changing behavior.

## Testing

- Write unit tests for all new functionality.
- Ensure all tests pass before submitting a pull request.
- Aim for good test coverage (80%+).
- Use descriptive test function names that explain what they're testing.

## Code Review Process

1. A maintainer will review your pull request.
2. The reviewer may request changes or ask questions.
3. Once approved, your changes will be merged into the main branch.

## License

By contributing to this project, you agree that your contributions will be licensed under the [MIT License](LICENSE).

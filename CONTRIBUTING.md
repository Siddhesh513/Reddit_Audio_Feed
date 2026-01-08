# Contributing to Reddit Audio Feed

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Reddit API credentials (for testing Reddit features)
- Basic understanding of FastAPI and vanilla JavaScript

### Setting Up Development Environment

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Reddit_Audio_Feed.git
cd Reddit_Audio_Feed

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/Reddit_Audio_Feed.git

# 4. Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Install development dependencies
pip install pytest pytest-cov black ruff mypy

# 6. Configure environment
cp ../.env.example .env
# Add your Reddit API credentials

# 7. Run tests to verify setup
pytest
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Lint your code
ruff check src tests

# Format your code
black src tests

# Type checking
mypy src
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: Add audio export to MP3 format"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks

### 5. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python (Backend)

#### Style Guide

Follow PEP 8 and use the provided tools:

```bash
# Format code
black src tests

# Lint code
ruff check src tests --fix

# Type hints
mypy src
```

#### Best Practices

```python
# ✅ Good
def process_reddit_post(post: RedditPost) -> AudioFile:
    """
    Process a Reddit post and generate audio file.

    Args:
        post: RedditPost object containing post data

    Returns:
        AudioFile object with generated audio metadata

    Raises:
        ValueError: If post has no text content
    """
    if not post.text_content:
        raise ValueError("Post must have text content")

    return audio_generator.generate(post.text_content)

# ❌ Avoid
def process(p):
    return gen(p.text)
```

#### Type Hints

Always use type hints:

```python
from typing import List, Optional, Dict

def fetch_posts(
    subreddit: str,
    limit: int = 10,
    sort_type: str = "hot"
) -> List[RedditPost]:
    """Type hints make code self-documenting"""
    pass
```

#### Error Handling

```python
# ✅ Good
try:
    result = api.fetch_data()
except RequestException as e:
    logger.error(f"API request failed: {e}")
    raise HTTPException(status_code=503, detail="Service unavailable")

# ❌ Avoid
try:
    result = api.fetch_data()
except:
    pass
```

### JavaScript (Frontend)

#### Style Guide

- Use ES6+ features
- Prefer `const` and `let` over `var`
- Use template literals for strings
- Follow existing code style

```javascript
// ✅ Good
const fetchPosts = async (subreddit, limit = 10) => {
    try {
        const response = await api.fetchPosts(subreddit, limit);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch posts:', error);
        throw error;
    }
};

// ❌ Avoid
function fetchPosts(subreddit, limit) {
    var response = api.fetchPosts(subreddit, limit);
    return response.data;
}
```

#### Comments

```javascript
// ✅ Good - Explain WHY, not WHAT
// Retry failed requests with exponential backoff to handle rate limiting
const retryRequest = async (fn, maxRetries = 3) => {
    // ...
};

// ❌ Avoid - Obvious comments
// This function fetches posts
const fetchPosts = () => {
    // ...
};
```

## Testing

### Writing Tests

#### Backend Tests

```python
# tests/test_your_feature.py
import pytest
from src.services.your_service import YourService

def test_your_feature():
    """Test description"""
    # Arrange
    service = YourService()
    input_data = "test data"

    # Act
    result = service.process(input_data)

    # Assert
    assert result is not None
    assert result.status == "success"

@pytest.fixture
def sample_post():
    """Fixture for test data"""
    return RedditPost(
        title="Test Post",
        text_content="Test content"
    )

def test_with_fixture(sample_post):
    """Use fixtures for reusable test data"""
    assert sample_post.title == "Test Post"
```

#### Test Coverage

Aim for:
- New features: 80%+ coverage
- Bug fixes: Tests that reproduce the bug
- Refactoring: Maintain existing coverage

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_reddit_service.py

# Specific test
pytest tests/test_reddit_service.py::test_fetch_posts

# With coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Submitting Changes

### Creating a Pull Request

1. **Push your branch** to your fork
2. **Go to the original repository** on GitHub
3. **Click "New Pull Request"**
4. **Select your branch** from your fork
5. **Fill in the PR template**:
   - Clear title describing the change
   - Description of what and why
   - Link to related issues
   - Screenshots (for UI changes)
   - Test results

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed the code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests for new features
```

### Review Process

1. **Automated checks** run on your PR
2. **Maintainer review** - may request changes
3. **Address feedback** and push updates
4. **Approval** - maintainer approves
5. **Merge** - maintainer merges to main

## Reporting Issues

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 13.0]
- Python: [e.g., 3.11]
- Browser: [e.g., Chrome 120]

## Screenshots
If applicable

## Additional Context
Any other relevant information
```

### Feature Requests

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How might this work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## Areas for Contribution

### Good First Issues

Look for issues labeled:
- `good first issue` - Beginner friendly
- `help wanted` - Community help needed
- `documentation` - Docs improvements

### Priority Areas

1. **Frontend Enhancements**
   - Better error messages
   - Loading states
   - Accessibility improvements

2. **Backend Features**
   - Additional TTS engines
   - Queue optimization
   - Caching layer

3. **Testing**
   - Increase test coverage
   - Integration tests
   - E2E tests

4. **Documentation**
   - API examples
   - Tutorial videos
   - Troubleshooting guides

5. **Performance**
   - Optimize audio generation
   - Reduce bundle size
   - Database integration

## Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Report bugs and request features
- 📧 **Email**: Contact maintainers for sensitive issues

## Recognition

Contributors will be:
- Listed in the README
- Credited in release notes
- Given credit in commit history

Thank you for contributing to Reddit Audio Feed! 🎉

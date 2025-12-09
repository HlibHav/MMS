# Contributing Guide

## Development Process

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches

### Workflow

1. Create feature branch from `develop`
2. Make changes and write tests
3. Ensure all tests pass
4. Update documentation if needed
5. Create pull request to `develop`
6. After review, merge to `develop`
7. Deploy to staging for testing
8. Merge to `main` for production

## Code Standards

### Python

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Maximum line length: 100 characters
- Use Black for formatting
- Use mypy for type checking

### TypeScript/React

- Use functional components
- Prefer hooks over class components
- Use TypeScript strict mode
- Follow React best practices
- Use ESLint + Prettier

## Testing Requirements

- All new features must include tests
- Aim for >80% code coverage
- Write unit tests for engines and tools
- Write integration tests for agents
- Write E2E tests for critical flows

## Documentation

- Update README for user-facing changes
- Update API docs for endpoint changes
- Add code comments for complex logic
- Update architecture docs for structural changes

## Pull Request Process

1. **Title**: Use conventional commit format
   - `feat: add scenario comparison feature`
   - `fix: correct margin calculation`
   - `docs: update API documentation`

2. **Description**: Include
   - What changed and why
   - How to test
   - Screenshots (for UI changes)
   - Breaking changes (if any)

3. **Checklist**:
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Code follows style guidelines
   - [ ] All tests pass
   - [ ] No breaking changes (or documented)

## Review Process

- At least one approval required
- All CI checks must pass
- Address review comments
- Keep PRs focused and small

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

**Example**:
```
feat(scenarios): add scenario comparison table

- Implement comparison view in Scenario Lab
- Add KPI breakdown by channel
- Add validation indicators

Closes #123
```

## Getting Help

- Check existing documentation
- Review similar code in codebase
- Ask in team chat
- Create issue for discussion




---
name: qa-testing-expert
description: "Comprehensive software quality assurance and testing expertise. Covers unit tests (pytest, Jest, Go testing), integration tests, E2E tests (Playwright, Cypress), API testing, code review checklists, security vulnerability detection (OWASP Top 10), edge case analysis, and test coverage strategies. Use when writing tests, reviewing code quality, finding bugs, checking security, or defining QA strategies."
license: MIT
version: 1.0.0
metadata:
  author: tester-qa-agent
---

# QA & Testing Expert

Full-spectrum software quality assurance. From unit tests to security audits — find bugs before users do.

## When to Use

- Writing unit, integration, or E2E tests
- Reviewing code for bugs, edge cases, or security issues
- Defining a test strategy for a new feature or project
- Checking API contracts and error handling
- Validating database queries and business logic correctness
- Performing pre-launch quality checks

## Testing Pyramid

```
        /\
       /E2E\          ← Few, slow, high confidence (Playwright, Cypress)
      /------\
     /  Integ  \      ← Some, moderate speed (API tests, DB tests)
    /------------\
   /  Unit Tests  \   ← Many, fast, isolated (pytest, Jest, Go test)
  /-----------------\
```

**Rule:** Write mostly unit tests, some integration tests, few E2E tests.

## Unit Testing Patterns

### Python (pytest)
```python
# Good: test one behavior, clear name
def test_calculate_total_applies_discount():
    cart = Cart(items=[Item(price=100)], discount=0.1)
    assert cart.total() == 90.0

# Use fixtures for shared setup
@pytest.fixture
def db_session():
    session = create_test_db()
    yield session
    session.rollback()

# Parametrize for multiple inputs
@pytest.mark.parametrize("price,discount,expected", [
    (100, 0.1, 90),
    (200, 0.2, 160),
    (0,   0.5, 0),
])
def test_discount_calculation(price, discount, expected):
    assert calculate_discounted(price, discount) == expected
```

### JavaScript (Jest)
```javascript
// Mock external dependencies
jest.mock('../api/userService');

test('shows error when login fails', async () => {
  userService.login.mockRejectedValue(new Error('Invalid credentials'));
  render(<LoginForm />);
  fireEvent.click(screen.getByRole('button', { name: /login/i }));
  expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
});
```

## Code Review Checklist

### Logic & Correctness
- [ ] Does the code do what the function/method name says?
- [ ] Are all edge cases handled? (empty list, null, zero, negative)
- [ ] Are error paths tested, not just happy paths?
- [ ] Are async operations awaited correctly?

### Security (OWASP Top 10)
- [ ] **Injection** — Is user input sanitized before DB queries? (use parameterized queries, never string concatenation)
- [ ] **Auth** — Are endpoints protected? Is JWT/session validated server-side?
- [ ] **Sensitive data** — Are passwords hashed (bcrypt)? No secrets in logs or responses?
- [ ] **XSS** — Is user input escaped before rendering in HTML?
- [ ] **CSRF** — Are state-changing endpoints protected with CSRF tokens?
- [ ] **Broken Access Control** — Can user A access user B's data?

### Performance
- [ ] Are there N+1 query problems? (use eager loading or batch queries)
- [ ] Is pagination applied to list endpoints?
- [ ] Are expensive operations cached?

### Code Quality
- [ ] No dead code or commented-out blocks
- [ ] Functions do one thing (Single Responsibility)
- [ ] No magic numbers — use named constants
- [ ] Error messages are descriptive and actionable

## API Testing

```python
# Test all response scenarios
def test_create_user_returns_201(client):
    response = client.post("/api/users", json={"email": "a@b.com", "password": "secure123"})
    assert response.status_code == 201
    assert "id" in response.json()

def test_create_user_rejects_duplicate_email(client, existing_user):
    response = client.post("/api/users", json={"email": existing_user.email})
    assert response.status_code == 409

def test_get_user_requires_auth(client):
    response = client.get("/api/users/1")
    assert response.status_code == 401
```

## Edge Cases to Always Check

| Category | Edge Cases |
|----------|-----------|
| **Strings** | Empty `""`, whitespace only `"   "`, very long string, special chars `<>&'"` |
| **Numbers** | Zero `0`, negative, max int, float precision, `NaN`, `Infinity` |
| **Lists/Arrays** | Empty `[]`, single item, duplicate items, very large list |
| **Dates** | Leap year, timezone differences, past/future extremes, invalid format |
| **Auth** | Expired token, tampered token, missing token, wrong role |
| **Concurrency** | Race conditions on shared resource, duplicate submission |
| **Network** | Timeout, partial response, connection drop, retry behavior |

## Bug Report Format

When finding a bug, report it as:

```
## Bug: [short title]

**Severity:** Critical / High / Medium / Low

**Steps to reproduce:**
1. [step 1]
2. [step 2]

**Expected:** [what should happen]
**Actual:** [what actually happens]

**Root cause:** [suspected or confirmed cause]
**Fix:** [suggested fix or code change]
```

## Pre-Launch QA Checklist

- [ ] All critical paths have test coverage
- [ ] No `console.log` / `print` debug statements in production code
- [ ] Environment variables are validated at startup
- [ ] Rate limiting is in place on public APIs
- [ ] Error responses don't leak stack traces or internal details
- [ ] Database migrations are reversible
- [ ] Health check endpoint returns correct status

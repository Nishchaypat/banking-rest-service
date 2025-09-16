# Security Considerations for Banking API

This document outlines critical security vulnerabilities and recommendations for the banking application backend.

## Current Security Implementation

### Existing Security Measures
- JWT token-based authentication with 30-minute expiration
- Account ownership verification for all operations
- Basic password hashing using HS256
- Database transaction rollbacks on transfer failures
- External transfer limits ($5,000 maximum)
- SQLite WAL mode for better concurrent access

## Critical Security Vulnerabilities

### 1. **Weak Password Hashing**
**Issue**: HS256 is cryptographically insecure for password storage
```python
# Current implementation (INSECURE)
hashed_pw = hashlib.HS256(user.password.encode()).hexdigest()
```

**Better to have**:
- Use Firebase
- Implement minimum password requirements
- Add password strength validation


### 2. **Hardcoded Secret Key**
**Issue**: JWT secret key is self coded
```python
SECRET_KEY = "FROM ENV"
```

**Better to have **:
- Implement secret rotation strategy

### 3. **Better Input Validation**
**Issues**:
- Simple use of Pydantic

**Better to have**:
- Need more advance Pydantic validators for all models
- Add input length limits and format validation


### 4. **SQL Injection Vulnerabilities**
**Issue**: While parameterized queries are used, there's no additional protection

### 5. **Missing Rate Limiting**
**Issues**:
- No API rate limiting

### 6. **Insecure Card Number Generation**
**Issue**: Random number generation for card numbers is predictable

**Better to have**:
- Use cryptographically secure random number generation

### 7. **Plain Text PIN Storage**
**Issue**: Card PINs stored in plain text


**Better to have**:
- Hash PINs with salt (bcrypt/Argon2)
- Implement PIN attempt limiting
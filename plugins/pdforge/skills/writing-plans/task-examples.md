# Task Examples Reference

This document provides concrete examples of well-written tasks for the `writing-plans` skill.

## Example 1: Create Data Model (TypeScript)

### T001: Create User Interface and Type

**File**: `src/types/user.ts`
**Action**: Create new file
**Estimate**: 2 min
**Dependencies**: None

**Context**: Define the core User type used throughout the authentication system.

**Code**:
```typescript
export interface User {
  id: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
  updatedAt: Date;
  isVerified: boolean;
  verificationToken: string | null;
  lastLoginAt: Date | null;
}

export interface CreateUserInput {
  email: string;
  password: string;
}

export interface UserPublic {
  id: string;
  email: string;
  isVerified: boolean;
  createdAt: Date;
}

export function toPublicUser(user: User): UserPublic {
  return {
    id: user.id,
    email: user.email,
    isVerified: user.isVerified,
    createdAt: user.createdAt,
  };
}
```

**Verification**:
```bash
npx tsc --noEmit
# Expected: No errors
```

**Success Criteria**:
- [ ] File exists at `src/types/user.ts`
- [ ] TypeScript compiles without errors
- [ ] All interfaces exported

---

## Example 2: Create Utility Function

### T002: Create Password Hashing Utility

**File**: `src/utils/password.ts`
**Action**: Create new file
**Estimate**: 3 min
**Dependencies**: None

**Context**: Utility for secure password hashing using bcrypt.

**Code**:
```typescript
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

export async function hashPassword(plainPassword: string): Promise<string> {
  if (!plainPassword || plainPassword.length < 8) {
    throw new Error('Password must be at least 8 characters');
  }
  return bcrypt.hash(plainPassword, SALT_ROUNDS);
}

export async function verifyPassword(
  plainPassword: string,
  hashedPassword: string
): Promise<boolean> {
  if (!plainPassword || !hashedPassword) {
    return false;
  }
  return bcrypt.compare(plainPassword, hashedPassword);
}
```

**Verification**:
```bash
npx tsc --noEmit
npm test -- --grep "password"
```

**Success Criteria**:
- [ ] File exists at `src/utils/password.ts`
- [ ] bcrypt is in dependencies
- [ ] Functions handle edge cases

---

## Example 3: Write Unit Test

### T003: Add Password Utility Tests

**File**: `src/utils/__tests__/password.test.ts`
**Action**: Create new file
**Estimate**: 4 min
**Dependencies**: T002

**Context**: Unit tests for password hashing utility.

**Code**:
```typescript
import { describe, it, expect } from 'vitest';
import { hashPassword, verifyPassword } from '../password';

describe('hashPassword', () => {
  it('should hash a valid password', async () => {
    const hash = await hashPassword('validPassword123');
    expect(hash).toBeDefined();
    expect(hash).not.toBe('validPassword123');
    expect(hash.length).toBeGreaterThan(20);
  });

  it('should throw for password shorter than 8 chars', async () => {
    await expect(hashPassword('short')).rejects.toThrow(
      'Password must be at least 8 characters'
    );
  });

  it('should throw for empty password', async () => {
    await expect(hashPassword('')).rejects.toThrow(
      'Password must be at least 8 characters'
    );
  });

  it('should generate different hashes for same password', async () => {
    const hash1 = await hashPassword('samePassword123');
    const hash2 = await hashPassword('samePassword123');
    expect(hash1).not.toBe(hash2);
  });
});

describe('verifyPassword', () => {
  it('should return true for correct password', async () => {
    const hash = await hashPassword('correctPassword');
    const result = await verifyPassword('correctPassword', hash);
    expect(result).toBe(true);
  });

  it('should return false for incorrect password', async () => {
    const hash = await hashPassword('correctPassword');
    const result = await verifyPassword('wrongPassword', hash);
    expect(result).toBe(false);
  });

  it('should return false for empty password', async () => {
    const hash = await hashPassword('somePassword123');
    const result = await verifyPassword('', hash);
    expect(result).toBe(false);
  });

  it('should return false for empty hash', async () => {
    const result = await verifyPassword('somePassword', '');
    expect(result).toBe(false);
  });
});
```

**Verification**:
```bash
npm test -- src/utils/__tests__/password.test.ts
# Expected: All 8 tests passing
```

**Success Criteria**:
- [ ] All tests pass
- [ ] Edge cases covered
- [ ] No test isolation issues

---

## Example 4: Create API Endpoint

### T004: Create POST /api/auth/register Endpoint

**File**: `src/routes/auth.ts`
**Action**: Modify existing file (add route)
**Estimate**: 5 min
**Dependencies**: T001, T002

**Context**: Registration endpoint that creates new users.

**Code**:
```typescript
// Add to existing auth router

import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { hashPassword } from '../utils/password';
import { User, CreateUserInput } from '../types/user';
import { db } from '../db';
import { v4 as uuid } from 'uuid';

const registerSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

router.post('/register', async (req: Request, res: Response) => {
  try {
    // Validate input
    const validationResult = registerSchema.safeParse(req.body);
    if (!validationResult.success) {
      return res.status(400).json({
        error: 'Validation failed',
        details: validationResult.error.flatten().fieldErrors,
      });
    }

    const { email, password } = validationResult.data;

    // Check if user exists
    const existingUser = await db.user.findUnique({ where: { email } });
    if (existingUser) {
      return res.status(409).json({
        error: 'User already exists',
      });
    }

    // Create user
    const passwordHash = await hashPassword(password);
    const user = await db.user.create({
      data: {
        id: uuid(),
        email,
        passwordHash,
        isVerified: false,
        verificationToken: uuid(),
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    });

    // Return success (without password hash)
    return res.status(201).json({
      id: user.id,
      email: user.email,
      isVerified: user.isVerified,
      createdAt: user.createdAt,
    });
  } catch (error) {
    console.error('Registration error:', error);
    return res.status(500).json({
      error: 'Internal server error',
    });
  }
});
```

**Verification**:
```bash
# Type check
npx tsc --noEmit

# Test endpoint (requires running server)
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Expected: 201 with user object
```

**Success Criteria**:
- [ ] Endpoint responds to POST
- [ ] Validates input with proper errors
- [ ] Returns 409 for duplicate email
- [ ] Returns 201 with user (no passwordHash)

---

## Example 5: Create React Component

### T005: Create LoginForm Component

**File**: `src/components/auth/LoginForm.tsx`
**Action**: Create new file
**Estimate**: 5 min
**Dependencies**: None (can be done in parallel with backend)

**Context**: Login form with email/password fields and validation.

**Code**:
```typescript
import React, { useState, FormEvent } from 'react';

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export function LoginForm({ onSubmit, isLoading = false, error }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Client-side validation
    if (!email) {
      setValidationError('Email is required');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setValidationError('Invalid email format');
      return;
    }
    if (!password) {
      setValidationError('Password is required');
      return;
    }
    if (password.length < 8) {
      setValidationError('Password must be at least 8 characters');
      return;
    }

    await onSubmit(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>Login</h2>
      
      {(error || validationError) && (
        <div className="error-message" role="alert">
          {error || validationError}
        </div>
      )}

      <div className="form-field">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          autoComplete="email"
        />
      </div>

      <div className="form-field">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          autoComplete="current-password"
        />
      </div>

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

**Verification**:
```bash
# Type check
npx tsc --noEmit

# Run component tests
npm test -- --grep "LoginForm"

# Visual check (storybook or dev server)
npm run storybook
# Navigate to LoginForm story
```

**Success Criteria**:
- [ ] Component renders without errors
- [ ] Form validation works
- [ ] Loading state disables inputs
- [ ] Error messages display correctly

---

## Task Size Reference

| Task Type | Target Time | Example |
|-----------|-------------|---------|
| Create type/interface | 2 min | Define User interface |
| Create utility function | 3 min | Password hashing |
| Write unit test file | 4 min | Test password utility |
| Create API endpoint | 5 min | POST /register |
| Create React component | 5 min | LoginForm |
| Add database migration | 3 min | Add users table |
| Update configuration | 2 min | Add env variable |

If a task exceeds these times, break it down further.

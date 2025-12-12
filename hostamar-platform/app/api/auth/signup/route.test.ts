
const { POST } = require('./route');
const { NextResponse } = require('next/server');

// Mock Prisma
jest.mock('@/lib/prisma', () => ({
  prisma: {
    customer: {
      findUnique: jest.fn(),
      create: jest.fn(),
    },
  },
}));

// Mock bcrypt
jest.mock('bcrypt', () => ({
  hash: jest.fn(() => Promise.resolve('hashed_password')),
}));

// Mock email
jest.mock('@/lib/email', () => ({
  sendWelcomeEmail: jest.fn(() => Promise.resolve()),
}));

// Mock NextResponse
jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((body, init) => ({ body, status: init?.status || 200 })),
  },
}));

describe('Signup Route', () => {
  it('should reject passwords that are only whitespace', async () => {
    const request = {
      json: jest.fn(() => Promise.resolve({
        email: 'test@example.com',
        password: '      ', // 6 spaces
        name: 'Test User'
      })),
    };

    const response = await POST(request);

    // Expectation: Should fail because password is just spaces
    // Current buggy behavior: It passes because length is 6
    // We want it to fail with 400
    if (response.status === 201) {
        throw new Error('Bug reproduced: Whitespace password was accepted');
    }
    
    expect(response.status).toBe(400);
    expect(response.body.error).toMatch(/Password/);
  });
});

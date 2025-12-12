import { NextResponse } from 'next/server'
import bcrypt from 'bcrypt'
import { prisma } from '@/lib/prisma'
import { sendWelcomeEmail } from '@/lib/email'

// Enhanced signup handler with better validation and error reporting
export async function POST(request: Request) {
  try {
    const body = await request.json()
    let { email, password, name, businessName, industry } = body || {}

    // Basic field normalization
    email = typeof email === 'string' ? email.trim().toLowerCase() : ''
    name = typeof name === 'string' ? name.trim() : ''
    password = typeof password === 'string' ? password.trim() : ''
    businessName = typeof businessName === 'string' ? businessName.trim() : ''
    industry = typeof industry === 'string' ? industry.trim() : ''

    // Validation
    if (!email || !password || !name) {
      return NextResponse.json({ error: 'Missing required fields: name, email, password' }, { status: 400 })
    }
    if (password.length < 6) {
      return NextResponse.json({ error: 'Password must be at least 6 characters' }, { status: 400 })
    }
    // Basic email format check
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return NextResponse.json({ error: 'Invalid email format' }, { status: 400 })
    }

    // Duplicate check
    const existingCustomer = await prisma.customer.findUnique({ where: { email } })
    if (existingCustomer) {
      return NextResponse.json({ error: 'Email already registered' }, { status: 409 })
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10)

    // Prepare customer data
    const data: any = {
      email,
      password: hashedPassword,
      name,
    }

    if (businessName) {
      data.business = {
        create: {
          name: businessName,
          industry: industry || 'Other'
        }
      }
    }

    let customer
    try {
      customer = await prisma.customer.create({
        data,
        include: { business: true }
      })
    } catch (err: any) {
      // Prisma specific error handling
      if (err?.code === 'P2002') {
        return NextResponse.json({ error: 'Email already registered' }, { status: 409 })
      }
      console.error('Prisma create customer error:', err)
      return NextResponse.json({ error: 'Unable to create account' }, { status: 500 })
    }

    // Send welcome email (async, don't wait for response)
    try {
      sendWelcomeEmail(customer.name || "User", customer.email).catch(err =>
        console.error("Failed to send welcome email:", err)
      );
    } catch (err) {
      console.error("Error sending welcome email:", err);
      // Don't fail signup if email fails
    }

    return NextResponse.json({
      id: customer.id,
      email: customer.email,
      name: customer.name,
      business: customer.business
    }, { status: 201 })
  } catch (error) {
    console.error('Signup route unexpected error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

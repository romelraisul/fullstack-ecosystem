import { NextResponse } from 'next/server'
import bcrypt from 'bcrypt'
import { prisma } from '@/lib/prisma'
import { sendWelcomeEmail } from '@/lib/email'
import { trackEvent } from '@/lib/analytics'

export async function POST(request: Request) {
  console.log("DEBUG: Signup Request Received")
  try {
    const body = await request.json()
    console.log("DEBUG: Body parsed")
    let { email, password, name, businessName, industry } = body || {}

    // Basic field normalization
    email = typeof email === 'string' ? email.trim().toLowerCase() : ''
    name = typeof name === 'string' ? name.trim() : ''
    password = typeof password === 'string' ? password.trim() : ''
    businessName = typeof businessName === 'string' ? businessName.trim() : ''
    industry = typeof industry === 'string' ? industry.trim() : ''

    // Validation
    if (!email || !password || !name) {
      console.log("DEBUG: Missing fields")
      return NextResponse.json({ error: 'Missing required fields: name, email, password' }, { status: 400 })
    }
    if (password.length < 6) {
      console.log("DEBUG: Password too short")
      return NextResponse.json({ error: 'Password must be at least 6 characters' }, { status: 400 })
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      console.log("DEBUG: Invalid email")
      return NextResponse.json({ error: 'Invalid email format' }, { status: 400 })
    }

    // Duplicate check
    console.log("DEBUG: Checking duplicate")
    const existingCustomer = await prisma.customer.findUnique({ where: { email } })
    if (existingCustomer) {
      console.log("DEBUG: Duplicate found")
      return NextResponse.json({ error: 'Email already registered' }, { status: 409 })
    }

    // Hash password
    console.log("DEBUG: Hashing password")
    const hashedPassword = await bcrypt.hash(password, 10)
    console.log("DEBUG: Password hashed")

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
      console.log("DEBUG: Creating customer in DB")
      customer = await prisma.customer.create({
        data,
        include: { business: true }
      })
      console.log("DEBUG: Customer created", customer.id)

      // Track signup event
      console.log("DEBUG: Tracking event")
      await trackEvent(customer.id, 'SIGNUP', { email: customer.email, name: customer.name })

    } catch (err: any) {
      console.error('DEBUG: Prisma/Event error:', err)
      if (err?.code === 'P2002') {
        return NextResponse.json({ error: 'Email already registered' }, { status: 409 })
      }
      return NextResponse.json({ error: 'Unable to create account' }, { status: 500 })
    }

    // Send welcome email
    try {
      console.log("DEBUG: Sending email")
      sendWelcomeEmail(customer.name || "User", customer.email).catch(err =>
        console.error("Failed to send welcome email:", err)
      );
    } catch (err) {
      console.error("Error sending welcome email:", err);
    }

    return NextResponse.json({
      id: customer.id,
      email: customer.email,
      name: customer.name,
      business: customer.business
    }, { status: 201 })
  } catch (error) {
    console.error('DEBUG: Signup route unexpected error:', error)
    return NextResponse.json({ error: 'Internal server error', details: String(error) }, { status: 500 })
  }
}
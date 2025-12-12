import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { prisma } from "@/lib/prisma";
import { generateVideoScript } from "@/lib/video-generator";



export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session?.user?.email) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { topic, businessName } = await req.json();

    if (!topic || !businessName) {
      return NextResponse.json(
        { error: "Missing topic or businessName" },
        { status: 400 },
      );
    }

    // Get customer
    const customer = await prisma.customer.findUnique({
      where: { email: session.user.email },
      include: { subscriptions: true, business: true },
    });

    if (!customer) {
      return NextResponse.json(
        { error: "Customer not found" },
        { status: 404 },
      );
    }

    // Check subscription videos limit
    const subscription = customer.subscriptions[0];
    if (!subscription) {
      return NextResponse.json(
        { error: "No active subscription" },
        { status: 403 },
      );
    }

    // Get this month's video count
    const monthStart = new Date();
    monthStart.setDate(1);
    const videosThisMonth = await prisma.video.count({
      where: {
        customerId: customer.id,
        createdAt: { gte: monthStart },
      },
    });

    if (videosThisMonth >= subscription.videosPerMonth) {
      return NextResponse.json(
        { error: "Video limit reached for this month" },
        { status: 429 },
      );
    }

    // Generate script
    const script = await generateVideoScript({
        customerId: customer.id,
        businessName: businessName || customer.business?.name || "My Business",
        industry: customer.business?.industry || "General",
        topic
    });

    // Create video record (status: processing)
    const video = await prisma.video.create({
      data: {
        customerId: customer.id,
        title: script.title,
        script: JSON.stringify(script),
        duration: script.duration,
        status: "processing",
        topic,
      },
    });

    // TODO: Queue video generation task (send to background worker/Celery/Bull)
    // For now, just return the video record

    return NextResponse.json({
      success: true,
      video: {
        id: video.id,
        title: video.title,
        status: video.status,
        createdAt: video.createdAt,
      },
    });
  } catch (error) {
    console.error("Video generation error:", error);
    return NextResponse.json(
      { error: "Failed to generate video" },
      { status: 500 },
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session?.user?.email) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const customer = await prisma.customer.findUnique({
      where: { email: session.user.email },
    });

    if (!customer) {
      return NextResponse.json(
        { error: "Customer not found" },
        { status: 404 },
      );
    }

    // Get customer's videos
    const videos = await prisma.video.findMany({
      where: { customerId: customer.id },
      orderBy: { createdAt: "desc" },
      take: 20,
    });

    return NextResponse.json({ videos });
  } catch (error) {
    console.error("Fetch videos error:", error);
    return NextResponse.json(
      { error: "Failed to fetch videos" },
      { status: 500 },
    );
  }
}

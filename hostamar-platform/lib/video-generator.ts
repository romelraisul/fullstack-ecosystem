/**
 * Video Generation Service
 * Generates marketing videos for customers using AI
 */

import { OpenAI } from 'openai';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs/promises';
import path from 'path';
import { randomUUID } from 'crypto';

// Initialize OpenAI (GitHub Models or Azure)
const openai = new OpenAI({
  apiKey: process.env.GITHUB_TOKEN,
  baseURL: 'https://models.inference.ai.azure.com',
});

// Initialize MinIO/S3 Client
const s3Client = new S3Client({
  endpoint: process.env.MINIO_ENDPOINT || 'http://localhost:9000',
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.MINIO_ACCESS_KEY || '',
    secretAccessKey: process.env.MINIO_SECRET_KEY || '',
  },
  forcePathStyle: true,
});

interface VideoGenerationParams {
  customerId: string;
  businessName: string;
  industry: string;
  topic: string;
  brandColor?: string;
  logoUrl?: string;
}

interface VideoScript {
  title: string;
  hook: string;
  mainContent: string[];
  callToAction: string;
  duration: number;
}

/**
 * Generate video script using AI
 */
export async function generateVideoScript(params: VideoGenerationParams): Promise<VideoScript> {
  const prompt = `
আপনি একজন expert marketing video script writer।

Business Details:
- Name: ${params.businessName}
- Industry: ${params.industry}
- Topic: ${params.topic}

Create a compelling 30-60 second video script in Bengali that:
1. Starts with an attention-grabbing hook
2. Delivers valuable information
3. Ends with a clear call-to-action
4. Is suitable for social media (Facebook, Instagram)

Format as JSON:
{
  "title": "Video title",
  "hook": "First 5 seconds attention grabber",
  "mainContent": ["Point 1", "Point 2", "Point 3"],
  "callToAction": "Final message",
  "duration": 45
}
`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content: 'You are a marketing expert specializing in short-form video content.',
      },
      {
        role: 'user',
        content: prompt,
      },
    ],
    response_format: { type: 'json_object' },
  });

  const script = JSON.parse(response.choices[0].message.content || '{}');
  return script;
}

/**
 * Generate voice-over from text
 * Using Google TTS (free) or ElevenLabs (better quality)
 */
export async function generateVoiceOver(text: string, outputPath: string): Promise<string> {
  // Option 1: Google TTS (free, basic)
  if (process.env.USE_GOOGLE_TTS === 'true') {
    const { TextToSpeechClient } = await import('@google-cloud/text-to-speech');
    const client = new TextToSpeechClient();

    const [response] = await client.synthesizeSpeech({
      input: { text },
      voice: { languageCode: 'bn-BD', name: 'bn-IN-Wavenet-A' },
      audioConfig: { audioEncoding: 'MP3' },
    });

    await fs.writeFile(outputPath, response.audioContent as Buffer);
    return outputPath;
  }

  // Option 2: ElevenLabs (premium)
  if (process.env.ELEVENLABS_API_KEY) {
    const { ElevenLabsClient, stream } = await import('elevenlabs-node');
    const client = new ElevenLabsClient({
      apiKey: process.env.ELEVENLABS_API_KEY,
    });

    const audio = await client.generate({
      voice: 'Bella', // Change to Bengali voice
      text,
      modelId: 'eleven_multilingual_v2',
    });

    await fs.writeFile(outputPath, audio);
    return outputPath;
  }

  // Fallback: Mock for development
  console.warn('No TTS service configured, using silent audio');
  return outputPath;
}

/**
 * Create video from assets
 * Combines images, text, voice-over, and music
 */
export async function composeVideo(
  script: VideoScript,
  params: VideoGenerationParams,
  outputPath: string
): Promise<string> {
  const tempDir = path.join(process.cwd(), 'temp', randomUUID());
  await fs.mkdir(tempDir, { recursive: true });

  try {
    // 1. Generate voice-over
    const voiceOverPath = path.join(tempDir, 'voiceover.mp3');
    const fullScript = `${script.hook}\n\n${script.mainContent.join('\n\n')}\n\n${script.callToAction}`;
    await generateVoiceOver(fullScript, voiceOverPath);

    // 2. Create video with FFmpeg
    // This is a simplified version - you'll need to add:
    // - Background images/videos
    // - Text overlays
    // - Logo placement
    // - Transitions
    
    return new Promise((resolve, reject) => {
      ffmpeg()
        // Input sources
        .input(voiceOverPath) // Voice-over audio
        .input(path.join(process.cwd(), 'assets/background.mp4')) // Background video
        
        // Video settings
        .size('1080x1920') // Portrait for social media
        .fps(30)
        .videoBitrate('2000k')
        
        // Add logo overlay
        .input(params.logoUrl || path.join(process.cwd(), 'assets/default-logo.png'))
        .complexFilter([
          // Position logo at top-right
          '[1:v][2:v]overlay=W-w-20:20[vid]',
          // Add text overlay (script.hook)
          `[vid]drawtext=text='${script.hook}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h-200[out]`,
        ])
        
        // Output
        .map('[out]')
        .map('0:a') // Use voice-over audio
        .output(outputPath)
        
        // Events
        .on('start', (cmd) => console.log('FFmpeg started:', cmd))
        .on('progress', (progress) => console.log('Processing:', progress.percent + '% done'))
        .on('end', () => {
          console.log('Video generation complete!');
          resolve(outputPath);
        })
        .on('error', (err) => {
          console.error('FFmpeg error:', err);
          reject(err);
        })
        .run();
    });
  } finally {
    // Cleanup temp files
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

/**
 * Upload video to MinIO/S3
 */
export async function uploadVideo(filePath: string, customerId: string): Promise<string> {
  const fileName = `${customerId}/${randomUUID()}.mp4`;
  const fileContent = await fs.readFile(filePath);

  await s3Client.send(
    new PutObjectCommand({
      Bucket: 'hostamar-videos',
      Key: fileName,
      Body: fileContent,
      ContentType: 'video/mp4',
    })
  );

  // Return public URL
  const publicUrl = `${process.env.MINIO_ENDPOINT}/hostamar-videos/${fileName}`;
  return publicUrl;
}

/**
 * Main function: Generate complete video
 */
export async function generateMarketingVideo(
  params: VideoGenerationParams
): Promise<{ videoUrl: string; script: VideoScript }> {
  console.log(`Generating video for ${params.businessName}...`);

  // 1. Generate script
  const script = await generateVideoScript(params);
  console.log('Script generated:', script.title);

  // 2. Compose video
  const tempVideoPath = path.join(process.cwd(), 'temp', `${randomUUID()}.mp4`);
  await composeVideo(script, params, tempVideoPath);
  console.log('Video composed');

  // 3. Upload to storage
  const videoUrl = await uploadVideo(tempVideoPath, params.customerId);
  console.log('Video uploaded:', videoUrl);

  // 4. Cleanup
  await fs.unlink(tempVideoPath);

  return { videoUrl, script };
}

/**
 * Generate multiple video topics for a business
 */
export async function suggestVideoTopics(businessName: string, industry: string): Promise<string[]> {
  const prompt = `
Suggest 10 engaging video topics for a ${industry} business called "${businessName}".
Topics should be:
- Educational and valuable
- Suitable for 30-60 second videos
- Shareable on social media
- In Bengali

Return as JSON array: ["topic 1", "topic 2", ...]
`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    response_format: { type: 'json_object' },
  });

  const result = JSON.parse(response.choices[0].message.content || '{"topics": []}');
  return result.topics || [];
}

// Export all functions
export default {
  generateVideoScript,
  generateVoiceOver,
  composeVideo,
  uploadVideo,
  generateMarketingVideo,
  suggestVideoTopics,
};

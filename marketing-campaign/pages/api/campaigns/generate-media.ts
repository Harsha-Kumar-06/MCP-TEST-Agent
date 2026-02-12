import type { NextApiRequest, NextApiResponse } from 'next';

/**
 * AI Media Generation API for Instagram Posts
 * 
 * Generates AI images/videos based on campaign information.
 * Uses OpenAI DALL-E for images or Stability AI as alternatives.
 * Falls back to placeholder images if AI service is unavailable.
 */

interface GenerateMediaRequest {
  productName: string;
  productDescription: string;
  features?: string;
  targetAudience?: string;
  brandVoice?: string;
  postType: 'image' | 'video' | 'carousel' | 'story';
  companyName?: string;
}

interface GenerateMediaResponse {
  success: boolean;
  mediaUrl?: string;
  mediaUrls?: string[];
  caption?: string;
  hashtags?: string;
  error?: string;
  isPlaceholder?: boolean;
}

// Generate AI image prompt from campaign info
function generateImagePrompt(data: GenerateMediaRequest): string {
  const { productName, productDescription, brandVoice, targetAudience } = data;
  
  let style = 'modern, clean, professional';
  if (brandVoice === 'casual' || brandVoice === 'playful') {
    style = 'vibrant, fun, colorful, energetic';
  } else if (brandVoice === 'luxury') {
    style = 'elegant, sophisticated, premium, minimalist';
  }

  return `Create a stunning Instagram marketing image for "${productName}". 
Product: ${productDescription.substring(0, 200)}
Target audience: ${targetAudience || 'general consumers'}
Style: ${style}, Instagram-worthy, high quality, 1080x1080 square format, 
visually appealing for social media marketing, no text overlay needed.`;
}

// Generate caption from campaign info
function generateCaption(data: GenerateMediaRequest): string {
  const { productName, productDescription, features, targetAudience, brandVoice, companyName } = data;
  
  const featuresList = features
    ?.split('\n')
    .filter(f => f.trim())
    .slice(0, 3)
    .map(f => `✓ ${f.trim()}`)
    .join('\n') || '';

  if (brandVoice === 'casual' || brandVoice === 'playful') {
    return `✨ ${productName} ✨

${productDescription}

🎯 Perfect for: ${targetAudience || 'You!'}

${featuresList ? `What you get:\n${featuresList}\n` : ''}
🔗 Link in bio!

Drop a ❤️ if you're excited!`.trim();
  } else if (brandVoice === 'luxury') {
    return `Introducing ${productName}

${productDescription}

Crafted for: ${targetAudience || 'The discerning individual'}

${featuresList ? `Excellence delivered:\n${featuresList}\n` : ''}
Discover more - Link in bio`.trim();
  } else {
    return `🚀 Introducing ${productName}!

${productDescription}

👥 Designed for: ${targetAudience || 'professionals like you'}

${featuresList ? `Key Benefits:\n${featuresList}\n` : ''}
🔗 Link in bio

Ready to get started? Comment below or DM us! 💬`.trim();
  }
}

// Generate hashtags from campaign info
function generateHashtags(data: GenerateMediaRequest): string {
  const { productName, targetAudience } = data;
  
  const productHashtag = '#' + productName.toLowerCase().replace(/[^a-z0-9]/g, '');
  
  // Extract potential hashtags from target audience
  const audienceWords = (targetAudience || '')
    .toLowerCase()
    .split(/[,\s]+/)
    .filter(w => w.length > 3)
    .slice(0, 4)
    .map(w => '#' + w.replace(/[^a-z0-9]/g, ''));

  const defaultHashtags = ['#marketing', '#newproduct', '#musthave', '#trending', '#promo'];
  
  return [productHashtag, ...audienceWords, ...defaultHashtags].slice(0, 10).join(' ');
}

// Generate placeholder image URL (for when AI service is unavailable)
function generatePlaceholderUrl(data: GenerateMediaRequest, index: number = 0): string {
  const { productName, brandVoice } = data;
  
  // Use different color schemes based on brand voice
  let bgColor = '4F46E5'; // Default: indigo
  let textColor = 'FFFFFF';
  
  if (brandVoice === 'casual' || brandVoice === 'playful') {
    const colors = ['FF6B6B', 'FFE66D', '4ECDC4', 'A8E6CF'];
    bgColor = colors[index % colors.length];
    textColor = '333333';
  } else if (brandVoice === 'luxury') {
    bgColor = '1a1a1a';
    textColor = 'D4AF37';
  }

  // Generate a placeholder using a service like placeholder.com or via.placeholder.com
  const encodedName = encodeURIComponent(productName.substring(0, 20));
  return `https://via.placeholder.com/1080x1080/${bgColor}/${textColor}?text=${encodedName}`;
}

// Call OpenAI DALL-E API (when configured)
async function generateWithDALLE(prompt: string): Promise<string | null> {
  const apiKey = process.env.OPENAI_API_KEY;
  
  if (!apiKey) {
    console.log('OpenAI API key not configured, using placeholder');
    return null;
  }

  try {
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'dall-e-3',
        prompt: prompt,
        n: 1,
        size: '1024x1024',
        quality: 'standard',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('DALL-E API error:', error);
      return null;
    }

    const data = await response.json();
    return data.data?.[0]?.url || null;
  } catch (error) {
    console.error('DALL-E generation failed:', error);
    return null;
  }
}

// Call Google Vertex AI Imagen for image generation
async function generateWithVertexAI(prompt: string): Promise<string | null> {
  const projectId = process.env.GOOGLE_CLOUD_PROJECT;
  const location = process.env.GOOGLE_CLOUD_LOCATION || 'us-central1';
  
  // Check if we have Google Cloud credentials
  if (!projectId) {
    console.log('Google Cloud project ID not configured');
    return null;
  }

  console.log('🎨 Attempting Vertex AI Imagen generation...');

  try {
    // Get access token from metadata server or service account
    let accessToken = process.env.GOOGLE_ACCESS_TOKEN;
    
    if (!accessToken) {
      // Try to get token from gcloud CLI (development)
      const { execSync } = require('child_process');
      try {
        accessToken = execSync('gcloud auth print-access-token', { encoding: 'utf8' }).trim();
      } catch {
        console.log('Could not get Google Cloud access token');
        return null;
      }
    }

    const endpoint = `https://${location}-aiplatform.googleapis.com/v1/projects/${projectId}/locations/${location}/publishers/google/models/imagen-3.0-generate-001:predict`;

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        instances: [{ prompt }],
        parameters: {
          sampleCount: 1,
          aspectRatio: '1:1',
          safetyFilterLevel: 'block_few',
        },
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Vertex AI error:', errorText);
      return null;
    }

    const data = await response.json();
    
    // Return base64 image as data URL
    if (data.predictions?.[0]?.bytesBase64Encoded) {
      console.log('✅ Vertex AI image generated successfully');
      return `data:image/png;base64,${data.predictions[0].bytesBase64Encoded}`;
    }
    
    return null;
  } catch (error) {
    console.error('Vertex AI Imagen generation failed:', error);
    return null;
  }
}

// Call Google Gemini/Generative AI for image generation
async function generateWithGemini(prompt: string): Promise<string | null> {
  const apiKey = process.env.GOOGLE_GENAI_API_KEY || process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY;
  
  if (!apiKey) {
    console.log('Google API key not found');
    return null;
  }

  console.log('🎨 Attempting Gemini image generation...');

  try {
    // Try Imagen via Generative Language API
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instances: [{ prompt }],
          parameters: {
            sampleCount: 1,
            aspectRatio: '1:1',
          },
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('Gemini Imagen not available:', errorData.error?.message || response.status);
      return null;
    }

    const data = await response.json();
    // Return base64 image as data URL or hosted URL if available
    if (data.predictions?.[0]?.bytesBase64Encoded) {
      console.log('✅ Gemini image generated successfully');
      return `data:image/png;base64,${data.predictions[0].bytesBase64Encoded}`;
    }
    return null;
  } catch (error) {
    console.error('Gemini image generation failed:', error);
    return null;
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateMediaResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  try {
    const data: GenerateMediaRequest = req.body;

    if (!data.productName || !data.productDescription) {
      return res.status(400).json({
        success: false,
        error: 'Product name and description are required',
      });
    }

    console.log(`🎨 Generating AI media for: ${data.productName}`);
    console.log(`   Post type: ${data.postType}`);

    // Generate caption and hashtags (always works)
    const caption = generateCaption(data);
    const hashtags = generateHashtags(data);

    // Generate image prompt
    const imagePrompt = generateImagePrompt(data);
    console.log(`   Image prompt: ${imagePrompt.substring(0, 100)}...`);

    // Try AI image generation
    let mediaUrl: string | null = null;
    let mediaUrls: string[] = [];
    let isPlaceholder = false;

    // Try AI providers in order: DALL-E → Vertex AI → Gemini
    if (data.postType !== 'video') {
      console.log('   Trying AI image generation providers...');
      
      // Try DALL-E first (OpenAI)
      mediaUrl = await generateWithDALLE(imagePrompt);
      
      // Try Google Vertex AI Imagen
      if (!mediaUrl) {
        mediaUrl = await generateWithVertexAI(imagePrompt);
      }
      
      // Try Gemini API
      if (!mediaUrl) {
        mediaUrl = await generateWithGemini(imagePrompt);
      }
      
      console.log(`   AI generation result: ${mediaUrl ? '✅ Success' : '⚠️ Using placeholder'}`);
    }

    // Handle carousel - generate multiple images
    if (data.postType === 'carousel') {
      if (mediaUrl) {
        // If we got one AI image, use it as first, add placeholders for rest
        mediaUrls = [
          mediaUrl,
          generatePlaceholderUrl(data, 1),
          generatePlaceholderUrl(data, 2),
        ];
      } else {
        // All placeholders
        mediaUrls = [
          generatePlaceholderUrl(data, 0),
          generatePlaceholderUrl(data, 1),
          generatePlaceholderUrl(data, 2),
        ];
        isPlaceholder = true;
      }

      return res.status(200).json({
        success: true,
        mediaUrls,
        caption,
        hashtags,
        isPlaceholder,
      });
    }

    // Single image/video/story
    if (!mediaUrl) {
      mediaUrl = generatePlaceholderUrl(data, 0);
      isPlaceholder = true;
    }

    // For video, return a note that video generation requires additional setup
    if (data.postType === 'video') {
      return res.status(200).json({
        success: true,
        mediaUrl: generatePlaceholderUrl(data, 0),
        caption: caption + '\n\n🎬 [Video content - upload your video file]',
        hashtags,
        isPlaceholder: true,
      });
    }

    console.log(`✅ Media generated: ${isPlaceholder ? 'placeholder' : 'AI-generated'}`);

    return res.status(200).json({
      success: true,
      mediaUrl,
      caption,
      hashtags,
      isPlaceholder,
    });

  } catch (error) {
    console.error('Media generation error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to generate media',
    });
  }
}

/**
 * Google ADK (Genkit) Configuration
 * Integrates Google's Agent Development Kit for AI-powered marketing agents
 * 
 * Latest Gemini Models (as of Feb 2026):
 * - gemini-2.5-flash: Best price-performance, recommended for most use cases (FREE)
 * - gemini-2.5-flash-lite: Fastest, cost-efficient (FREE)
 * - gemini-2.5-pro: Advanced reasoning for complex tasks
 * 
 * Note: Gemini 2.0 and 1.5 models are deprecated (shutdown March 31, 2026)
 */

import { googleAI } from '@genkit-ai/googleai';
import { genkit } from 'genkit';
import { z } from 'zod';

/**
 * Latest Gemini Model Identifiers (Feb 2026)
 * Using string identifiers for maximum flexibility
 */
export const GEMINI_MODELS = {
  // Recommended default - best price-performance, FREE tier available
  FLASH: 'googleai/gemini-2.5-flash',
  // Fastest model - cost-efficient, FREE tier available
  FLASH_LITE: 'googleai/gemini-2.5-flash-lite', 
  // Advanced reasoning - for complex tasks
  PRO: 'googleai/gemini-2.5-pro',
  // Latest aliases (auto-updated by Google)
  LATEST_FLASH: 'googleai/gemini-flash-latest',
} as const;

// Default model - Gemini 2.5 Flash (free, best balance)
export const DEFAULT_MODEL = GEMINI_MODELS.FLASH;

// Initialize Genkit with Google AI plugin
let genkitInstance: ReturnType<typeof genkit> | null = null;
let initializationError: Error | null = null;

/**
 * Initialize Google ADK (Genkit) safely with error handling
 */
export async function initializeGoogleADK(): Promise<{
  success: boolean;
  ai: ReturnType<typeof genkit> | null;
  error?: string;
}> {
  // Return cached instance if already initialized
  if (genkitInstance) {
    return { success: true, ai: genkitInstance };
  }

  // Return cached error if initialization failed before
  if (initializationError) {
    return { 
      success: false, 
      ai: null, 
      error: initializationError.message 
    };
  }

  try {
    // Validate API key exists
    const apiKey = process.env.GOOGLE_GENAI_API_KEY || process.env.GOOGLE_API_KEY;
    
    if (!apiKey) {
      console.warn('⚠️ Google AI API key not found. Set GOOGLE_GENAI_API_KEY in environment.');
      console.warn('   Google ADK features will be disabled.');
      return {
        success: false,
        ai: null,
        error: 'GOOGLE_GENAI_API_KEY not configured'
      };
    }

    // Initialize Genkit with Google AI - using latest Gemini 2.5 Flash
    genkitInstance = genkit({
      plugins: [
        googleAI({
          apiKey: apiKey,
        }),
      ],
      model: DEFAULT_MODEL, // Gemini 2.5 Flash - free and efficient
    });

    console.log('✅ Google ADK (Genkit) initialized with Gemini 2.5 Flash');
    return { success: true, ai: genkitInstance };

  } catch (error) {
    initializationError = error instanceof Error ? error : new Error(String(error));
    console.error('❌ Failed to initialize Google ADK:', initializationError.message);
    return {
      success: false,
      ai: null,
      error: initializationError.message
    };
  }
}

/**
 * Get the Genkit instance (initializes if needed)
 */
export async function getGenkitInstance(): Promise<ReturnType<typeof genkit> | null> {
  const result = await initializeGoogleADK();
  return result.ai;
}

/**
 * Check if Google ADK is available and configured
 */
export function isGoogleADKAvailable(): boolean {
  return !!(process.env.GOOGLE_GENAI_API_KEY || process.env.GOOGLE_API_KEY);
}

/**
 * Google ADK Model configurations
 * Updated to use latest Gemini 2.5 models (FREE tier available)
 */
export const GoogleADKModels = {
  // Fast model for quick responses - Gemini 2.5 Flash (FREE)
  fast: GEMINI_MODELS.FLASH,
  // Ultra-fast model for high throughput - Gemini 2.5 Flash Lite (FREE)
  lite: GEMINI_MODELS.FLASH_LITE,
  // Pro model for complex reasoning tasks
  pro: GEMINI_MODELS.PRO,
  // Latest version (auto-updates)
  latest: GEMINI_MODELS.LATEST_FLASH,
};

// Type for model selection
export type GeminiModelType = typeof GEMINI_MODELS[keyof typeof GEMINI_MODELS];

/**
 * Generate content using Google ADK with safe error handling
 */
export async function generateWithGoogleADK(
  prompt: string,
  options?: {
    model?: GeminiModelType;
    temperature?: number;
    maxTokens?: number;
    systemPrompt?: string;
  }
): Promise<{
  success: boolean;
  content?: string;
  error?: string;
}> {
  try {
    const ai = await getGenkitInstance();
    
    if (!ai) {
      return {
        success: false,
        error: 'Google ADK not initialized. Check API key configuration.'
      };
    }

    const model = options?.model || DEFAULT_MODEL;
    
    const response = await ai.generate({
      model: model,
      prompt: options?.systemPrompt 
        ? `${options.systemPrompt}\n\n${prompt}`
        : prompt,
      config: {
        temperature: options?.temperature ?? 0.7,
        maxOutputTokens: options?.maxTokens ?? 2000,
      },
    });

    return {
      success: true,
      content: response.text,
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('❌ Google ADK generation error:', errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Marketing-specific schema definitions for structured outputs
 */
export const MarketingSchemas = {
  // Email content schema
  emailContent: z.object({
    subjectLine: z.string().describe('Compelling email subject line'),
    preheader: z.string().describe('Email preview text'),
    bodyHtml: z.string().describe('HTML email body content'),
    cta: z.object({
      text: z.string().describe('Call-to-action button text'),
      url: z.string().describe('CTA destination URL'),
    }),
  }),

  // SMS content schema
  smsContent: z.object({
    message: z.string().max(160).describe('SMS message content (max 160 chars)'),
    includeLink: z.boolean().describe('Whether to include a link'),
    urgencyLevel: z.enum(['low', 'medium', 'high']).describe('Message urgency'),
  }),

  // Audience segment schema
  audienceSegment: z.object({
    segmentName: z.string().describe('Name of the audience segment'),
    description: z.string().describe('Segment description'),
    estimatedSize: z.number().describe('Estimated number of contacts'),
    characteristics: z.array(z.string()).describe('Key characteristics'),
    recommendedChannels: z.array(z.string()).describe('Best channels for this segment'),
  }),

  // Compliance check schema
  complianceCheck: z.object({
    passed: z.boolean().describe('Whether compliance check passed'),
    issues: z.array(z.string()).describe('List of compliance issues'),
    recommendations: z.array(z.string()).describe('Compliance recommendations'),
  }),
};

/**
 * Generate structured marketing content using Google ADK
 */
export async function generateStructuredContent<T extends z.ZodType>(
  prompt: string,
  schema: T,
  options?: {
    model?: GeminiModelType;
    systemPrompt?: string;
  }
): Promise<{
  success: boolean;
  data?: z.infer<T>;
  error?: string;
}> {
  try {
    const ai = await getGenkitInstance();
    
    if (!ai) {
      return {
        success: false,
        error: 'Google ADK not initialized'
      };
    }

    const response = await ai.generate({
      model: options?.model || DEFAULT_MODEL,
      prompt: options?.systemPrompt 
        ? `${options.systemPrompt}\n\n${prompt}`
        : prompt,
      output: { schema },
    });

    return {
      success: true,
      data: response.output,
    };

  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export default {
  initializeGoogleADK,
  getGenkitInstance,
  isGoogleADKAvailable,
  generateWithGoogleADK,
  generateStructuredContent,
  GoogleADKModels,
  MarketingSchemas,
  GEMINI_MODELS,
  DEFAULT_MODEL,
};

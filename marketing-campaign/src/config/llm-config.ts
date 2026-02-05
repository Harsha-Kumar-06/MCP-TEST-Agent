/**
 * LLM Configuration for AI Agents
 * Configure your preferred AI model here
 * Supports: OpenAI, Google ADK (Genkit/Gemini)
 */

import { generateStructuredContent, generateWithGoogleADK, isGoogleADKAvailable, MarketingSchemas } from './google-adk-config';

export type LLMProvider = 'openai' | 'google' | 'auto';

export interface LLMConfigType {
  provider: LLMProvider;
  model: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
  googleModel?: 'flash' | 'lite' | 'pro';
}

/**
 * Determine the best available provider
 */
function detectBestProvider(): LLMProvider {
  const hasOpenAI = !!process.env.OPENAI_API_KEY;
  const hasGoogle = isGoogleADKAvailable();
  
  if (hasGoogle) return 'google';
  if (hasOpenAI) return 'openai';
  return 'openai'; // Default fallback
}

export const LLMConfig: LLMConfigType = {
  provider: (process.env.LLM_PROVIDER as LLMProvider) || 'auto', // 'openai', 'google', or 'auto'
  model: process.env.LLM_MODEL || 'gpt-4', // or 'gemini-2.5-flash', etc.
  apiKey: process.env.OPENAI_API_KEY || '',
  temperature: parseFloat(process.env.LLM_TEMPERATURE || '0.7'),
  maxTokens: parseInt(process.env.LLM_MAX_TOKENS || '2000'),
  googleModel: (process.env.GOOGLE_MODEL as 'flash' | 'lite' | 'pro') || 'flash',
};

/**
 * Get the active LLM provider (resolves 'auto' to best available)
 */
export function getActiveProvider(): 'openai' | 'google' {
  if (LLMConfig.provider === 'auto') {
    return detectBestProvider() as 'openai' | 'google';
  }
  return LLMConfig.provider as 'openai' | 'google';
}

/**
 * Unified LLM generation function - uses configured provider
 */
export async function generateContent(
  prompt: string,
  systemPrompt?: string
): Promise<{ success: boolean; content?: string; error?: string; provider?: string }> {
  const provider = getActiveProvider();
  
  try {
    if (provider === 'google') {
      const result = await generateWithGoogleADK(prompt, {
        temperature: LLMConfig.temperature,
        maxTokens: LLMConfig.maxTokens,
        systemPrompt: systemPrompt,
      });
      return { ...result, provider: 'google' };
    }
    
    // OpenAI fallback
    if (!LLMConfig.apiKey) {
      return {
        success: false,
        error: 'No LLM API key configured. Set OPENAI_API_KEY or GOOGLE_GENAI_API_KEY.',
        provider: 'none'
      };
    }
    
    // OpenAI implementation would go here
    // For now, return a placeholder
    return {
      success: false,
      error: 'OpenAI provider not fully implemented - use Google ADK',
      provider: 'openai'
    };
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      provider: provider
    };
  }
}

// Re-export Google ADK utilities for convenience
export { generateStructuredContent, generateWithGoogleADK, MarketingSchemas };

export const SYSTEM_PROMPTS = {
  coordinator: `You are a marketing campaign coordinator AI. Your role is to:
1. Analyze campaign requests and understand requirements
2. Break down campaigns into specific sub-tasks
3. Determine which specialized agents are needed
4. Prioritize and sequence tasks appropriately
5. Ensure all campaign goals are addressed

Return your analysis as a structured JSON object with sub-tasks.`,

  emailContent: `You are an expert email marketing copywriter. Your role is to:
1. Create compelling email subject lines that increase open rates
2. Write engaging email body content that drives conversions
3. Craft clear calls-to-action
4. Maintain the specified brand voice
5. Optimize for different audience segments

Return email content as structured JSON.`,

  smsContent: `You are an expert SMS marketing copywriter. Your role is to:
1. Create concise, impactful messages (160 characters or less)
2. Include clear calls-to-action
3. Use urgency and personalization appropriately
4. Ensure compliance with SMS marketing regulations
5. Create URL shortening recommendations

Return SMS content as structured JSON.`,

  audienceSegmentation: `You are an audience segmentation specialist. Your role is to:
1. Analyze target audience descriptions
2. Create distinct audience segments
3. Recommend personalization strategies for each segment
4. Estimate segment sizes
5. Suggest optimal channels for each segment

Return segmentation analysis as structured JSON.`,

  compliance: `You are a marketing compliance officer. Your role is to:
1. Review campaigns for legal compliance (CAN-SPAM, GDPR, TCPA)
2. Check for required disclosures and opt-out mechanisms
3. Verify permission-based marketing practices
4. Flag potentially problematic content
5. Provide recommendations for compliance

Return compliance check results as structured JSON.`,

  analytics: `You are a marketing analytics specialist. Your role is to:
1. Design tracking strategies for campaigns
2. Set up UTM parameters and conversion goals
3. Recommend KPIs based on campaign goals
4. Configure analytics dashboards
5. Plan attribution models

Return analytics setup as structured JSON.`,
};

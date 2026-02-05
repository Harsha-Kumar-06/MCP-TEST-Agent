/**
 * Safe Initialization Module
 * Handles startup of all services with crash protection
 */

import * as dotenv from 'dotenv';

// Load environment variables first
dotenv.config();

import { initializeGoogleADK, isGoogleADKAvailable } from './google-adk-config';
import { getActiveProvider } from './llm-config';

export interface InitializationResult {
  success: boolean;
  services: {
    googleADK: { available: boolean; initialized: boolean; error?: string };
    openAI: { available: boolean; configured: boolean };
    email: { configured: boolean };
    sms: { configured: boolean };
    instagram: { configured: boolean };
  };
  errors: string[];
  warnings: string[];
}

/**
 * Initialize all services safely with comprehensive error handling
 */
export async function initializeServices(): Promise<InitializationResult> {
  const result: InitializationResult = {
    success: true,
    services: {
      googleADK: { available: false, initialized: false },
      openAI: { available: false, configured: false },
      email: { configured: false },
      sms: { configured: false },
      instagram: { configured: false },
    },
    errors: [],
    warnings: [],
  };

  console.log('\n🔧 Initializing Marketing Campaign Agent Services...');
  console.log('─'.repeat(60));

  // 1. Initialize Google ADK (Genkit)
  try {
    result.services.googleADK.available = isGoogleADKAvailable();
    
    if (result.services.googleADK.available) {
      const adkResult = await initializeGoogleADK();
      result.services.googleADK.initialized = adkResult.success;
      if (!adkResult.success) {
        result.services.googleADK.error = adkResult.error;
        result.warnings.push(`Google ADK available but failed to initialize: ${adkResult.error}`);
      } else {
        console.log('✅ Google ADK (Genkit) initialized');
      }
    } else {
      console.log('ℹ️  Google ADK not configured (set GOOGLE_GENAI_API_KEY to enable)');
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    result.services.googleADK.error = errorMsg;
    result.warnings.push(`Google ADK initialization error: ${errorMsg}`);
    console.warn('⚠️ Google ADK error (non-fatal):', errorMsg);
  }

  // 2. Check OpenAI configuration
  try {
    result.services.openAI.available = !!process.env.OPENAI_API_KEY;
    result.services.openAI.configured = result.services.openAI.available;
    
    if (result.services.openAI.configured) {
      console.log('✅ OpenAI configured');
    } else {
      console.log('ℹ️  OpenAI not configured (set OPENAI_API_KEY to enable)');
    }
  } catch (error) {
    result.warnings.push(`OpenAI check error: ${error instanceof Error ? error.message : String(error)}`);
  }

  // 3. Check Email (Nodemailer) configuration
  try {
    result.services.email.configured = !!(
      process.env.GMAIL_USER && 
      process.env.GMAIL_APP_PASSWORD
    );
    
    if (result.services.email.configured) {
      console.log('✅ Email service configured');
    } else {
      console.log('ℹ️  Email not configured (set GMAIL_USER and GMAIL_APP_PASSWORD)');
    }
  } catch (error) {
    result.warnings.push(`Email check error: ${error instanceof Error ? error.message : String(error)}`);
  }

  // 4. Check SMS (Twilio) configuration
  try {
    result.services.sms.configured = !!(
      process.env.TWILIO_ACCOUNT_SID && 
      process.env.TWILIO_AUTH_TOKEN &&
      process.env.TWILIO_PHONE_NUMBER
    );
    
    if (result.services.sms.configured) {
      console.log('✅ SMS service configured');
    } else {
      console.log('ℹ️  SMS not configured (set TWILIO_* environment variables)');
    }
  } catch (error) {
    result.warnings.push(`SMS check error: ${error instanceof Error ? error.message : String(error)}`);
  }

  // 5. Check Instagram configuration
  try {
    result.services.instagram.configured = !!(
      process.env.INSTAGRAM_ACCESS_TOKEN && 
      process.env.INSTAGRAM_USER_ID
    );
    
    if (result.services.instagram.configured) {
      console.log('✅ Instagram service configured');
    } else {
      console.log('ℹ️  Instagram not configured (set INSTAGRAM_* environment variables)');
    }
  } catch (error) {
    result.warnings.push(`Instagram check error: ${error instanceof Error ? error.message : String(error)}`);
  }

  // Determine overall success - at least one LLM provider should be available
  const hasLLM = result.services.googleADK.initialized || result.services.openAI.configured;
  
  if (!hasLLM) {
    result.errors.push('No LLM provider available. Configure GOOGLE_GENAI_API_KEY or OPENAI_API_KEY.');
    result.success = false;
  }

  console.log('─'.repeat(60));
  
  if (result.success) {
    const activeProvider = getActiveProvider();
    console.log(`✅ Initialization complete. Active LLM provider: ${activeProvider.toUpperCase()}`);
  } else {
    console.error('❌ Initialization failed with errors:');
    result.errors.forEach(e => console.error(`   • ${e}`));
  }

  if (result.warnings.length > 0) {
    console.log('\n⚠️ Warnings:');
    result.warnings.forEach(w => console.warn(`   • ${w}`));
  }

  console.log('');
  return result;
}

/**
 * Check if the system is ready to run campaigns
 */
export function isSystemReady(initResult: InitializationResult): boolean {
  return initResult.success && initResult.errors.length === 0;
}

/**
 * Get a summary of available features based on initialization
 */
export function getAvailableFeatures(initResult: InitializationResult): string[] {
  const features: string[] = [];
  
  if (initResult.services.googleADK.initialized) {
    features.push('AI Content Generation (Google Gemini)');
    features.push('Structured Output Generation');
  }
  
  if (initResult.services.openAI.configured) {
    features.push('AI Content Generation (OpenAI)');
  }
  
  if (initResult.services.email.configured) {
    features.push('Email Campaign Sending');
  }
  
  if (initResult.services.sms.configured) {
    features.push('SMS Campaign Sending');
  }
  
  if (initResult.services.instagram.configured) {
    features.push('Instagram Posting');
  }
  
  // Always available (template-based)
  features.push('Campaign Planning');
  features.push('Audience Segmentation');
  features.push('Compliance Checking');
  features.push('Analytics Setup');
  
  return features;
}

export default {
  initializeServices,
  isSystemReady,
  getAvailableFeatures,
};

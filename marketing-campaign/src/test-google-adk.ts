/**
 * Test Script for Google ADK Integration
 * Run with: npx ts-node src/test-google-adk.ts
 */

import * as dotenv from 'dotenv';
dotenv.config();

import {
    generateWithGoogleADK,
    initializeGoogleADK,
    isGoogleADKAvailable
} from './config/google-adk-config';

async function testGoogleADK() {
  console.log('\n' + '='.repeat(60));
  console.log('🧪 GOOGLE ADK (GENKIT) TEST');
  console.log('='.repeat(60));

  // Test 1: Check if API key is available
  console.log('\n📋 Test 1: API Key Check');
  const hasKey = isGoogleADKAvailable();
  console.log(`   API Key Present: ${hasKey ? '✅ Yes' : '❌ No'}`);
  
  if (!hasKey) {
    console.error('\n❌ GOOGLE_GENAI_API_KEY not found in environment!');
    process.exit(1);
  }

  // Test 2: Initialize Genkit
  console.log('\n📋 Test 2: Initialize Google ADK');
  const initResult = await initializeGoogleADK();
  console.log(`   Initialization: ${initResult.success ? '✅ Success' : '❌ Failed'}`);
  
  if (!initResult.success) {
    console.error(`   Error: ${initResult.error}`);
    process.exit(1);
  }

  // Test 3: Simple text generation
  console.log('\n📋 Test 3: Simple Text Generation');
  console.log('   Prompt: "Write a one-sentence marketing tagline for a coffee shop"');
  
  const simpleResult = await generateWithGoogleADK(
    'Write a one-sentence marketing tagline for a coffee shop called "Morning Brew". Be creative and catchy.'
  );
  
  if (simpleResult.success) {
    console.log(`   ✅ Response: ${simpleResult.content}`);
  } else {
    console.log(`   ❌ Error: ${simpleResult.error}`);
  }

  // Test 4: Marketing email generation
  console.log('\n📋 Test 4: Marketing Email Generation');
  console.log('   Generating email content for a product launch...');
  
  const emailResult = await generateWithGoogleADK(
    `Generate a marketing email for a new fitness app launch.
    Product: FitTrack Pro
    Target: Health-conscious professionals aged 25-45
    
    Return a JSON object with:
    - subjectLine: compelling email subject
    - preheader: preview text (50 chars)
    - bodyText: brief email body (100 words max)
    - cta: call to action text`,
    {
      systemPrompt: 'You are an expert marketing copywriter. Return only valid JSON.',
      temperature: 0.8
    }
  );
  
  if (emailResult.success) {
    console.log('   ✅ Email Content Generated:');
    console.log('   ' + '-'.repeat(50));
    console.log(`   ${emailResult.content?.substring(0, 500)}...`);
  } else {
    console.log(`   ❌ Error: ${emailResult.error}`);
  }

  // Test 5: SMS content generation
  console.log('\n📋 Test 5: SMS Content (160 char limit)');
  
  const smsResult = await generateWithGoogleADK(
    'Write a promotional SMS message (max 160 characters) for a 20% off flash sale at an online clothing store. Include urgency.',
    { maxTokens: 100 }
  );
  
  if (smsResult.success) {
    const smsContent = smsResult.content || '';
    console.log(`   ✅ SMS (${smsContent.length} chars): ${smsContent}`);
  } else {
    console.log(`   ❌ Error: ${smsResult.error}`);
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`   Model Used: Gemini 2.5 Flash (Free Tier)`);
  console.log(`   API Key: ${process.env.GOOGLE_GENAI_API_KEY?.substring(0, 10)}...`);
  console.log(`   All Tests: ${simpleResult.success && emailResult.success && smsResult.success ? '✅ PASSED' : '⚠️ SOME FAILED'}`);
  console.log('='.repeat(60) + '\n');
}

// Run the test
testGoogleADK().catch(console.error);

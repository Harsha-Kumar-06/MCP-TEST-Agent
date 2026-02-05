/**
 * Simple Google Gemini API Test
 * Run with: node src/simple-gemini-test.js
 */

require('dotenv').config();

const { GoogleGenerativeAI } = require('@google/generative-ai');

async function testGemini() {
  console.log('\n' + '='.repeat(60));
  console.log('🧪 GOOGLE GEMINI API TEST');
  console.log('='.repeat(60));

  const apiKey = process.env.GOOGLE_GENAI_API_KEY;
  
  console.log('\n📋 Test 1: API Key Check');
  console.log('   API Key Present:', apiKey ? '✅ Yes' : '❌ No');
  
  if (!apiKey) {
    console.error('\n❌ GOOGLE_GENAI_API_KEY not found!');
    process.exit(1);
  }

  try {
    console.log('\n📋 Test 2: Initialize Google AI');
    const genAI = new GoogleGenerativeAI(apiKey);
    // Use gemini-2.5-flash - the CORRECT model name (free tier)
    const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });
    console.log('   ✅ Model initialized: gemini-2.5-flash (FREE)');

    console.log('\n📋 Test 3: Generate Marketing Tagline');
    const result1 = await model.generateContent(
      'Write a one-sentence marketing tagline for a coffee shop called "Morning Brew". Just the tagline, nothing else.'
    );
    console.log('   ✅ Tagline:', result1.response.text().trim());

    console.log('\n📋 Test 4: Generate Email Subject Lines');
    const result2 = await model.generateContent(
      'Generate 3 email subject lines for a fitness app launch. Format: numbered list, one per line.'
    );
    console.log('   ✅ Subject Lines:\n', result2.response.text());

    console.log('\n📋 Test 5: Generate SMS (160 chars)');
    const result3 = await model.generateContent(
      'Write ONE promotional SMS under 160 characters for a 20% off flash sale. Include urgency.'
    );
    const sms = result3.response.text().trim();
    console.log('   ✅ SMS (' + sms.length + ' chars):', sms);

    console.log('\n' + '='.repeat(60));
    console.log('✅ ALL TESTS PASSED - Google Gemini API is working!');
    console.log('='.repeat(60) + '\n');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

testGemini();

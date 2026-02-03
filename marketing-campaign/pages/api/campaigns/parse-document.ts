import formidable from 'formidable';
import fs from 'fs';
import mammoth from 'mammoth';
import { NextApiRequest, NextApiResponse } from 'next';
const pdfParse = require('pdf-parse');

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const form = formidable({ multiples: false });

    form.parse(req, async (err, fields, files) => {
      if (err) {
        return res.status(500).json({ success: false, error: 'Failed to parse upload' });
      }

      const file = Array.isArray(files.document) ? files.document[0] : files.document;
      
      if (!file) {
        return res.status(400).json({ success: false, error: 'No document uploaded' });
      }

      try {
        let text = '';
        const filepath = file.filepath;
        const filename = file.originalFilename || '';

        // Parse based on file type
        if (filename.endsWith('.pdf')) {
          const dataBuffer = fs.readFileSync(filepath);
          const pdfData = await pdfParse(dataBuffer);
          text = pdfData.text;
        } else if (filename.endsWith('.docx')) {
          const result = await mammoth.extractRawText({ path: filepath });
          text = result.value;
        } else if (filename.endsWith('.txt')) {
          text = fs.readFileSync(filepath, 'utf-8');
        } else {
          return res.status(400).json({ 
            success: false, 
            error: 'Unsupported file type. Use PDF, DOCX, or TXT' 
          });
        }

        // Clean up uploaded file
        fs.unlinkSync(filepath);

        // Parse campaign details from text
        const campaignData = parseCampaignDetails(text);

        res.status(200).json({ 
          success: true, 
          data: campaignData,
          extractedText: text.substring(0, 500) + '...' // First 500 chars for preview
        });

      } catch (error) {
        console.error('Document parsing error:', error);
        return res.status(500).json({ 
          success: false, 
          error: 'Failed to parse document content' 
        });
      }
    });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to process document' 
    });
  }
}

/**
 * Parse campaign details from unstructured text
 * Uses pattern matching and keyword extraction
 */
function parseCampaignDetails(text: string): any {
  const lowerText = text.toLowerCase();
  
  // Extract campaign name
  const campaignName = extractField(text, [
    /campaign\s*name\s*[:=]\s*(.+?)(?:\n|$)/i,
    /campaign\s*title\s*[:=]\s*(.+?)(?:\n|$)/i,
    /name\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || 'Imported Campaign';

  // Extract product name
  const productName = extractField(text, [
    /product\s*name\s*[:=]\s*(.+?)(?:\n|$)/i,
    /product\s*[:=]\s*(.+?)(?:\n|$)/i,
    /service\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || '';

  // Extract product description
  const productDescription = extractField(text, [
    /description\s*[:=]\s*(.+?)(?:\n\n|features|pricing|target|$)/is,
    /about\s*[:=]\s*(.+?)(?:\n\n|features|pricing|target|$)/is,
    /overview\s*[:=]\s*(.+?)(?:\n\n|features|pricing|target|$)/is,
  ]) || '';

  // Extract features
  const featuresText = extractField(text, [
    /features?\s*[:=]\s*(.+?)(?:\n\n|pricing|target|benefits|$)/is,
    /benefits?\s*[:=]\s*(.+?)(?:\n\n|pricing|target|features|$)/is,
    /capabilities\s*[:=]\s*(.+?)(?:\n\n|pricing|target|$)/is,
  ]) || '';
  
  const features = featuresText
    .split(/\n|•|-|\*/)
    .map(f => f.trim())
    .filter(f => f.length > 5 && f.length < 200)
    .slice(0, 5)
    .join('\n');

  // Extract pricing
  const pricing = extractField(text, [
    /pricing\s*[:=]\s*(.+?)(?:\n|$)/i,
    /price\s*[:=]\s*(.+?)(?:\n|$)/i,
    /cost\s*[:=]\s*(.+?)(?:\n|$)/i,
    /\$\d+[\d,]*(?:\/\w+)?/,
  ]) || '';

  // Extract target audience/demographics
  const targetDemographics = extractField(text, [
    /target\s*audience\s*[:=]\s*(.+?)(?:\n|$)/i,
    /demographics\s*[:=]\s*(.+?)(?:\n|$)/i,
    /audience\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || '';

  // Extract interests
  const targetInterests = extractField(text, [
    /interests?\s*[:=]\s*(.+?)(?:\n|$)/i,
    /topics?\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || '';

  // Extract pain points
  const painPoints = extractField(text, [
    /pain\s*points?\s*[:=]\s*(.+?)(?:\n|$)/i,
    /challenges?\s*[:=]\s*(.+?)(?:\n|$)/i,
    /problems?\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || '';

  // Extract budget
  const budgetMatch = text.match(/budget\s*[:=]?\s*\$?([\d,]+)/i);
  const budget = budgetMatch ? budgetMatch[1].replace(/,/g, '') : '';

  // Extract dates
  const startDate = extractField(text, [
    /start\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})/i,
    /launch\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})/i,
  ]) || '';

  const endDate = extractField(text, [
    /end\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})/i,
    /finish\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})/i,
  ]) || '';

  // Extract goals
  const goalsText = extractField(text, [
    /goals?\s*[:=]\s*(.+?)(?:\n\n|objectives|budget|$)/is,
    /objectives?\s*[:=]\s*(.+?)(?:\n\n|goals|budget|$)/is,
  ]) || '';
  
  const goals = goalsText
    .split(/\n|•|-|\*/)
    .map(g => g.trim())
    .filter(g => g.length > 5 && g.length < 200)
    .slice(0, 3)
    .join('\n');

  // Detect channels
  const channels: string[] = [];
  if (lowerText.includes('email')) channels.push('email');
  if (lowerText.includes('sms') || lowerText.includes('text message')) channels.push('sms');
  if (lowerText.includes('instagram')) channels.push('instagram');
  
  // Default to email if no channels detected
  if (channels.length === 0) channels.push('email');

  // Extract contact info
  const companyName = extractField(text, [
    /company\s*name\s*[:=]\s*(.+?)(?:\n|$)/i,
    /organization\s*[:=]\s*(.+?)(?:\n|$)/i,
  ]) || '';

  const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/);
  const replyToEmail = emailMatch ? emailMatch[0] : '';

  const phoneMatch = text.match(/(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})/);
  const companyPhone = phoneMatch ? phoneMatch[0] : '';

  const websiteMatch = text.match(/https?:\/\/[\w.-]+\.\w+[\w./-]*/);
  const companyWebsite = websiteMatch ? websiteMatch[0] : '';

  return {
    campaignName,
    channels,
    productName,
    productDescription,
    features,
    pricing,
    targetDemographics,
    targetInterests,
    painPoints,
    budget,
    startDate,
    endDate,
    goals,
    companyName,
    replyToEmail,
    companyPhone,
    companyWebsite,
  };
}

/**
 * Extract field using multiple regex patterns
 */
function extractField(text: string, patterns: RegExp[]): string | null {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  return null;
}

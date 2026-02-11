import formidable from 'formidable';
import fs from 'fs';
import { NextApiRequest, NextApiResponse } from 'next';
import { contactDB } from '../../../src/database/contact-database';

export const config = {
  api: {
    bodyParser: false,
    responseLimit: false, // Allow large responses
  },
};

// Increase max listeners to prevent warning with large uploads
process.setMaxListeners(20);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const form = formidable({
      maxFileSize: 50 * 1024 * 1024, // 50MB max file size
    });
    const [fields, files] = await form.parse(req);

    const csvFile = files.file?.[0];
    const listName = fields.listName?.[0] || 'Imported List';

    if (!csvFile) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // Read CSV content
    const csvContent = fs.readFileSync(csvFile.filepath, 'utf-8');
    
    // Quick validation - count lines for progress estimation
    const lineCount = csvContent.split('\n').filter(line => line.trim()).length;
    const estimatedContacts = Math.max(0, lineCount - 1); // Subtract header
    
    if (estimatedContacts > 10000) {
      return res.status(400).json({ 
        error: 'File too large. Maximum 10,000 contacts per upload.',
        contactCount: estimatedContacts
      });
    }

    // Import contacts (batched processing happens inside the function)
    const list = await contactDB.importFromCSV(csvContent, listName);
    const duplicatesSkipped = (list as any).duplicatesSkipped || 0;

    // Clean up temp file
    try {
      fs.unlinkSync(csvFile.filepath);
    } catch (e) {
      // Ignore cleanup errors
    }

    const message = duplicatesSkipped > 0
      ? `Successfully imported ${list.contacts.length} contacts (${duplicatesSkipped} duplicates skipped)`
      : `Successfully imported ${list.contacts.length} contacts`;

    res.status(200).json({ 
      success: true, 
      data: {
        id: list.id,
        name: list.name,
        description: list.description,
        contactCount: list.contacts.length,
        duplicatesSkipped,
        // Don't return all contacts for large lists to reduce response size
        contacts: list.contacts.length > 100 ? list.contacts.slice(0, 100) : list.contacts,
        hasMore: list.contacts.length > 100,
      },
      message
    });
  } catch (error) {
    console.error('CSV import error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to import CSV' 
    });
  }
}

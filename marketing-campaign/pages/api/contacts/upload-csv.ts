import formidable from 'formidable';
import fs from 'fs';
import { NextApiRequest, NextApiResponse } from 'next';
import { contactDB } from '../../../src/database/contact-database';

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
    const form = formidable({});
    const [fields, files] = await form.parse(req);

    const csvFile = files.file?.[0];
    const listName = fields.listName?.[0] || 'Imported List';

    if (!csvFile) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // Read CSV content
    const csvContent = fs.readFileSync(csvFile.filepath, 'utf-8');

    // Import contacts
    const list = await contactDB.importFromCSV(csvContent, listName);

    res.status(200).json({ 
      success: true, 
      data: list,
      message: `Imported ${list.contacts.length} contacts`
    });
  } catch (error) {
    console.error('CSV import error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to import CSV' 
    });
  }
}

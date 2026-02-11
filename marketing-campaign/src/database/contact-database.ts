import * as fs from 'fs';
import * as path from 'path';
import { Contact, ContactList } from '../types/database';

/**
 * Simple file-based database for contacts
 * In production, replace with PostgreSQL, MongoDB, etc.
 */

const DATA_DIR = path.join(process.cwd(), 'data');
const CONTACTS_FILE = path.join(DATA_DIR, 'contacts.json');
const LISTS_FILE = path.join(DATA_DIR, 'contact-lists.json');

export class ContactDatabase {
  constructor() {
    this.ensureDataDirectory();
  }

  private ensureDataDirectory(): void {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(CONTACTS_FILE)) {
      fs.writeFileSync(CONTACTS_FILE, JSON.stringify([], null, 2));
    }
    if (!fs.existsSync(LISTS_FILE)) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify([], null, 2));
    }
  }

  // Contacts
  async getAllContacts(): Promise<Contact[]> {
    const data = fs.readFileSync(CONTACTS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getContactById(id: string): Promise<Contact | null> {
    const contacts = await this.getAllContacts();
    return contacts.find(c => c.id === id) || null;
  }

  async createContact(contact: Omit<Contact, 'id' | 'createdAt' | 'updatedAt'>): Promise<Contact> {
    const contacts = await this.getAllContacts();
    
    // Check for duplicates by email or phone
    const email = contact.email?.toLowerCase();
    const phone = contact.phone?.replace(/\D/g, '');
    
    if (email) {
      const existingByEmail = contacts.find(c => c.email?.toLowerCase() === email);
      if (existingByEmail) {
        throw new Error(`A contact with email "${contact.email}" already exists`);
      }
    }
    
    if (phone) {
      const existingByPhone = contacts.find(c => c.phone?.replace(/\D/g, '') === phone);
      if (existingByPhone) {
        throw new Error(`A contact with phone "${contact.phone}" already exists`);
      }
    }
    
    const newContact: Contact = {
      ...contact,
      id: `contact-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    contacts.push(newContact);
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2));
    return newContact;
  }

  async updateContact(id: string, updates: Partial<Contact>): Promise<Contact | null> {
    const contacts = await this.getAllContacts();
    const index = contacts.findIndex(c => c.id === id);
    if (index === -1) return null;

    // Check for duplicates if email or phone is being updated
    if (updates.email) {
      const email = updates.email.toLowerCase();
      const existingByEmail = contacts.find(c => c.id !== id && c.email?.toLowerCase() === email);
      if (existingByEmail) {
        throw new Error(`A contact with email "${updates.email}" already exists`);
      }
    }
    
    if (updates.phone) {
      const phone = updates.phone.replace(/\D/g, '');
      const existingByPhone = contacts.find(c => c.id !== id && c.phone?.replace(/\D/g, '') === phone);
      if (existingByPhone) {
        throw new Error(`A contact with phone "${updates.phone}" already exists`);
      }
    }

    contacts[index] = {
      ...contacts[index],
      ...updates,
      updatedAt: new Date(),
    };
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2));
    
    // Sync update to contact lists
    const lists = await this.getAllLists();
    let listsUpdated = false;
    for (const list of lists) {
      const contactIndex = list.contacts.findIndex(c => c.id === id);
      if (contactIndex !== -1) {
        list.contacts[contactIndex] = contacts[index];
        list.updatedAt = new Date();
        listsUpdated = true;
      }
    }
    if (listsUpdated) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    }
    
    return contacts[index];
  }

  async deleteContact(id: string): Promise<boolean> {
    const contacts = await this.getAllContacts();
    const filtered = contacts.filter(c => c.id !== id);
    if (filtered.length === contacts.length) return false;
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(filtered, null, 2));
    
    // Remove contact from all lists
    const lists = await this.getAllLists();
    let listsUpdated = false;
    for (const list of lists) {
      const originalLength = list.contacts.length;
      list.contacts = list.contacts.filter(c => c.id !== id);
      if (list.contacts.length !== originalLength) {
        list.updatedAt = new Date();
        listsUpdated = true;
      }
    }
    if (listsUpdated) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    }
    
    return true;
  }

  // Contact Lists
  async getAllLists(): Promise<ContactList[]> {
    const data = fs.readFileSync(LISTS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getListById(id: string): Promise<ContactList | null> {
    const lists = await this.getAllLists();
    return lists.find(l => l.id === id) || null;
  }

  async createList(list: Omit<ContactList, 'id' | 'createdAt' | 'updatedAt'>): Promise<ContactList> {
    const lists = await this.getAllLists();
    const newList: ContactList = {
      ...list,
      id: `list-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    lists.push(newList);
    fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    return newList;
  }

  async updateList(id: string, updates: Partial<ContactList>): Promise<ContactList | null> {
    const lists = await this.getAllLists();
    const index = lists.findIndex(l => l.id === id);
    if (index === -1) return null;

    lists[index] = {
      ...lists[index],
      ...updates,
      updatedAt: new Date(),
    };
    fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    return lists[index];
  }

  async deleteList(id: string, deleteContacts: boolean = true): Promise<{ deleted: boolean; contactsDeleted: number }> {
    const lists = await this.getAllLists();
    const listToDelete = lists.find(l => l.id === id);
    if (!listToDelete) return { deleted: false, contactsDeleted: 0 };

    let contactsDeleted = 0;

    // Delete all contacts in this list from the main contacts file
    if (deleteContacts && listToDelete.contacts.length > 0) {
      const allContacts = await this.getAllContacts();
      const contactIdsToDelete = new Set(listToDelete.contacts.map(c => c.id));
      const remainingContacts = allContacts.filter(c => !contactIdsToDelete.has(c.id));
      contactsDeleted = allContacts.length - remainingContacts.length;
      fs.writeFileSync(CONTACTS_FILE, JSON.stringify(remainingContacts, null, 2));
    }

    // Delete the list
    const filtered = lists.filter(l => l.id !== id);
    fs.writeFileSync(LISTS_FILE, JSON.stringify(filtered, null, 2));
    
    return { deleted: true, contactsDeleted };
  }

  async deleteAllLists(deleteContacts: boolean = true): Promise<{ listsDeleted: number; contactsDeleted: number }> {
    const lists = await this.getAllLists();
    if (lists.length === 0) return { listsDeleted: 0, contactsDeleted: 0 };

    let contactsDeleted = 0;

    if (deleteContacts) {
      // Collect all contact IDs from all lists
      const contactIdsToDelete = new Set<string>();
      for (const list of lists) {
        for (const contact of list.contacts) {
          contactIdsToDelete.add(contact.id);
        }
      }

      // Remove these contacts from the main contacts file
      const allContacts = await this.getAllContacts();
      const remainingContacts = allContacts.filter(c => !contactIdsToDelete.has(c.id));
      contactsDeleted = allContacts.length - remainingContacts.length;
      fs.writeFileSync(CONTACTS_FILE, JSON.stringify(remainingContacts, null, 2));
    }

    // Clear all lists
    fs.writeFileSync(LISTS_FILE, JSON.stringify([], null, 2));
    
    return { listsDeleted: lists.length, contactsDeleted };
  }

  // CSV Import - supports multiple emails per row (semicolon or pipe separated)
  async importFromCSV(csvContent: string, listName: string): Promise<ContactList> {
    const lines = csvContent.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
      throw new Error('CSV file is empty');
    }
    
    // Parse CSV properly handling quoted fields with commas
    const parseCSVLine = (line: string): string[] => {
      const result: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      return result;
    };
    
    const headers = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase());
    
    const contacts: Contact[] = [];
    const contactsToCreate: Omit<Contact, 'id' | 'createdAt' | 'updatedAt'>[] = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = parseCSVLine(lines[i]);
      const row: any = {};
      
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });

      const emailField = row.email || '';
      const phoneField = row.phone || '';
      const firstName = row.firstname || row.first_name || '';
      const lastName = row.lastname || row.last_name || '';
      const company = row.company || '';
      const tags = row.tags ? row.tags.split(';').map((t: string) => t.trim()).filter((t: string) => t) : [];
      const optInEmail = row.optin_email !== 'false' && row.optin_email !== '0';
      const optInSMS = row.optin_sms !== 'false' && row.optin_sms !== '0';

      // Handle multiple emails (semicolon, pipe, or space separated)
      const emails = emailField
        .split(/[;|,\s]+/)
        .map((e: string) => e.trim())
        .filter((e: string) => e && e.includes('@'));

      // Handle multiple phones (semicolon or pipe separated)
      const phones = phoneField
        .split(/[;|]+/)
        .map((p: string) => p.trim())
        .filter((p: string) => p);

      if (emails.length === 0 && phones.length === 0) {
        // Skip rows without any contact info
        continue;
      }

      // If multiple emails, create one contact per email
      if (emails.length > 1) {
        for (let j = 0; j < emails.length; j++) {
          contactsToCreate.push({
            email: emails[j],
            phone: phones[j] || phones[0] || undefined, // Use corresponding phone or first phone
            firstName: firstName || undefined,
            lastName: lastName || undefined,
            company: company || undefined,
            tags: [...tags, `multi-email-row-${i}`], // Tag to identify split contacts
            optInEmail,
            optInSMS,
          });
        }
      } else {
        // Single email or no email (phone only)
        contactsToCreate.push({
          email: emails[0] || undefined,
          phone: phones[0] || undefined,
          firstName: firstName || undefined,
          lastName: lastName || undefined,
          company: company || undefined,
          tags,
          optInEmail,
          optInSMS,
        });
      }
    }

    // Batch create contacts to improve performance
    const BATCH_SIZE = 100;
    let duplicatesSkipped = 0;
    for (let i = 0; i < contactsToCreate.length; i += BATCH_SIZE) {
      const batch = contactsToCreate.slice(i, i + BATCH_SIZE);
      const result = await this.createContactsBatch(batch);
      contacts.push(...result.created);
      duplicatesSkipped += result.duplicatesSkipped;
    }

    // Create list
    const list = await this.createList({
      name: listName,
      description: `Imported from CSV - ${contacts.length} contacts${duplicatesSkipped > 0 ? ` (${duplicatesSkipped} duplicates skipped)` : ''}`,
      contacts,
    });
    
    // Attach duplicates count to help with UI reporting
    (list as any).duplicatesSkipped = duplicatesSkipped;
    
    return list;
  }

  // Batch create contacts for better performance with large files
  async createContactsBatch(contactsData: Omit<Contact, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<{ created: Contact[], duplicatesSkipped: number }> {
    const allContacts = await this.getAllContacts();
    const now = new Date();
    const newContacts: Contact[] = [];
    let duplicatesSkipped = 0;

    // Build a Set of existing emails and phones for quick lookup
    const existingEmails = new Set(
      allContacts.map(c => c.email?.toLowerCase()).filter(Boolean)
    );
    const existingPhones = new Set(
      allContacts.map(c => c.phone?.replace(/\D/g, '')).filter(Boolean)
    );
    
    // Also track new contacts being added in this batch to avoid duplicates within the batch
    const newEmails = new Set<string>();
    const newPhones = new Set<string>();

    for (const contact of contactsData) {
      const email = contact.email?.toLowerCase();
      const phone = contact.phone?.replace(/\D/g, '');
      
      // Check if duplicate (by email or phone)
      const isDuplicateEmail = email && (existingEmails.has(email) || newEmails.has(email));
      const isDuplicatePhone = phone && (existingPhones.has(phone) || newPhones.has(phone));
      
      if (isDuplicateEmail || isDuplicatePhone) {
        duplicatesSkipped++;
        continue;
      }
      
      const newContact: Contact = {
        ...contact,
        id: `contact-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        createdAt: now,
        updatedAt: now,
      };
      newContacts.push(newContact);
      allContacts.push(newContact);
      
      // Track added contacts for batch deduplication
      if (email) newEmails.add(email);
      if (phone) newPhones.add(phone);
    }

    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(allContacts, null, 2));
    return { created: newContacts, duplicatesSkipped };
  }
}

export const contactDB = new ContactDatabase();

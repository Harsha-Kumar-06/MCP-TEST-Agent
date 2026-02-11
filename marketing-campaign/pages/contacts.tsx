import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useRef, useState, useTransition } from 'react';

const CONTACTS_PER_PAGE = 50;

export default function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [lists, setLists] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [editingContact, setEditingContact] = useState<any>(null);
  const [editingList, setEditingList] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loadingContacts, setLoadingContacts] = useState(true);
  const [isPending, startTransition] = useTransition();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Calculate pagination
  const totalPages = Math.ceil(contacts.length / CONTACTS_PER_PAGE);
  const paginatedContacts = contacts.slice(
    (currentPage - 1) * CONTACTS_PER_PAGE,
    currentPage * CONTACTS_PER_PAGE
  );

  useEffect(() => {
    fetchContacts();
    fetchLists();
  }, []);

  const fetchContacts = async () => {
    setLoadingContacts(true);
    try {
      const res = await fetch('/api/contacts');
      const data = await res.json();
      if (data.success) {
        startTransition(() => {
          setContacts(data.data);
        });
      }
    } catch (error) {
      console.error('Failed to fetch contacts:', error);
    } finally {
      setLoadingContacts(false);
    }
  };

  const fetchLists = async () => {
    try {
      const res = await fetch('/api/contacts/lists');
      const data = await res.json();
      if (data.success) {
        setLists(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch lists:', error);
    }
  };

  const handleDeleteAllLists = async () => {
    if (lists.length === 0) {
      alert('No lists to delete');
      return;
    }
    
    const totalContacts = lists.reduce((sum: number, list: any) => sum + list.contacts.length, 0);
    if (!confirm(`⚠️ DELETE ALL ${lists.length} LISTS?\n\nThis will permanently delete:\n• ${lists.length} contact lists\n• ${totalContacts} contacts\n\nThis action cannot be undone!`)) return;
    
    // Double confirmation for safety
    if (!confirm('Are you absolutely sure? Type OK to confirm.')) return;
    
    try {
      const res = await fetch('/api/contacts/lists?deleteAll=true', {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.success) {
        alert(`✅ ${data.message}`);
        fetchLists();
        fetchContacts();
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Failed to delete all lists');
    }
  };

  const handleDeleteList = async (listId: string, listName: string, contactCount: number) => {
    if (!confirm(`Delete list "${listName}"?\n\nThis will also delete ${contactCount} contacts.\nThis cannot be undone.`)) return;
    
    try {
      const res = await fetch(`/api/contacts/lists?id=${listId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.success) {
        alert('List deleted successfully');
        fetchLists();
        fetchContacts();
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Failed to delete list');
    }
  };

  const handleDeleteContact = async (contactId: string) => {
    if (!confirm('Delete this contact?')) return;
    
    try {
      const res = await fetch(`/api/contacts?id=${contactId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.success) {
        fetchContacts();
        fetchLists(); // Refresh lists too as they contain contacts
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Failed to delete contact');
    }
  };

  const handleUpdateContact = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingContact) return;

    const formData = new FormData(e.currentTarget);
    const updates = {
      firstName: formData.get('firstName'),
      lastName: formData.get('lastName'),
      email: formData.get('email'),
      phone: formData.get('phone'),
      company: formData.get('company'),
      optInEmail: formData.get('optInEmail') === 'on',
      optInSMS: formData.get('optInSMS') === 'on',
    };

    try {
      const res = await fetch(`/api/contacts?id=${editingContact.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        setEditingContact(null);
        fetchContacts();
        fetchLists();
      } else {
        alert('Failed to update: ' + data.error);
      }
    } catch (error) {
      alert('Failed to update contact');
    }
  };

  const handleUpdateList = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingList) return;

    const formData = new FormData(e.currentTarget);
    const updates = {
      name: formData.get('name'),
      description: formData.get('description'),
    };

    try {
      const res = await fetch(`/api/contacts/lists?id=${editingList.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        setEditingList(null);
        fetchLists();
      } else {
        alert('Failed to update: ' + data.error);
      }
    } catch (error) {
      alert('Failed to update list');
    }
  };

  const handleFileUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please select a file first');
      return;
    }
    
    // Capture form values BEFORE any async operations (React event pooling)
    const listNameInput = e.currentTarget.querySelector('input[name="listName"]') as HTMLInputElement;
    const listName = listNameInput?.value || 'Imported List';
    
    setUploading(true);
    setUploadProgress('Validating file...');

    try {
      // Quick file size check
      const fileSizeMB = selectedFile.size / (1024 * 1024);
      if (fileSizeMB > 50) {
        alert('File too large. Maximum file size is 50MB.');
        setUploading(false);
        setUploadProgress('');
        return;
      }

      // Quick line count estimate
      const text = await selectedFile.text();
      const lineCount = text.split('\n').filter(line => line.trim()).length;
      const estimatedContacts = Math.max(0, lineCount - 1);

      if (estimatedContacts > 10000) {
        alert(`File contains ~${estimatedContacts.toLocaleString()} contacts. Maximum is 10,000 per upload. Please split your file.`);
        setUploading(false);
        setUploadProgress('');
        return;
      }

      setUploadProgress(`Processing ${estimatedContacts.toLocaleString()} contacts...`);

      const formData = new FormData();
      formData.set('file', selectedFile);
      formData.set('listName', listName);

      const res = await fetch('/api/contacts/upload-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        setUploadProgress('');
        alert(data.message);
        setShowUpload(false);
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        fetchContacts();
        fetchLists();
      } else {
        alert('Upload failed: ' + data.error);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress('');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Contacts - Campaign Manager</title>
      </Head>

      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
                🤖 Campaign Coordinator
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-700 hover:text-gray-900">
                🏠 Home
              </Link>
              <Link href="/campaigns" className="text-gray-700 hover:text-gray-900">
                Campaigns
              </Link>
              <Link href="/campaigns/create" className="text-gray-700 hover:text-gray-900">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-blue-600 font-medium">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Contacts</h1>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {showUpload ? 'Cancel' : '📤 Upload CSV'}
          </button>
        </div>

        {/* CSV Upload Form */}
        {showUpload && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">Upload CSV File</h2>
            <form onSubmit={handleFileUpload}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  List Name
                </label>
                <input
                  type="text"
                  name="listName"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Q1 2026 Leads"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CSV File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  name="file"
                  accept=".csv"
                  required
                  onChange={handleFileSelect}
                  className="w-full"
                />
                {selectedFile && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-md border border-blue-200">
                    <p className="text-sm text-blue-800">
                      📄 <strong>{selectedFile.name}</strong>
                    </p>
                    <p className="text-xs text-blue-600">
                      Size: {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                )}
                <div className="mt-2 text-xs text-gray-500 space-y-1">
                  <p>📋 Required columns: email OR phone</p>
                  <p>📋 Optional: firstName, lastName, company, tags, optInEmail, optInSMS</p>
                  <p>💡 <strong>Multiple emails:</strong> Separate with semicolons (john@test.com;jane@test.com)</p>
                  <p>⚠️ Maximum 10,000 contacts per upload</p>
                </div>
              </div>
              
              {/* Upload Progress */}
              {uploading && uploadProgress && (
                <div className="mb-4 p-3 bg-yellow-50 rounded-md border border-yellow-200">
                  <div className="flex items-center">
                    <svg className="animate-spin h-5 w-5 text-yellow-600 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="text-sm text-yellow-800">{uploadProgress}</span>
                  </div>
                  <p className="text-xs text-yellow-600 mt-2">This may take a while for large files. Please don't close this page.</p>
                </div>
              )}
              
              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {uploading ? '⏳ Uploading...' : '📤 Upload'}
              </button>
            </form>
          </div>
        )}

        {/* Contact Lists */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold">Contact Lists ({lists.length})</h2>
            {lists.length > 0 && (
              <button
                onClick={handleDeleteAllLists}
                className="text-red-600 hover:text-red-800 px-3 py-1 text-sm border border-red-600 rounded hover:bg-red-50"
              >
                🗑️ Delete All Lists
              </button>
            )}
          </div>
          <div className="p-6">
            {lists.length === 0 ? (
              <p className="text-gray-500">No contact lists yet. Upload a CSV to get started.</p>
            ) : (
              <div className="space-y-4">
                {lists.map((list: any) => (
                  <div key={list.id} className="border border-gray-200 rounded p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{list.name}</h3>
                        <p className="text-sm text-gray-600">{list.description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {list.contacts.length} contacts • Created {new Date(list.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setEditingList(list)}
                          className="text-blue-600 hover:text-blue-800 px-3 py-1 text-sm border border-blue-600 rounded"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteList(list.id, list.name, list.contacts.length)}
                          className="text-red-600 hover:text-red-800 px-3 py-1 text-sm border border-red-600 rounded"
                        >
                          🗑️ Delete
                        </button>
                        <Link
                          href={`/campaigns/create?listId=${list.id}`}
                          className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Create Campaign
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Edit List Modal */}
        {editingList && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold mb-4">Edit List</h2>
              <form onSubmit={handleUpdateList}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    name="name"
                    defaultValue={editingList.name}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    name="description"
                    defaultValue={editingList.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setEditingList(null)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* All Contacts */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold">
              All Contacts ({contacts.length.toLocaleString()})
              {(loadingContacts || isPending) && <span className="ml-2 text-sm text-gray-400">Loading...</span>}
            </h2>
            {contacts.length > CONTACTS_PER_PAGE && (
              <p className="text-sm text-gray-500">
                Showing {((currentPage - 1) * CONTACTS_PER_PAGE + 1).toLocaleString()}-{Math.min(currentPage * CONTACTS_PER_PAGE, contacts.length).toLocaleString()} of {contacts.length.toLocaleString()}
              </p>
            )}
          </div>
          
          {/* Page Summary - Quick Navigation */}
          {totalPages > 1 && (
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
              <p className="text-sm text-gray-600 mb-2">Quick jump to page:</p>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: totalPages }, (_, i) => {
                  const pageNum = i + 1;
                  const startContact = (pageNum - 1) * CONTACTS_PER_PAGE + 1;
                  const endContact = Math.min(pageNum * CONTACTS_PER_PAGE, contacts.length);
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-300 text-gray-700 hover:bg-blue-50 hover:border-blue-300'
                      }`}
                    >
                      Page {pageNum}: #{startContact}-{endContact}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Opt-In</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loadingContacts ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      <div className="animate-pulse">Loading contacts...</div>
                    </td>
                  </tr>
                ) : paginatedContacts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                      No contacts yet
                    </td>
                  </tr>
                ) : (
                  paginatedContacts.map((contact: any) => (
                    <tr key={contact.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {contact.firstName} {contact.lastName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.phone}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.company}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {contact.optInEmail && <span className="text-green-600">✉️ </span>}
                        {contact.optInSMS && <span className="text-green-600">📱</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setEditingContact(contact)}
                          className="text-blue-600 hover:text-blue-800 mr-3"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteContact(contact.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          🗑️ Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Previous
              </button>
              <div className="flex items-center space-x-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1 rounded ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <>
                    <span className="text-gray-500">...</span>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      className="px-3 py-1 rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </div>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          )}
        </div>

        {/* Edit Contact Modal */}
        {editingContact && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-semibold mb-4">Edit Contact</h2>
              <form onSubmit={handleUpdateContact}>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                    <input
                      type="text"
                      name="firstName"
                      defaultValue={editingContact.firstName}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                    <input
                      type="text"
                      name="lastName"
                      defaultValue={editingContact.lastName}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    name="email"
                    defaultValue={editingContact.email}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="text"
                    name="phone"
                    defaultValue={editingContact.phone}
                    placeholder="+1234567890"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                  <input
                    type="text"
                    name="company"
                    defaultValue={editingContact.company}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4 flex space-x-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="optInEmail"
                      defaultChecked={editingContact.optInEmail}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Email Opt-In</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="optInSMS"
                      defaultChecked={editingContact.optInSMS}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">SMS Opt-In</span>
                  </label>
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                  <button
                    type="button"
                    onClick={() => setEditingContact(null)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

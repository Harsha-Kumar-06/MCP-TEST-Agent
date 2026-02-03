import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function Templates() {
  const router = useRouter();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/api/campaigns/templates');
      const data = await res.json();
      if (data.success) {
        setTemplates(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUseTemplate = (templateId: string) => {
    router.push(`/campaigns/create?templateId=${templateId}`);
  };

  const handleDelete = async (templateId: string) => {
    if (!confirm('Delete this template?')) return;

    try {
      const res = await fetch(`/api/campaigns/templates?id=${templateId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      
      if (data.success) {
        alert('Template deleted successfully');
        fetchTemplates();
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Error deleting template');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Templates - Campaign Manager</title>
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
              <Link href="/campaigns/templates" className="text-blue-600 font-medium">
                📚 Templates
              </Link>
              <Link href="/campaigns/create" className="text-gray-700 hover:text-gray-900">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-gray-700 hover:text-gray-900">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">📚 Campaign Templates</h1>
          <Link
            href="/campaigns/create"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            ➕ New Campaign
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading templates...</div>
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No templates</h3>
            <p className="mt-1 text-sm text-gray-500">
              Save a campaign as a template to reuse it later.
            </p>
            <div className="mt-6">
              <Link
                href="/campaigns"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                View Campaigns
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template: any) => (
              <div key={template.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {template.templateName || template.campaignName}
                      </h3>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {template.channels.map((channel: string) => (
                          <span
                            key={channel}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {channel === 'email' ? '✉️' : channel === 'sms' ? '📱' : '📸'} {channel}
                          </span>
                        ))}
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                        {template.campaignData?.product?.description || 'No description'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleUseTemplate(template.id)}
                      className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                    >
                      Use Template
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="bg-red-100 text-red-600 px-3 py-2 rounded-md hover:bg-red-200 text-sm"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

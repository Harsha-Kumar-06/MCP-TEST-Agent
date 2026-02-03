import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const res = await fetch('/api/campaigns');
      const data = await res.json();
      if (data.success) {
        setCampaigns(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, campaignName: string) => {
    if (!confirm(`Delete campaign "${campaignName}"?`)) return;

    try {
      const res = await fetch(`/api/campaigns?id=${id}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      
      if (data.success) {
        alert('Campaign deleted successfully');
        fetchCampaigns();
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Error deleting campaign');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Campaigns - Campaign Manager</title>
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
              <Link href="/campaigns" className="text-blue-600 font-medium">
                Campaigns
              </Link>
              <Link href="/campaigns/templates" className="text-gray-700 hover:text-gray-900">
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
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Campaign History</h1>
          <Link
            href="/campaigns/create"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            + New Campaign
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading campaigns...</div>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 text-5xl mb-4">📭</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No campaigns yet</h3>
            <p className="text-gray-500 mb-6">Create your first campaign to get started!</p>
            <Link
              href="/campaigns/create"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700"
            >
              Create Campaign
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channels
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Results
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.map((campaign: any) => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{campaign.campaignName}</div>
                      <div className="text-sm text-gray-500">{campaign.recipientInfo}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-1">
                        {campaign.channels.map((ch: string) => (
                          <span
                            key={ch}
                            className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {ch === 'email' ? '✉️' : '📱'} {ch}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {campaign.recipientCount} contact{campaign.recipientCount !== 1 ? 's' : ''}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {campaign.results.emailsSent !== undefined && (
                        <div>📧 {campaign.results.emailsSent} sent</div>
                      )}
                      {campaign.results.smsSent !== undefined && (
                        <div>💬 {campaign.results.smsSent} sent</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(campaign.status)}`}>
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(campaign.executedAt).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium space-x-2">
                      <Link
                        href={`/campaigns/${campaign.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </Link>
                      <Link
                        href={`/campaigns/edit/${campaign.id}`}
                        className="text-green-600 hover:text-green-900"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDelete(campaign.id, campaign.campaignName)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

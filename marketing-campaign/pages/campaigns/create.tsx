import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useCallback, useEffect, useRef, useState } from 'react';

const FORM_STORAGE_KEY = 'campaign_form_draft';

export default function CreateCampaign() {
  const router = useRouter();
  const { listId, templateId } = router.query;

  const [lists, setLists] = useState([]);
  const [executing, setExecuting] = useState(false);
  const [recipientMode, setRecipientMode] = useState<'list' | 'single'>('list');
  const [uploading, setUploading] = useState(false);
  const [showUploadSection, setShowUploadSection] = useState(true);
  const [scheduleNow, setScheduleNow] = useState(true);
  const [scheduledDateTime, setScheduledDateTime] = useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showDraftRecoveryModal, setShowDraftRecoveryModal] = useState(false);
  const isInitialized = useRef(false);
  
  const [formData, setFormData] = useState({
    campaignName: '',
    channels: [] as string[],
    productName: '',
    productDescription: '',
    features: '',
    pricing: '',
    targetDemographics: '',
    targetInterests: '',
    painPoints: '',
    budget: '',
    startDate: '',
    endDate: '',
    goals: '',
    brandVoice: 'professional',
    contactListId: listId || '',
    // Single contact fields
    singleEmail: '',
    singlePhone: '',
    singleFirstName: '',
    singleLastName: '',
    singleCompany: '',
    // Company/Contact info fields (per campaign)
    companyName: '',
    replyToEmail: '',
    companyPhone: '',
    companyWebsite: '',
    landingUrl: '', // URL for SMS/email links
    bookingLink: '',
    twitter: '',
    linkedin: '',
    facebook: '',
    instagram: '',
  });

  // Check for saved draft on mount
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;
    
    const savedDraft = localStorage.getItem(FORM_STORAGE_KEY);
    if (savedDraft && !templateId) {
      try {
        const draft = JSON.parse(savedDraft);
        // Check if draft has meaningful data
        if (draft.campaignName || draft.productName || draft.productDescription) {
          setShowDraftRecoveryModal(true);
        }
      } catch (e) {
        localStorage.removeItem(FORM_STORAGE_KEY);
      }
    }
  }, [templateId]);

  // Save form data to localStorage whenever it changes
  useEffect(() => {
    if (!isInitialized.current) return;
    
    // Don't save if form is empty
    const hasData = formData.campaignName || formData.productName || formData.productDescription;
    if (hasData) {
      localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({
        ...formData,
        recipientMode,
        scheduleNow,
        scheduledDateTime,
        savedAt: new Date().toISOString()
      }));
      setHasUnsavedChanges(true);
    }
  }, [formData, recipientMode, scheduleNow, scheduledDateTime]);

  // Warn before leaving page with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges && !executing) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    const handleRouteChange = (url: string) => {
      if (hasUnsavedChanges && !executing && !url.includes('/campaigns')) {
        if (!window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
          router.events.emit('routeChangeError');
          throw 'Route change aborted';
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    router.events.on('routeChangeStart', handleRouteChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      router.events.off('routeChangeStart', handleRouteChange);
    };
  }, [hasUnsavedChanges, executing, router.events]);

  // Recover draft from localStorage
  const recoverDraft = useCallback(() => {
    const savedDraft = localStorage.getItem(FORM_STORAGE_KEY);
    if (savedDraft) {
      try {
        const draft = JSON.parse(savedDraft);
        setFormData(prev => ({
          ...prev,
          ...draft,
          contactListId: listId || draft.contactListId || '',
        }));
        if (draft.recipientMode) setRecipientMode(draft.recipientMode);
        if (draft.scheduleNow !== undefined) setScheduleNow(draft.scheduleNow);
        if (draft.scheduledDateTime) setScheduledDateTime(draft.scheduledDateTime);
        setShowUploadSection(false);
      } catch (e) {
        console.error('Failed to recover draft:', e);
      }
    }
    setShowDraftRecoveryModal(false);
  }, [listId]);

  // Discard draft and start fresh
  const discardDraft = useCallback(() => {
    localStorage.removeItem(FORM_STORAGE_KEY);
    setShowDraftRecoveryModal(false);
    setHasUnsavedChanges(false);
  }, []);

  // Clear draft after successful campaign execution
  const clearDraft = useCallback(() => {
    localStorage.removeItem(FORM_STORAGE_KEY);
    setHasUnsavedChanges(false);
  }, []);

  useEffect(() => {
    fetchLists();
    if (templateId) {
      loadTemplate(templateId as string);
    }
  }, []);

  useEffect(() => {
    if (listId) {
      setFormData(prev => ({ ...prev, contactListId: listId as string }));
    }
  }, [listId]);

  const loadTemplate = async (id: string) => {
    try {
      const res = await fetch('/api/campaigns/templates');
      const data = await res.json();
      if (data.success) {
        const template = data.data.find((t: any) => t.id === id);
        if (template) {
          setFormData(prev => ({
            ...prev,
            campaignName: template.campaignName + ' (Copy)',
            channels: template.channels,
            productName: template.campaignData.product.name,
            productDescription: template.campaignData.product.description,
            features: template.campaignData.product.features.join('\n'),
            pricing: template.campaignData.product.pricing,
            targetDemographics: template.campaignData.targetAudience.demographics,
            targetInterests: template.campaignData.targetAudience.interests.join(', '),
            painPoints: template.campaignData.targetAudience.painPoints.join(', '),
            budget: template.campaignData.budget.toString(),
            goals: template.campaignData.goals.join('\n'),
            brandVoice: template.campaignData.brandVoice,
            companyName: template.campaignData.companyInfo?.companyName || '',
            replyToEmail: template.campaignData.companyInfo?.replyToEmail || '',
            companyPhone: template.campaignData.companyInfo?.phone || '',
            companyWebsite: template.campaignData.companyInfo?.website || '',
            bookingLink: template.campaignData.companyInfo?.bookingLink || '',
            twitter: template.campaignData.companyInfo?.socialMedia?.twitter || '',
            linkedin: template.campaignData.companyInfo?.socialMedia?.linkedin || '',
            facebook: template.campaignData.companyInfo?.socialMedia?.facebook || '',
            instagram: template.campaignData.companyInfo?.socialMedia?.instagram || '',
          }));
          setShowUploadSection(false);
          alert('✅ Template loaded! Review and edit as needed.');
        }
      }
    } catch (error) {
      console.error('Failed to load template:', error);
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

  const handleChannelToggle = (channel: string) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  const handleDocumentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('document', file);

      const res = await fetch('/api/campaigns/parse-document', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (data.success) {
        // Auto-populate form with extracted data
        setFormData(prev => ({
          ...prev,
          campaignName: data.data.campaignName || prev.campaignName,
          channels: data.data.channels?.length > 0 ? data.data.channels : prev.channels,
          productName: data.data.productName || prev.productName,
          productDescription: data.data.productDescription || prev.productDescription,
          features: data.data.features || prev.features,
          pricing: data.data.pricing || prev.pricing,
          targetDemographics: data.data.targetDemographics || prev.targetDemographics,
          targetInterests: data.data.targetInterests || prev.targetInterests,
          painPoints: data.data.painPoints || prev.painPoints,
          budget: data.data.budget || prev.budget,
          startDate: data.data.startDate || prev.startDate,
          endDate: data.data.endDate || prev.endDate,
          goals: data.data.goals || prev.goals,
          companyName: data.data.companyName || prev.companyName,
          replyToEmail: data.data.replyToEmail || prev.replyToEmail,
          companyPhone: data.data.companyPhone || prev.companyPhone,
          companyWebsite: data.data.companyWebsite || prev.companyWebsite,
        }));

        setShowUploadSection(false);
        alert('✅ Campaign details extracted successfully! Review and edit as needed before executing.');
      } else {
        alert('Failed to parse document: ' + data.error);
      }
    } catch (error) {
      alert('Error uploading document');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecuting(true);

    try {
      // Build campaign request
      const campaignRequest: any = {
        campaignId: `camp-${Date.now()}`,
        campaignName: formData.campaignName,
        channels: formData.channels,
        product: {
          name: formData.productName,
          description: formData.productDescription,
          features: formData.features.split('\n').filter(f => f.trim()),
          pricing: formData.pricing,
        },
        targetAudience: {
          demographics: formData.targetDemographics,
          interests: formData.targetInterests.split(',').map(i => i.trim()),
          painPoints: formData.painPoints.split(',').map(p => p.trim()),
        },
        budget: parseFloat(formData.budget),
        timeline: {
          startDate: formData.startDate,
          endDate: formData.endDate,
        },
        goals: formData.goals.split('\n').filter(g => g.trim()),
        brandVoice: formData.brandVoice,
        landingUrl: formData.landingUrl || undefined,
      };

      // Add company info if provided
      if (formData.companyName || formData.replyToEmail || formData.companyPhone) {
        campaignRequest.companyInfo = {
          companyName: formData.companyName || undefined,
          replyToEmail: formData.replyToEmail || undefined,
          phone: formData.companyPhone || undefined,
          website: formData.companyWebsite || undefined,
          bookingLink: formData.bookingLink || undefined,
          socialMedia: {
            twitter: formData.twitter || undefined,
            linkedin: formData.linkedin || undefined,
            facebook: formData.facebook || undefined,
            instagram: formData.instagram || undefined,
          },
        };
      }

      // Build payload based on recipient mode
      const payload: any = { campaignRequest };
      
      if (recipientMode === 'single') {
        payload.singleContact = {
          id: `contact-${Date.now()}`,
          email: formData.singleEmail,
          phone: formData.singlePhone,
          firstName: formData.singleFirstName,
          lastName: formData.singleLastName,
          company: formData.singleCompany,
          optInEmail: true,
          optInSMS: true,
        };
      } else {
        payload.contactListId = formData.contactListId;
      }

      // If scheduling, use schedule endpoint
      if (!scheduleNow && scheduledDateTime) {
        const schedulePayload = {
          ...payload,
          scheduledAt: new Date(scheduledDateTime).toISOString(),
        };

        const res = await fetch('/api/campaigns/schedule', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(schedulePayload),
        });

        const data = await res.json();
        
        if (data.success) {
          clearDraft();
          alert(`Campaign scheduled successfully for ${new Date(scheduledDateTime).toLocaleString()}!`);
          router.push('/campaigns');
        } else {
          alert('Failed to schedule campaign: ' + data.error);
        }
      } else {
        // Execute immediately
        const res = await fetch('/api/campaigns/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await res.json();
        
        if (data.success) {
          clearDraft();
          alert('Campaign executed successfully!');
          router.push('/campaigns');
        } else {
          alert('Campaign failed: ' + data.error);
        }
      }
    } catch (error) {
      alert('Failed to execute campaign');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Create Campaign - Campaign Manager</title>
      </Head>

      {/* Draft Recovery Modal */}
      {showDraftRecoveryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">📝 Recover Draft?</h3>
            <p className="text-gray-600 mb-4">
              You have an unsaved campaign draft. Would you like to continue where you left off?
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={discardDraft}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Start Fresh
              </button>
              <button
                onClick={recoverDraft}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Recover Draft
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Unsaved Changes Indicator */}
      {hasUnsavedChanges && (
        <div className="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded-lg text-sm z-40 shadow-lg">
          💾 Draft auto-saved
        </div>
      )}

      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-2">
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
              <Link href="/campaigns/templates" className="text-gray-700 hover:text-gray-900">
                📚 Templates
              </Link>
              <Link href="/campaigns/create" className="text-blue-600 font-medium">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-gray-700 hover:text-gray-900">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Campaign</h1>

        {/* Document Upload Section */}
        {showUploadSection && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg shadow mb-6 border-2 border-dashed border-blue-300">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <svg className="h-12 w-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  📄 Quick Import - Upload Campaign Document
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  Upload a PDF, DOCX, or TXT file containing campaign details. We'll automatically extract and populate the form fields for you!
                </p>
                <div className="flex items-center space-x-4">
                  <label className="cursor-pointer bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 inline-flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    {uploading ? 'Processing...' : 'Choose File'}
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={handleDocumentUpload}
                      disabled={uploading}
                      className="hidden"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowUploadSection(false)}
                    className="text-gray-600 hover:text-gray-800 underline"
                  >
                    Skip & fill manually
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Supported formats: PDF, DOCX, TXT • Max size: 10MB
                </p>
              </div>
            </div>
          </div>
        )}

        {!showUploadSection && (
          <button
            type="button"
            onClick={() => setShowUploadSection(true)}
            className="mb-4 text-blue-600 hover:text-blue-800 text-sm flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload document to auto-fill form
          </button>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Campaign Name*</label>
                <input
                  type="text"
                  required
                  value={formData.campaignName}
                  onChange={(e) => setFormData({...formData, campaignName: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Q1 2026 Product Launch"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Channels*</label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes('email')}
                      onChange={() => handleChannelToggle('email')}
                      className="mr-2"
                    />
                    ✉️ Email
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes('sms')}
                      onChange={() => handleChannelToggle('sms')}
                      className="mr-2"
                    />
                    📱 SMS
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes('instagram')}
                      onChange={() => handleChannelToggle('instagram')}
                      className="mr-2"
                    />
                    📸 Instagram
                  </label>
                </div>
              </div>

              {/* Recipients Section - Dynamic based on channels */}
              <div>
                {/* Show note if only Instagram is selected */}
                {formData.channels.length === 1 && formData.channels[0] === 'instagram' ? (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      📸 <strong>Instagram Channel:</strong> Posts to your Instagram account feed. No individual recipients needed.
                    </p>
                  </div>
                ) : (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recipient Mode*
                      {formData.channels.includes('instagram') && (
                        <span className="ml-2 text-xs text-gray-500">(for Email/SMS channels)</span>
                      )}
                    </label>
                    
                    <div className="flex space-x-4 mb-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          checked={recipientMode === 'list'}
                          onChange={() => setRecipientMode('list')}
                          className="mr-2"
                        />
                        📋 Contact List
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          checked={recipientMode === 'single'}
                          onChange={() => setRecipientMode('single')}
                          className="mr-2"
                        />
                        👤 Single Contact
                      </label>
                    </div>

                    {recipientMode === 'list' ? (
                      <select
                        required={formData.channels.some(c => c === 'email' || c === 'sms')}
                        value={formData.contactListId}
                        onChange={(e) => setFormData({...formData, contactListId: e.target.value})}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                      >
                        <option value="">Choose a contact list...</option>
                        {lists.map((list: any) => (
                          <option key={list.id} value={list.id}>
                            {list.name} ({list.contacts.length} contacts)
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="space-y-3 bg-gray-50 p-4 rounded-md">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700">First Name*</label>
                            <input
                              type="text"
                              required={recipientMode === 'single' && (formData.channels.includes('email') || formData.channels.includes('sms'))}
                              value={formData.singleFirstName}
                              onChange={(e) => setFormData({...formData, singleFirstName: e.target.value})}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                              placeholder="John"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Last Name*</label>
                            <input
                              type="text"
                              required={recipientMode === 'single' && (formData.channels.includes('email') || formData.channels.includes('sms'))}
                              value={formData.singleLastName}
                              onChange={(e) => setFormData({...formData, singleLastName: e.target.value})}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                              placeholder="Smith"
                            />
                          </div>
                        </div>
                        
                        {/* Email field - only show if email channel selected */}
                        {formData.channels.includes('email') && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700">
                              Email*
                              <span className="ml-1 text-xs text-gray-500">(for Email channel)</span>
                            </label>
                            <input
                              type="email"
                              required={recipientMode === 'single' && formData.channels.includes('email')}
                              value={formData.singleEmail}
                              onChange={(e) => setFormData({...formData, singleEmail: e.target.value})}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                              placeholder="john.smith@example.com"
                            />
                          </div>
                        )}
                        
                        {/* Phone field - only show if SMS channel selected */}
                        {formData.channels.includes('sms') && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700">
                              Phone*
                              <span className="ml-1 text-xs text-gray-500">(for SMS channel)</span>
                            </label>
                            <input
                              type="tel"
                              required={recipientMode === 'single' && formData.channels.includes('sms')}
                              value={formData.singlePhone}
                              onChange={(e) => setFormData({...formData, singlePhone: e.target.value})}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                              placeholder="+1-555-0123"
                            />
                          </div>
                        )}
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Company</label>
                          <input
                            type="text"
                            value={formData.singleCompany}
                            onChange={(e) => setFormData({...formData, singleCompany: e.target.value})}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                            placeholder="Acme Corp"
                          />
                        </div>
                      </div>
                    )}

                    {/* Instagram note when combined with other channels */}
                    {formData.channels.includes('instagram') && formData.channels.length > 1 && (
                      <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p className="text-xs text-blue-700">
                          ℹ️ Instagram will post to your account feed separately (no individual recipients)
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Product Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Product Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Product Name*</label>
                <input
                  type="text"
                  required
                  value={formData.productName}
                  onChange={(e) => setFormData({...formData, productName: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description*</label>
                <textarea
                  required
                  value={formData.productDescription}
                  onChange={(e) => setFormData({...formData, productDescription: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Features (one per line)*</label>
                <textarea
                  required
                  value={formData.features}
                  onChange={(e) => setFormData({...formData, features: e.target.value})}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="AI-powered analytics&#10;Real-time collaboration&#10;Easy integration"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Pricing</label>
                <input
                  type="text"
                  value={formData.pricing}
                  onChange={(e) => setFormData({...formData, pricing: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Starting at $29/month"
                />
              </div>
            </div>
          </div>

          {/* Audience */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Target Audience</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Demographics*</label>
                <input
                  type="text"
                  required
                  value={formData.targetDemographics}
                  onChange={(e) => setFormData({...formData, targetDemographics: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Software developers, ages 25-45"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Interests (comma-separated)*</label>
                <input
                  type="text"
                  required
                  value={formData.targetInterests}
                  onChange={(e) => setFormData({...formData, targetInterests: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Technology, Productivity, SaaS"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Pain Points (comma-separated)*</label>
                <input
                  type="text"
                  required
                  value={formData.painPoints}
                  onChange={(e) => setFormData({...formData, painPoints: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Slow workflows, Poor collaboration"
                />
              </div>
            </div>
          </div>

          {/* Campaign Details */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Campaign Details</h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Budget ($)*</label>
                  <input
                    type="number"
                    required
                    value={formData.budget}
                    onChange={(e) => setFormData({...formData, budget: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    placeholder="5000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Brand Voice*</label>
                  <select
                    value={formData.brandVoice}
                    onChange={(e) => setFormData({...formData, brandVoice: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="friendly">Friendly</option>
                    <option value="authoritative">Authoritative</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Start Date*</label>
                  <input
                    type="date"
                    required
                    value={formData.startDate}
                    onChange={(e) => setFormData({...formData, startDate: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">End Date*</label>
                  <input
                    type="date"
                    required
                    value={formData.endDate}
                    onChange={(e) => setFormData({...formData, endDate: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Goals (one per line)*</label>
                <textarea
                  required
                  value={formData.goals}
                  onChange={(e) => setFormData({...formData, goals: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="Generate 1000 qualified leads&#10;Achieve 20% open rate&#10;Drive 500 trial signups"
                />
              </div>
            </div>
          </div>

          {/* Company Contact Information */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">📞 Contact Information (Optional)</h2>
            <p className="text-sm text-gray-600 mb-4">
              Leave blank to use default values from settings. Customize for specific clients.
            </p>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Company Name</label>
                  <input
                    type="text"
                    value={formData.companyName}
                    onChange={(e) => setFormData({...formData, companyName: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    placeholder="Acme Corp"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reply-To Email</label>
                  <input
                    type="email"
                    value={formData.replyToEmail}
                    onChange={(e) => setFormData({...formData, replyToEmail: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    placeholder="support@acmecorp.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                  <input
                    type="tel"
                    value={formData.companyPhone}
                    onChange={(e) => setFormData({...formData, companyPhone: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    placeholder="+1-234-567-8900"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Website URL</label>
                  <input
                    type="url"
                    value={formData.companyWebsite}
                    onChange={(e) => setFormData({...formData, companyWebsite: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    placeholder="https://acmecorp.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Landing Page URL (for SMS/Email links) *</label>
                <input
                  type="url"
                  value={formData.landingUrl}
                  onChange={(e) => setFormData({...formData, landingUrl: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="https://yoursite.com/promo or https://bit.ly/yourlink"
                />
                <p className="text-xs text-gray-500 mt-1">This URL will be included in SMS messages. Use a short URL for best results.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Booking/Calendar Link</label>
                <input
                  type="url"
                  value={formData.bookingLink}
                  onChange={(e) => setFormData({...formData, bookingLink: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  placeholder="https://calendly.com/yourname/demo"
                />
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Social Media Links (Optional)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <input
                      type="url"
                      value={formData.twitter}
                      onChange={(e) => setFormData({...formData, twitter: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                      placeholder="🐦 Twitter: https://twitter.com/..."
                    />
                  </div>
                  <div>
                    <input
                      type="url"
                      value={formData.linkedin}
                      onChange={(e) => setFormData({...formData, linkedin: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                      placeholder="💼 LinkedIn: https://linkedin.com/..."
                    />
                  </div>
                  <div>
                    <input
                      type="url"
                      value={formData.facebook}
                      onChange={(e) => setFormData({...formData, facebook: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                      placeholder="📘 Facebook: https://facebook.com/..."
                    />
                  </div>
                  <div>
                    <input
                      type="url"
                      value={formData.instagram}
                      onChange={(e) => setFormData({...formData, instagram: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                      placeholder="📷 Instagram: https://instagram.com/..."
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scheduling Section */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">⏰ Schedule Campaign</h2>
            
            <div className="space-y-4">
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    checked={scheduleNow}
                    onChange={() => setScheduleNow(true)}
                    className="mr-2"
                  />
                  <span className="font-medium">Send Now</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    checked={!scheduleNow}
                    onChange={() => setScheduleNow(false)}
                    className="mr-2"
                  />
                  <span className="font-medium">Schedule for Later</span>
                </label>
              </div>

              {!scheduleNow && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Send Date & Time*</label>
                  <input
                    type="datetime-local"
                    required={!scheduleNow}
                    value={scheduledDateTime}
                    onChange={(e) => setScheduledDateTime(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                    min={new Date().toISOString().slice(0, 16)}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Campaign will be automatically sent at the scheduled time
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <Link
              href="/"
              className="px-6 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={executing || formData.channels.length === 0}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {executing ? '⏳ Processing...' : (scheduleNow ? '🚀 Execute Now' : '📅 Schedule Campaign')}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

/**
 * Instagram Posting Agent
 * Posts campaign content to Instagram feed and stories
 * Requires Instagram Graph API access
 */

export interface InstagramPost {
  caption: string;
  imageUrl?: string;
  imageUrls?: string[];  // For carousel posts
  videoUrl?: string;
  postType?: 'image' | 'video' | 'carousel' | 'story';
  hashtags: string[];
  callToAction?: string;
}

interface FacebookGraphError {
  message: string;
  type: string;
  code: number;
  error_subcode?: number;
}

interface ContainerResponse {
  id: string;
  error?: FacebookGraphError;
}

interface PublishResponse {
  id: string;
  error?: FacebookGraphError;
}

export class InstagramPostingAgent {
  private accessToken: string;
  private instagramAccountId: string;

  constructor() {
    this.accessToken = process.env.INSTAGRAM_ACCESS_TOKEN || '';
    this.instagramAccountId = process.env.INSTAGRAM_ACCOUNT_ID || '';
  }

  /**
   * Check if Instagram is configured
   */
  isConfigured(): boolean {
    return !!(this.accessToken && this.instagramAccountId);
  }

  /**
   * Generate Instagram post content from campaign
   */
  generatePostContent(campaignData: any): InstagramPost {
    const product = campaignData.product;
    const hashtags = [
      '#marketing',
      '#business',
      '#startup',
      ...campaignData.targetAudience.interests.map((i: string) => 
        '#' + i.toLowerCase().replace(/\s+/g, '')
      )
    ].slice(0, 10); // Instagram allows max 30, we'll use 10

    const caption = `
✨ ${product.name} ✨

${product.description}

🎯 Perfect for: ${campaignData.targetAudience.demographics}

Key Features:
${product.features.slice(0, 3).map((f: string) => `✓ ${f}`).join('\n')}

${product.pricing ? `💰 ${product.pricing}` : ''}

${campaignData.companyInfo?.website ? `🔗 Link in bio: ${campaignData.companyInfo.website}` : ''}

${hashtags.join(' ')}
`.trim();

    return {
      caption,
      hashtags,
      callToAction: campaignData.goals[0],
    };
  }

  /**
   * Post to Instagram Feed (supports image, video/reels, and carousel)
   */
  async postToFeed(content: InstagramPost): Promise<{ success: boolean; postId?: string; error?: string }> {
    if (!this.isConfigured()) {
      console.warn('⚠️  Instagram posting skipped - Not configured');
      console.log('   To enable Instagram: Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env');
      return {
        success: false,
        error: 'Instagram not configured'
      };
    }

    // Check for media
    const hasCarouselImages = content.imageUrls && content.imageUrls.length >= 2;
    const hasSingleImage = !!content.imageUrl;
    const hasVideo = !!content.videoUrl;

    if (!hasCarouselImages && !hasSingleImage && !hasVideo) {
      console.warn('⚠️  Instagram posting skipped - No media URL provided');
      console.log('   Instagram requires a publicly accessible image or video URL');
      return {
        success: false,
        error: 'Instagram requires a media URL (image or video)'
      };
    }

    try {
      const postType = content.postType || (hasCarouselImages ? 'carousel' : hasVideo ? 'video' : 'image');
      console.log(`📸 Posting to Instagram feed (${postType})...`);
      console.log('📝 Caption:', content.caption.substring(0, 100) + '...');
      
      let creationId: string;

      // Handle different post types
      if (postType === 'carousel' && hasCarouselImages) {
        creationId = await this.createCarouselContainer(content);
      } else if (postType === 'video' && hasVideo) {
        console.log('🎬 Video URL:', content.videoUrl);
        creationId = await this.createMediaContainer({
          video_url: content.videoUrl,
          caption: content.caption,
          media_type: 'REELS',
        });
      } else {
        console.log('🖼️  Image URL:', content.imageUrl);
        creationId = await this.createMediaContainer({
          image_url: content.imageUrl,
          caption: content.caption,
        });
      }

      // Wait for media to be ready and publish
      await this.waitForMediaReady(creationId);
      const publishResult = await this.publishMedia(creationId);

      console.log(`✅ Instagram ${postType} post published: ${publishResult.id}`);
      console.log(`   View at: https://www.instagram.com/p/${this.getShortcode(publishResult.id)}`);
      
      return {
        success: true,
        postId: publishResult.id,
      };

    } catch (error) {
      console.error('❌ Instagram posting failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Create a single media container (image or video)
   */
  private async createMediaContainer(params: any): Promise<string> {
    console.log('   Creating media container...');
    
    const response = await fetch(
      `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...params,
          access_token: this.accessToken,
        })
      }
    );

    const data = await response.json() as ContainerResponse;
    console.log('   Container response:', JSON.stringify(data, null, 2));

    if (!response.ok || data.error) {
      throw new Error(data.error?.message || 'Failed to create media container');
    }

    return data.id;
  }

  /**
   * Create carousel container (multiple images)
   */
  private async createCarouselContainer(content: InstagramPost): Promise<string> {
    console.log(`   Creating carousel with ${content.imageUrls!.length} images...`);
    
    // Step 1: Create container for each image (without caption)
    const childContainerIds: string[] = [];
    
    for (let i = 0; i < content.imageUrls!.length; i++) {
      const imageUrl = content.imageUrls![i];
      console.log(`   Creating child container ${i + 1}/${content.imageUrls!.length}: ${imageUrl}`);
      
      const childResponse = await fetch(
        `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_url: imageUrl,
            is_carousel_item: true,
            access_token: this.accessToken,
          })
        }
      );

      const childData = await childResponse.json() as ContainerResponse;
      
      if (!childResponse.ok || childData.error) {
        throw new Error(`Failed to create carousel item ${i + 1}: ${childData.error?.message}`);
      }
      
      childContainerIds.push(childData.id);
      console.log(`   ✓ Child container ${i + 1} created: ${childData.id}`);
      
      // Wait for each child to be ready
      await this.waitForMediaReady(childData.id);
    }

    // Step 2: Create the carousel container
    console.log('   Creating carousel parent container...');
    const carouselResponse = await fetch(
      `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          media_type: 'CAROUSEL',
          caption: content.caption,
          children: childContainerIds.join(','),
          access_token: this.accessToken,
        })
      }
    );

    const carouselData = await carouselResponse.json() as ContainerResponse;
    console.log('   Carousel container response:', JSON.stringify(carouselData, null, 2));

    if (!carouselResponse.ok || carouselData.error) {
      throw new Error(carouselData.error?.message || 'Failed to create carousel container');
    }

    return carouselData.id;
  }

  /**
   * Wait for media container to be ready
   */
  private async waitForMediaReady(containerId: string): Promise<void> {
    console.log('   Waiting for media to be ready...');
    const maxAttempts = 60; // Max 60 seconds
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      attempts++;
      
      const statusResponse = await fetch(
        `https://graph.facebook.com/v18.0/${containerId}?fields=status_code,status&access_token=${this.accessToken}`
      );
      const statusData = await statusResponse.json() as any;
      
      if (statusData.status_code === 'FINISHED') {
        console.log(`   ✅ Media ready (attempt ${attempts})`);
        // Extra wait for Instagram backend sync
        await new Promise(resolve => setTimeout(resolve, 2000));
        return;
      } else if (statusData.status_code === 'ERROR') {
        throw new Error(`Media processing failed: ${statusData.status || 'Unknown error'}`);
      }
      
      // Log every 5 attempts
      if (attempts % 5 === 1) {
        console.log(`   Status check ${attempts}: ${statusData.status_code || 'processing...'}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error('Timeout waiting for media to be ready');
  }

  /**
   * Publish media container with retry logic
   */
  private async publishMedia(containerId: string): Promise<{ id: string }> {
    console.log('   Publishing post...');
    const maxAttempts = 5;
    let lastError: string = '';
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      console.log(`   Publish attempt ${attempt}/${maxAttempts}...`);
      
      const publishResponse = await fetch(
        `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media_publish`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            creation_id: containerId,
            access_token: this.accessToken,
          })
        }
      );

      const publishData = await publishResponse.json() as PublishResponse;
      
      if (publishResponse.ok && !publishData.error) {
        return { id: publishData.id };
      }
      
      lastError = publishData.error?.message || 'Unknown error';
      
      // If "media not ready", wait and retry
      if (publishData.error?.error_subcode === 2207027) {
        console.log(`   ⏳ Media not ready, waiting 3 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      } else {
        // Other error - don't retry
        console.log('   Publish error:', JSON.stringify(publishData.error, null, 2));
        break;
      }
    }
    
    throw new Error(lastError || 'Failed to publish after multiple attempts');
  }

  /**
   * Convert Instagram media ID to shortcode for URL
   */
  private getShortcode(mediaId: string): string {
    // Simplified - in production you'd get this from the API response
    return mediaId.split('_')[0];
  }

  /**
   * Post to Instagram Story
   */
  async postToStory(content: InstagramPost): Promise<{ success: boolean; storyId?: string; error?: string }> {
    if (!this.isConfigured()) {
      return {
        success: false,
        error: 'Instagram not configured'
      };
    }

    // Stories require an image or video
    if (!content.imageUrl && !content.videoUrl) {
      return {
        success: false,
        error: 'Story requires image or video URL'
      };
    }

    try {
      console.log('📱 Posting to Instagram story...');
      
      // Create story container (no caption for stories)
      const containerParams: any = {
        media_type: 'STORIES',
      };

      if (content.videoUrl) {
        containerParams.video_url = content.videoUrl;
      } else {
        containerParams.image_url = content.imageUrl;
      }

      const containerId = await this.createMediaContainer(containerParams);
      await this.waitForMediaReady(containerId);
      const publishResult = await this.publishMedia(containerId);

      console.log(`✅ Instagram story published: ${publishResult.id}`);
      
      return {
        success: true,
        storyId: publishResult.id,
      };

    } catch (error) {
      console.error('❌ Instagram story posting failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Execute Instagram campaign (post + story)
   */
  async executeCampaign(campaignData: any): Promise<{
    feedPost?: any;
    story?: any;
  }> {
    // Check if campaign has custom Instagram content
    const instagramContent = campaignData.instagramContent;
    
    let content: InstagramPost;
    
    if (instagramContent && (instagramContent.caption || instagramContent.mediaUrl || instagramContent.mediaUrls)) {
      // Use custom content from campaign
      console.log('📝 Using custom Instagram content from campaign...');
      content = {
        caption: instagramContent.caption || this.generatePostContent(campaignData).caption,
        imageUrl: instagramContent.mediaUrl,
        imageUrls: instagramContent.mediaUrls,  // For carousel
        videoUrl: instagramContent.videoUrl,
        postType: instagramContent.postType,
        hashtags: instagramContent.hashtags || [],
        callToAction: campaignData.goals?.[0],
      };
      
      // Append hashtags to caption if they exist
      if (content.hashtags.length > 0 && !content.caption.includes('#')) {
        content.caption += '\n\n' + content.hashtags.join(' ');
      }
    } else {
      // Generate content from campaign data (legacy mode)
      console.log('⚠️  No custom Instagram content provided, generating from campaign data...');
      content = this.generatePostContent(campaignData);
    }

    // Post to feed (image, video, or carousel)
    let feedPost: any = { success: false, error: 'Not attempted' };
    
    if (content.postType === 'story') {
      // Story-only post
      feedPost = { success: false, error: 'Post type is story, skipping feed' };
    } else {
      feedPost = await this.postToFeed(content);
    }
    
    // Post story if requested or if post type is story
    let story: any = { success: false, error: 'Story not requested' };
    if (content.postType === 'story' && (content.imageUrl || content.videoUrl)) {
      story = await this.postToStory(content);
    }

    return {
      feedPost,
      story,
    };
  }
}

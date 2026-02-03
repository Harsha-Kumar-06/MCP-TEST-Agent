import { AgentResult, CampaignRequest, SubTask } from '../types/campaign';
import { AnalyticsSetupAgent } from './analytics-setup-agent';
import { AudienceSegmentationAgent } from './audience-segmentation-agent';
import { ComplianceAgent } from './compliance-agent';
import { EmailContentAgent } from './email-content-agent';
import { SMSContentAgent } from './sms-content-agent';

/**
 * CoordinatorAgent - The brain of the multi-agent system
 * 
 * Responsibilities:
 * 1. Analyze incoming campaign requests
 * 2. Break down into sub-tasks
 * 3. Determine which specialized agents to invoke
 * 4. Orchestrate the workflow dynamically
 * 5. Aggregate results from all agents
 */
export class CoordinatorAgent {
  private taskQueue: SubTask[] = [];
  private completedTasks: SubTask[] = [];
  private results: Map<string, AgentResult> = new Map();

  /**
   * Main coordination method
   */
  async coordinate(request: CampaignRequest): Promise<Map<string, AgentResult>> {
    console.log('\n🎯 COORDINATOR AGENT: Starting campaign coordination...');
    console.log(`Campaign: ${request.campaignName}`);
    console.log(`Channels: ${request.channels.join(', ')}`);
    console.log('─'.repeat(60));

    try {
      // Step 1: Analyze the request and decompose into sub-tasks
      await this.analyzeAndDecompose(request);

      // Step 2: Execute tasks in order (respecting dependencies)
      await this.executeTasks(request);

      // Step 3: Return aggregated results
      console.log('\n✅ COORDINATOR: Campaign coordination completed successfully');
      return this.results;

    } catch (error) {
      console.error('❌ COORDINATOR: Error during coordination:', error);
      throw error;
    }
  }

  /**
   * Analyze campaign request and create sub-tasks
   * This is where AI-powered dynamic routing happens
   */
  private async analyzeAndDecompose(request: CampaignRequest): Promise<void> {
    console.log('\n📋 COORDINATOR: Analyzing campaign requirements...');

    // Use AI to intelligently determine what agents are needed
    const subTasks: SubTask[] = [];
    let taskId = 1;

    // Always start with audience segmentation
    subTasks.push({
      id: `task-${taskId++}`,
      agentType: 'audience-segmentation',
      taskDescription: 'Analyze and segment target audience',
      priority: 'high',
      status: 'pending',
    });

    // Channel-specific agents based on request
    if (request.channels.includes('email')) {
      subTasks.push({
        id: `task-${taskId++}`,
        agentType: 'email-content',
        taskDescription: 'Generate email marketing content',
        priority: 'high',
        status: 'pending',
        dependencies: ['task-1'], // Depends on audience segmentation
      });
    }

    if (request.channels.includes('sms')) {
      subTasks.push({
        id: `task-${taskId++}`,
        agentType: 'sms-content',
        taskDescription: 'Generate SMS marketing content',
        priority: 'high',
        status: 'pending',
        dependencies: ['task-1'], // Depends on audience segmentation
      });
    }

    // Compliance check (always required)
    subTasks.push({
      id: `task-${taskId++}`,
      agentType: 'compliance',
      taskDescription: 'Review campaign for legal compliance',
      priority: 'high',
      status: 'pending',
      dependencies: request.channels.includes('email') 
        ? ['task-2', 'task-3'] 
        : ['task-2'], // Depends on content creation
    });

    // Analytics setup (always required)
    subTasks.push({
      id: `task-${taskId++}`,
      agentType: 'analytics-setup',
      taskDescription: 'Configure tracking and analytics',
      priority: 'medium',
      status: 'pending',
    });

    this.taskQueue = subTasks;

    console.log(`\n📊 COORDINATOR: Identified ${subTasks.length} sub-tasks:`);
    subTasks.forEach((task) => {
      console.log(`  • [${task.priority.toUpperCase()}] ${task.agentType}: ${task.taskDescription}`);
    });
  }

  /**
   * Execute tasks respecting dependencies
   */
  private async executeTasks(request: CampaignRequest): Promise<void> {
    console.log('\n🚀 COORDINATOR: Beginning task execution...');

    while (this.taskQueue.length > 0) {
      // Find tasks that are ready to execute (no pending dependencies)
      const readyTasks = this.taskQueue.filter((task) => {
        if (!task.dependencies || task.dependencies.length === 0) {
          return true;
        }
        // Check if all dependencies are completed
        return task.dependencies.every((depId) =>
          this.completedTasks.some((t) => t.id === depId && t.status === 'completed')
        );
      });

      if (readyTasks.length === 0) {
        console.warn('⚠️  COORDINATOR: No tasks ready to execute. Possible circular dependency.');
        break;
      }

      // Execute ready tasks
      for (const task of readyTasks) {
        await this.executeTask(task, request);
        // Move task from queue to completed
        this.taskQueue = this.taskQueue.filter((t) => t.id !== task.id);
        this.completedTasks.push(task);
      }
    }
  }

  /**
   * Route task to appropriate specialized agent
   */
  private async executeTask(task: SubTask, request: CampaignRequest): Promise<void> {
    console.log(`\n🔄 COORDINATOR: Routing to ${task.agentType}...`);
    task.status = 'in-progress';

    try {
      // Dynamic routing based on agent type
      let result: AgentResult;

      switch (task.agentType) {
        case 'audience-segmentation':
          const audienceAgent = new AudienceSegmentationAgent();
          result = await audienceAgent.execute(request);
          break;

        case 'email-content':
          const emailAgent = new EmailContentAgent();
          result = await emailAgent.execute(request, this.results.get('audience-segmentation')?.data);
          break;

        case 'sms-content':
          const smsAgent = new SMSContentAgent();
          result = await smsAgent.execute(request, this.results.get('audience-segmentation')?.data);
          break;

        case 'compliance':
          const complianceAgent = new ComplianceAgent();
          result = await complianceAgent.execute(request, this.results);
          break;

        case 'analytics-setup':
          const analyticsAgent = new AnalyticsSetupAgent();
          result = await analyticsAgent.execute(request);
          break;

        default:
          throw new Error(`Unknown agent type: ${task.agentType}`);
      }

      // Store result
      this.results.set(task.agentType, result);
      task.status = 'completed';
      task.result = result.data;

      console.log(`✅ COORDINATOR: ${task.agentType} completed successfully`);

    } catch (error) {
      task.status = 'failed';
      task.error = error instanceof Error ? error.message : 'Unknown error';
      console.error(`❌ COORDINATOR: ${task.agentType} failed:`, task.error);
      throw error;
    }
  }

  /**
   * Get summary of execution
   */
  getSummary(): string {
    const total = this.completedTasks.length;
    const successful = this.completedTasks.filter((t) => t.status === 'completed').length;
    const failed = this.completedTasks.filter((t) => t.status === 'failed').length;

    return `
Campaign Execution Summary
${'='.repeat(60)}
Total Tasks: ${total}
Successful: ${successful}
Failed: ${failed}
${'='.repeat(60)}
    `;
  }
}

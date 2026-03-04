/**
 * Portfolio Manager - Application Logic
 * Handles form submission, API calls, and result rendering
 */

// State management
let portfolioData = null;
let sectorChart = null;
let compositionChart = null;
let workflowInterval = null;

// DOM Elements
const elements = {
    profileForm: null,
    generateBtn: null,
    loadingOverlay: null,
    emptyState: null,
    overviewTab: null,
    holdingsTab: null,
    analysisTab: null,
    statusBadge: null
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
    checkApiHealth();
});

function initializeElements() {
    elements.profileForm = document.getElementById('profileForm');
    elements.generateBtn = document.getElementById('generateBtn');
    elements.loadingOverlay = document.getElementById('loadingOverlay');
    elements.emptyState = document.getElementById('emptyState');
    elements.overviewTab = document.getElementById('overviewTab');
    elements.holdingsTab = document.getElementById('holdingsTab');
    elements.analysisTab = document.getElementById('analysisTab');
    elements.statusBadge = document.getElementById('statusBadge');
}

function setupEventListeners() {
    if (elements.profileForm) {
        elements.profileForm.addEventListener('submit', handleFormSubmit);
    }
}

// Check API health
async function checkApiHealth() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            updateStatus('connected', 'API Connected');
        } else {
            updateStatus('disconnected', 'API Error');
        }
    } catch (error) {
        updateStatus('disconnected', 'API Offline');
    }
}

function updateStatus(status, text) {
    if (elements.statusBadge) {
        elements.statusBadge.className = `status-badge ${status === 'connected' ? '' : status}`;
        elements.statusBadge.innerHTML = `● ${text}`;
    }
}

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();
    await generatePortfolio();
}

// Main portfolio generation function
async function generatePortfolio() {
    // Collect form data
    const capital = parseFloat(document.getElementById('capital').value);
    const goal = document.getElementById('goal').value;
    const horizon = document.getElementById('horizon').value;
    const maxLoss = parseInt(document.getElementById('maxLoss').value) || 15;
    const experience = document.getElementById('experience').value;
    const income = document.getElementById('income').value;

    // Validate
    if (!capital || capital <= 0) {
        showError('Please enter a valid investment capital amount');
        return;
    }

    if (!goal) {
        showError('Please select an investment goal');
        return;
    }

    // Show loading
    showLoading();
    updateStatus('processing', 'Processing...');

    try {
        const response = await fetch('/api/generate-portfolio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                capital: capital,
                goal: goal || 'balanced_growth',
                horizon: horizon || '3_5_years',
                max_loss: maxLoss,
                experience: experience || 'intermediate',
                income_stability: income || 'stable'
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate portfolio');
        }

        const data = await response.json();
        console.log('Portfolio response:', data);

        if (data.success) {
            portfolioData = data;
            displayPortfolio(data);
            updateStatus('connected', 'Complete');
        } else {
            throw new Error(data.error || 'Portfolio generation failed');
        }

    } catch (error) {
        console.error('Error:', error);
        showError('Error generating portfolio: ' + error.message);
        updateStatus('disconnected', 'Error');
    } finally {
        hideLoading();
    }
}

// Display portfolio data from agent response
function displayPortfolio(data) {
    // Hide empty state
    if (elements.emptyState) {
        elements.emptyState.style.display = 'none';
    }

    // Show all tabs
    ['overviewTab', 'holdingsTab', 'analysisTab'].forEach(tab => {
        if (elements[tab]) {
            elements[tab].style.display = 'block';
        }
    });

    // Show download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'inline-flex';
    }

    // Render each section based on agent data
    renderOverview(data);
    renderHoldings(data);
    renderAnalysis(data);

    // Switch to overview tab
    switchTab('overview');
}

// Render overview section
function renderOverview(data) {
    const { profile, portfolio, performance_report } = data;
    
    // Calculate total capital from profile or portfolio
    const totalCapital = profile?.capital || portfolio?.total_capital || 0;
    
    // Calculate invested amount from positions
    const positions = portfolio?.positions || [];
    const investedAmount = positions.reduce((sum, p) => sum + (p.value || 0), 0);
    
    // Count unique sectors
    const sectors = new Set(positions.map(p => p.sector).filter(Boolean));

    // Update stats
    document.getElementById('statCapital').textContent = totalCapital 
        ? '$' + totalCapital.toLocaleString() 
        : '-';
    document.getElementById('statPositions').textContent = positions.length || '-';
    document.getElementById('statSectors').textContent = sectors.size || '-';
    document.getElementById('statRisk').textContent = profile?.risk_score 
        ? profile.risk_score + '/10' 
        : '-';

    // Render charts if we have portfolio data
    if (positions.length > 0) {
        renderCharts({ positions, sector_allocation: portfolio?.sector_allocation });
    }
}

// Render holdings table
function renderHoldings(data) {
    const { portfolio, profile } = data;
    const tbody = document.getElementById('holdingsTable');
    
    if (!portfolio?.positions || !tbody) {
        return;
    }

    // Calculate total value for weight calculation
    const positions = portfolio.positions;
    const totalValue = positions.reduce((sum, h) => sum + (h.value || 0), 0);
    const totalCapital = profile?.capital || totalValue;

    tbody.innerHTML = positions.map(h => {
        // Calculate weight if not provided
        const value = h.value || (h.shares * h.price);
        const weight = h.weight || (totalCapital > 0 ? (value / totalCapital) * 100 : 0);
        
        return `
        <tr>
            <td>
                <div class="stock-cell">
                    <div class="stock-icon">${h.symbol?.slice(0, 2) || '??'}</div>
                    <div>
                        <div class="stock-name">${h.symbol || 'Unknown'}</div>
                        <div class="stock-symbol">${h.name || ''}</div>
                    </div>
                </div>
            </td>
            <td><span class="sector-badge ${getSectorType(h.sector)}">${h.sector || '-'}</span></td>
            <td>${h.shares || '-'}</td>
            <td>$${h.price?.toFixed(2) || '-'}</td>
            <td>$${value?.toLocaleString() || '-'}</td>
            <td>
                <div style="display:flex;align-items:center;gap:8px;">
                    <div class="weight-bar">
                        <div class="weight-fill" style="width:${Math.min(weight, 100)}%"></div>
                    </div>
                    <span>${weight?.toFixed(1) || 0}%</span>
                </div>
            </td>
        </tr>
    `}).join('');
}

// Clean the final report by removing JSON blocks and user profile
function cleanFinalReport(text) {
    if (!text) return '';
    
    // Remove JSON code blocks (```json ... ```)
    let cleaned = text.replace(/```json[\s\S]*?```/g, '');
    
    // Remove the initial confirmation message
    cleaned = cleaned.replace(/^I have your profile\..*?\n+/i, '');
    cleaned = cleaned.replace(/^I cannot generate.*?\n+/gi, '');
    
    // Remove any remaining raw JSON objects at the start
    cleaned = cleaned.replace(/^\s*\{[\s\S]*?\}\s*/g, '');
    
    // Find where the actual report starts (look for markdown headers)
    const reportStart = cleaned.search(/^#\s+Portfolio|^#\s+Investment|Executive Summary/im);
    if (reportStart > 0) {
        cleaned = cleaned.substring(reportStart);
    }
    
    // Clean up extra whitespace
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n').trim();
    
    return cleaned;
}

// Render analysis section with agent outputs
function renderAnalysis(data) {
    const content = document.getElementById('analysisContent');
    if (!content) return;

    const { macro_outlook, top_sectors, selected_stocks, portfolio, performance_report, backtest_results, final_report, raw_response } = data;

    let html = '';
    
    // Check if we have agent reasoning data
    const hasAgentData = macro_outlook || top_sectors || selected_stocks || performance_report || backtest_results;

    // If we have the final report, render it prominently (cleaned)
    if (final_report || raw_response) {
        const cleanedReport = cleanFinalReport(final_report || raw_response);
        
        if (cleanedReport) {
            html += `
                <div class="card agent-response-card">
                    <div class="card-header">
                        <div class="card-title">📊 Portfolio Investment Report</div>
                    </div>
                    <div class="agent-response-content" id="finalReportContent">
                        ${formatMarkdown(cleanedReport)}
                    </div>
                </div>
            `;
        }
    }

    // Agent reasoning in collapsible section
    if (hasAgentData) {
        
        // Macro Outlook from Agent
        if (macro_outlook) {
            html += renderMacroSection(macro_outlook);
        }

        // Sector Selection from Agent
        if (top_sectors) {
            html += renderSectorsSection(top_sectors);
        }

        // Stock Selection Analysis from Agent
        if (selected_stocks) {
            html += renderStocksSection(selected_stocks);
        }

        // Performance Analysis from Agent
        if (performance_report) {
            html += renderPerformanceSection(performance_report);
        }

        // Backtest Results from Agent
        if (backtest_results) {
            html += renderBacktestSection(backtest_results);
        }
        

    }

    // If no agent data yet, show waiting message
    if (!final_report && !raw_response && !hasAgentData) {
        html += `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">⏳ Generating Portfolio...</div>
                </div>
                <div style="padding: 20px; background: var(--bg-input); border-radius: 8px;">
                    <p>Your profile has been submitted. The AI agent is analyzing your requirements...</p>
                    <p style="margin-top: 12px; color: var(--text-secondary);">
                        The agent will perform: Macro Analysis → Sector Selection → Stock Picking → 
                        Portfolio Construction → Performance Analysis → Backtesting → Report Generation
                    </p>
                </div>
            </div>
        `;
    }

    content.innerHTML = html;
}

// Toggle agent reasoning section visibility
function toggleAgentReasoning() {
    const content = document.getElementById('agentReasoningContent');
    const icon = document.getElementById('agentReasoningIcon');
    
    if (content && icon) {
        const isHidden = content.style.display === 'none';
        content.style.display = isHidden ? 'block' : 'none';
        icon.textContent = isHidden ? '▼' : '▶';
    }
}

// Section renderers for agent outputs
function renderMacroSection(macro) {
    const sentiment = macro.market_sentiment || 'neutral';
    const sentimentColor = sentiment.includes('bullish') ? 'var(--success)' : 
                          sentiment.includes('bearish') ? 'var(--danger)' : 'var(--warning)';

    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title">🌍 Macroeconomic Analysis</div>
                <span style="color: ${sentimentColor}; font-weight: 600; text-transform: uppercase;">
                    ${sentiment}
                </span>
            </div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value ${sentiment.includes('bullish') ? 'positive' : 'neutral'}">
                        ${macro.confidence_score || '-'}%
                    </div>
                    <div class="metric-label">Confidence</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${macro.economic_summary?.gdp_assessment || '-'}</div>
                    <div class="metric-label">GDP</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${macro.economic_summary?.inflation_assessment || '-'}</div>
                    <div class="metric-label">Inflation</div>
                </div>
            </div>
            ${macro.sector_implications?.favored ? `
                <div style="margin-top: 16px;">
                    <strong>Favored Sectors:</strong>
                    ${macro.sector_implications.favored.map(s => 
                        `<span class="sector-badge" style="margin: 0 4px;">${s}</span>`
                    ).join('')}
                </div>
            ` : ''}
            ${macro.recommendation ? `
                <p style="margin-top: 12px; color: var(--text-secondary); font-style: italic;">
                    ${macro.recommendation}
                </p>
            ` : ''}
        </div>
    `;
}

function renderSectorsSection(sectors) {
    const sectorList = sectors.sectors || sectors.top_sectors || [];
    
    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title">🎯 Sector Selection</div>
            </div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                ${sectorList.map(s => `
                    <div style="background: var(--bg-input); padding: 16px; border-radius: 8px; min-width: 140px;">
                        <div style="font-weight: 600;">${s.name || s.sector || s}</div>
                        ${s.weight ? `<div style="font-size: 24px; font-weight: 700; color: var(--primary);">${s.weight}%</div>` : ''}
                        ${s.type ? `<div class="sector-badge ${s.type}">${s.type}</div>` : ''}
                    </div>
                `).join('')}
            </div>
            ${sectors.rationale || sectors.selection_rationale ? `
                <p style="margin-top: 16px; color: var(--text-secondary);">
                    ${sectors.rationale || sectors.selection_rationale}
                </p>
            ` : ''}
        </div>
    `;
}

function renderStocksSection(stocks) {
    const stockList = stocks.stocks || [];
    
    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title">📈 Stock Selection Analysis</div>
                <span style="color: var(--text-secondary);">
                    ${stocks.total_candidates_analyzed || stockList.length} candidates analyzed
                </span>
            </div>
            ${stockList.length > 0 ? `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Stock</th>
                                <th>Sector</th>
                                <th>Score</th>
                                <th>Investment Thesis</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stockList.map(s => `
                                <tr>
                                    <td><strong>${s.symbol}</strong> - ${s.name || ''}</td>
                                    <td><span class="sector-badge">${s.sector || '-'}</span></td>
                                    <td><span style="color: var(--success); font-weight: 600;">${s.composite_score || '-'}/100</span></td>
                                    <td style="max-width: 300px; white-space: normal;">${s.investment_thesis || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p>No stocks selected yet.</p>'}
            ${stocks.selection_summary ? `
                <p style="margin-top: 16px; color: var(--text-secondary);">${stocks.selection_summary}</p>
            ` : ''}
        </div>
    `;
}

function renderPerformanceSection(perf) {
    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title">📊 Performance Projections</div>
            </div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value positive">${perf.expected_return || perf.expected_annual_return || '-'}%</div>
                    <div class="metric-label">Expected Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value neutral">${perf.volatility || perf.annual_volatility || '-'}%</div>
                    <div class="metric-label">Volatility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${perf.sharpe_ratio || '-'}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
            </div>
            ${perf.risk_assessment ? `
                <div style="margin-top: 16px; padding: 16px; background: var(--bg-input); border-radius: 8px;">
                    <strong>Risk Assessment:</strong>
                    <p style="margin-top: 8px; color: var(--text-secondary);">${perf.risk_assessment}</p>
                </div>
            ` : ''}
        </div>
    `;
}

function renderBacktestSection(backtest) {
    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title">🔬 Historical Validation</div>
            </div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value ${(backtest.portfolio_return || 0) >= 0 ? 'positive' : 'negative'}">
                        ${backtest.portfolio_return || backtest.total_return || '-'}%
                    </div>
                    <div class="metric-label">Backtest Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${backtest.benchmark_return || backtest.sp500_return || '-'}%</div>
                    <div class="metric-label">S&P 500 Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value ${(backtest.alpha || 0) >= 0 ? 'positive' : 'negative'}">
                        ${backtest.alpha || backtest.excess_return || '-'}%
                    </div>
                    <div class="metric-label">Alpha</div>
                </div>
            </div>
            ${backtest.summary || backtest.conclusion ? `
                <p style="margin-top: 16px; color: var(--text-secondary);">
                    ${backtest.summary || backtest.conclusion}
                </p>
            ` : ''}
        </div>
    `;
}

// Render charts
function renderCharts(portfolio) {
    const positions = portfolio.positions || [];
    
    // Build sector data
    const sectorData = positions.reduce((acc, p) => {
        const sector = p.sector || 'Other';
        acc[sector] = (acc[sector] || 0) + (p.weight || 0);
        return acc;
    }, {});

    const colors = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#9334e6', '#e91e63', '#00bcd4', '#ff9800'];

    // Sector pie chart
    if (sectorChart) sectorChart.destroy();
    const sectorCtx = document.getElementById('sectorChart')?.getContext('2d');
    if (sectorCtx && Object.keys(sectorData).length > 0) {
        sectorChart = new Chart(sectorCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(sectorData),
                datasets: [{
                    data: Object.values(sectorData),
                    backgroundColor: colors.slice(0, Object.keys(sectorData).length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#e8eaed', padding: 12, font: { size: 12 } }
                    }
                }
            }
        });
    }

    // Composition bar chart
    if (compositionChart) compositionChart.destroy();
    const compCtx = document.getElementById('compositionChart')?.getContext('2d');
    if (compCtx && positions.length > 0) {
        compositionChart = new Chart(compCtx, {
            type: 'bar',
            data: {
                labels: positions.map(s => s.symbol),
                datasets: [{
                    label: 'Weight (%)',
                    data: positions.map(s => s.weight || 0),
                    backgroundColor: '#1a73e8',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: '#3c4043' }, ticks: { color: '#9aa0a6' } },
                    y: { grid: { display: false }, ticks: { color: '#e8eaed' } }
                }
            }
        });
    }
}

// Tab switching
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[onclick="switchTab('${tab}')"]`)?.classList.add('active');

    const tabs = ['overview', 'holdings', 'analysis'];
    tabs.forEach(t => {
        const el = document.getElementById(`${t}Tab`);
        if (el) {
            el.style.display = t === tab ? 'block' : 'none';
        }
    });
}

// Loading overlay
function showLoading() {
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.add('active');
    }
    if (elements.generateBtn) {
        elements.generateBtn.disabled = true;
    }

    // Animate loading steps
    const steps = ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7'];
    let currentStep = 0;

    workflowInterval = setInterval(() => {
        if (currentStep > 0 && currentStep <= steps.length) {
            const prevEl = document.getElementById(steps[currentStep - 1]);
            if (prevEl) {
                prevEl.classList.remove('active');
                prevEl.classList.add('done');
            }
        }
        if (currentStep < steps.length) {
            const currEl = document.getElementById(steps[currentStep]);
            if (currEl) {
                currEl.classList.add('active');
            }
            currentStep++;
        }
    }, 2000);
}

function hideLoading() {
    clearInterval(workflowInterval);
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.remove('active');
    }
    if (elements.generateBtn) {
        elements.generateBtn.disabled = false;
    }
    // Reset step states
    ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('active', 'done');
        }
    });
}

// Reset form
function resetForm() {
    portfolioData = null;
    if (elements.profileForm) {
        elements.profileForm.reset();
    }
    if (elements.emptyState) {
        elements.emptyState.style.display = 'block';
    }
    ['overviewTab', 'holdingsTab', 'analysisTab'].forEach(tab => {
        if (elements[tab]) {
            elements[tab].style.display = 'none';
        }
    });
    // Hide download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'none';
    }
    // Reset stat cards to default state
    ['statCapital', 'statPositions', 'statSectors', 'statRisk'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '-';
    });
    // Clear holdings table
    const tbody = document.getElementById('holdingsTable');
    if (tbody) tbody.innerHTML = '';
    // Clear analysis content
    const analysisContent = document.getElementById('analysisContent');
    if (analysisContent) analysisContent.innerHTML = '';
    // Destroy charts and clear references
    if (sectorChart) { sectorChart.destroy(); sectorChart = null; }
    if (compositionChart) { compositionChart.destroy(); compositionChart = null; }
    checkApiHealth();
}

// Utility functions
function getSectorType(sector) {
    const defensive = ['Utilities', 'Consumer Staples', 'Healthcare'];
    const growth = ['Technology', 'Consumer Discretionary', 'Communication Services'];
    const income = ['Real Estate', 'Energy'];
    
    if (defensive.includes(sector)) return 'defensive';
    if (growth.includes(sector)) return 'growth';
    if (income.includes(sector)) return 'income';
    return '';
}

function formatMarkdown(text) {
    if (!text) return '';
    
    // Basic markdown to HTML conversion
    let html = text
        // Escape HTML
        .replace(/</g, '&lt;').replace(/>/g, '&gt;')
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        // Inline code
        .replace(/`(.*?)`/g, '<code>$1</code>')
        // Lists
        .replace(/^\s*[-*] (.*$)/gm, '<li>$1</li>')
        // Numbered lists
        .replace(/^\s*\d+\. (.*$)/gm, '<li>$1</li>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // Wrap in paragraph
    html = '<p>' + html + '</p>';
    
    // Fix list wrapping
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    
    return html;
}

function showError(message) {
    alert(message);
}

// Generate PDF of the portfolio
function downloadPortfolioPDF() {
    if (!portfolioData) {
        showError('No portfolio data to download');
        return;
    }

    const { profile, portfolio, macro_outlook, top_sectors, selected_stocks, performance_report, backtest_results, final_report, raw_response } = portfolioData;
    const positions = portfolio?.positions || [];
    const totalValue = positions.reduce((sum, p) => sum + (p.value || 0), 0);
    const sectors = [...new Set(positions.map(p => p.sector).filter(Boolean))];

    // Build PDF content
    const pdfContent = document.createElement('div');
    pdfContent.style.cssText = 'font-family: Arial, sans-serif; color: #333; padding: 20px; max-width: 800px;';
    
    // Header
    pdfContent.innerHTML = `
        <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #1a73e8; padding-bottom: 20px;">
            <h1 style="color: #1a73e8; margin: 0;">📈 Portfolio Investment Report</h1>
            <p style="color: #666; margin-top: 8px;">Generated by AI Portfolio Manager</p>
            <p style="color: #999; font-size: 12px;">Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>

        <!-- Investment Profile Section -->
        <div style="margin-bottom: 30px; background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <h2 style="color: #1a73e8; margin-top: 0; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">📋 Investment Profile</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Investment Capital:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">$${profile?.capital?.toLocaleString() || '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Investment Goal:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">${profile?.investment_goal?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Time Horizon:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">${profile?.time_horizon?.replace(/_/g, ' ') || '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Risk Score:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">${profile?.risk_score || '-'}/10 (${profile?.risk_category || '-'})</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Max Acceptable Loss:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">${profile?.max_loss_percent || '-'}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Experience Level:</strong></td>
                    <td style="padding: 8px 0; text-align: right;">${profile?.investment_experience?.replace(/\b\w/g, l => l.toUpperCase()) || '-'}</td>
                </tr>
            </table>
        </div>

        <!-- Portfolio Overview Section -->
        <div style="margin-bottom: 30px;">
            <h2 style="color: #34a853; margin-top: 0; border-bottom: 2px solid #34a853; padding-bottom: 8px;">📊 Portfolio Overview</h2>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 150px; background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #34a853;">$${totalValue.toLocaleString()}</div>
                    <div style="color: #666; font-size: 12px;">Total Invested</div>
                </div>
                <div style="flex: 1; min-width: 150px; background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #1a73e8;">${positions.length}</div>
                    <div style="color: #666; font-size: 12px;">Positions</div>
                </div>
                <div style="flex: 1; min-width: 150px; background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #fb8c00;">${sectors.length}</div>
                    <div style="color: #666; font-size: 12px;">Sectors</div>
                </div>
            </div>
        </div>

        <!-- Holdings Section -->
        <div style="margin-bottom: 30px;">
            <h2 style="color: #9c27b0; margin-top: 0; border-bottom: 2px solid #9c27b0; padding-bottom: 8px;">💼 Portfolio Holdings</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Symbol</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Name</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Sector</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Shares</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Value</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Weight</th>
                    </tr>
                </thead>
                <tbody>
                    ${positions.map(h => {
                        const value = h.value || (h.shares * h.price);
                        const weight = h.weight || (profile?.capital > 0 ? (value / profile.capital) * 100 : 0);
                        return `
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">${h.symbol || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">${h.name || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">${h.sector || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">${h.shares || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">$${h.price?.toFixed(2) || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">$${value?.toLocaleString() || '-'}</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">${weight?.toFixed(1) || 0}%</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>

        ${macro_outlook ? `
        <!-- Market Analysis Section -->
        <div style="margin-bottom: 30px; background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <h2 style="color: #00bcd4; margin-top: 0; border-bottom: 2px solid #00bcd4; padding-bottom: 8px;">🌍 Market Analysis</h2>
            <p><strong>Market Sentiment:</strong> <span style="color: ${macro_outlook.market_sentiment?.includes('bullish') ? '#34a853' : macro_outlook.market_sentiment?.includes('bearish') ? '#ea4335' : '#fb8c00'}; text-transform: uppercase;">${macro_outlook.market_sentiment || '-'}</span></p>
            <p><strong>Confidence:</strong> ${macro_outlook.confidence_score || '-'}%</p>
            ${macro_outlook.recommendation ? `<p><strong>Recommendation:</strong> ${macro_outlook.recommendation}</p>` : ''}
            ${macro_outlook.sector_implications?.favored ? `<p><strong>Favored Sectors:</strong> ${macro_outlook.sector_implications.favored.join(', ')}</p>` : ''}
        </div>
        ` : ''}

        ${performance_report ? `
        <!-- Performance Projections -->
        <div style="margin-bottom: 30px;">
            <h2 style="color: #ff9800; margin-top: 0; border-bottom: 2px solid #ff9800; padding-bottom: 8px;">📈 Performance Projections</h2>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 120px; background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 20px; font-weight: bold; color: #34a853;">${performance_report.expected_return || performance_report.expected_annual_return || '-'}%</div>
                    <div style="color: #666; font-size: 11px;">Expected Return</div>
                </div>
                <div style="flex: 1; min-width: 120px; background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 20px; font-weight: bold; color: #fb8c00;">${performance_report.volatility || performance_report.annual_volatility || '-'}%</div>
                    <div style="color: #666; font-size: 11px;">Volatility</div>
                </div>
                <div style="flex: 1; min-width: 120px; background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 20px; font-weight: bold; color: #1a73e8;">${performance_report.sharpe_ratio || '-'}</div>
                    <div style="color: #666; font-size: 11px;">Sharpe Ratio</div>
                </div>
            </div>
        </div>
        ` : ''}

        ${backtest_results ? `
        <!-- Backtest Results -->
        <div style="margin-bottom: 30px; background: #f3e5f5; padding: 20px; border-radius: 8px;">
            <h2 style="color: #9c27b0; margin-top: 0; border-bottom: 2px solid #9c27b0; padding-bottom: 8px;">🔬 Historical Backtest</h2>
            <p><strong>Portfolio Return:</strong> ${backtest_results.portfolio_return || backtest_results.total_return || '-'}%</p>
            <p><strong>Benchmark (S&P 500):</strong> ${backtest_results.benchmark_return || backtest_results.sp500_return || '-'}%</p>
            <p><strong>Alpha:</strong> ${backtest_results.alpha || backtest_results.excess_return || '-'}%</p>
        </div>
        ` : ''}

        <!-- Full Report Section -->
        ${(final_report || raw_response) ? `
        <div style="margin-bottom: 30px; page-break-before: always;">
            <h2 style="color: #1a73e8; margin-top: 0; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">📄 Full Investment Report</h2>
            <div style="white-space: pre-wrap; font-size: 13px; line-height: 1.6;">
                ${cleanReportForPDF(final_report || raw_response)}
            </div>
        </div>
        ` : ''}

        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #eee; text-align: center; color: #999; font-size: 11px;">
            <p>This portfolio recommendation is based on algorithmic analysis and historical data.</p>
            <p>Past performance is not indicative of future results. All investments carry risk including potential loss of principal.</p>
            <p style="margin-top: 10px;">Generated by AI Portfolio Manager | ${new Date().toISOString()}</p>
        </div>
    `;

    // PDF options
    const opt = {
        margin: [10, 10, 10, 10],
        filename: `portfolio_report_${new Date().toISOString().slice(0, 10)}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    // Generate PDF
    html2pdf().set(opt).from(pdfContent).save();
}

// Clean report for PDF (remove JSON blocks)
function cleanReportForPDF(text) {
    if (!text) return '';
    
    // Remove JSON code blocks
    let cleaned = text.replace(/```json[\s\S]*?```/g, '');
    
    // Remove confirmation messages
    cleaned = cleaned.replace(/^I have your profile\..*?\n+/i, '');
    cleaned = cleaned.replace(/^I cannot generate.*?\n+/gi, '');
    
    // Find where the actual report starts
    const reportStart = cleaned.search(/^#\s+Portfolio|^#\s+Investment|Executive Summary/im);
    if (reportStart > 0) {
        cleaned = cleaned.substring(reportStart);
    }
    
    // Convert basic markdown to readable text
    cleaned = cleaned
        .replace(/^### (.*$)/gm, '\n$1\n')
        .replace(/^## (.*$)/gm, '\n$1\n' + '─'.repeat(40) + '\n')
        .replace(/^# (.*$)/gm, '\n$1\n' + '═'.repeat(40) + '\n')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/`(.*?)`/g, '$1');
    
    // Clean up extra whitespace
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n').trim();
    
    return cleaned;
}

// Export functions to global scope for HTML onclick handlers
window.generatePortfolio = generatePortfolio;
window.switchTab = switchTab;
window.resetForm = resetForm;
window.toggleAgentReasoning = toggleAgentReasoning;
window.downloadPortfolioPDF = downloadPortfolioPDF;

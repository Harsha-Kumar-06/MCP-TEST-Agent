"""
Flask Web UI for Portfolio Swarm System
Interactive web interface for portfolio optimization
Now powered by Google Gemini AI

Run with: python flask_ui.py
Then open: http://localhost:5000
"""
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import json
import os
import tempfile
from werkzeug.utils import secure_filename
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.config import cost_tracker
from portfolio_swarm.strategies import (
    OptimizationStrategy, StrategyType, get_strategy, 
    create_custom_strategy, list_available_strategies, STRATEGY_TEMPLATES
)

def log_activity(message):
    """Print activity to terminal for visibility"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.input_parser import PortfolioParser

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'csv', 'json', 'yaml', 'yml'}

# Global progress tracking (keyed by session ID)
optimization_progress = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_sample_portfolio() -> Portfolio:
    """Create sample portfolio"""
    from demo import create_sample_portfolio as demo_portfolio
    return demo_portfolio()

def update_progress(session_id: str, iteration: int, max_iterations: int, phase: str, details: str = ""):
    """Update optimization progress for a session"""
    optimization_progress[session_id] = {
        'iteration': iteration,
        'max_iterations': max_iterations,
        'phase': phase,
        'details': details,
        'progress_percent': (iteration / max_iterations * 100) if max_iterations > 0 else 0,
        'timestamp': datetime.now().isoformat()
    }

def calculate_recommended_threshold(portfolio_data: dict) -> dict:
    """
    Calculate recommended consensus threshold based on portfolio characteristics
    
    Returns dict with:
        - recommended_threshold: float (0.6-0.8)
        - recommended_iterations: int (5-15)
        - reasoning: str explaining the recommendation
    """
    total_value = portfolio_data.get('total_value', 0)
    num_positions = portfolio_data.get('num_positions', 0)
    beta = portfolio_data.get('beta', 1.0)
    esg_score = portfolio_data.get('esg_score', 50)
    
    # Base threshold starts at 0.60 (60% = 3/5 agents)
    threshold = 0.60
    iterations = 10
    reasons = []
    
    # Factor 1: Portfolio Size - Larger portfolios need higher consensus
    if total_value > 50_000_000:  # $50M+
        threshold += 0.15
        iterations += 3
        reasons.append(f"Large portfolio (${total_value/1_000_000:.1f}M) requires higher consensus")
    elif total_value > 10_000_000:  # $10M+
        threshold += 0.10
        iterations += 2
        reasons.append(f"Medium-large portfolio (${total_value/1_000_000:.1f}M) needs careful review")
    elif total_value < 1_000_000:  # <$1M
        threshold -= 0.05
        iterations -= 2
        reasons.append(f"Smaller portfolio (${total_value/1_000:.0f}K) allows faster consensus")
    
    # Factor 2: Portfolio Complexity - More positions need more debate
    if num_positions > 20:
        threshold += 0.05
        iterations += 2
        reasons.append(f"Complex portfolio ({num_positions} positions) needs thorough analysis")
    elif num_positions > 10:
        threshold += 0.02
        iterations += 1
        reasons.append(f"Moderate complexity ({num_positions} positions)")
    elif num_positions < 5:
        threshold -= 0.05
        iterations -= 1
        reasons.append(f"Simple portfolio ({num_positions} positions) converges faster")
    
    # Factor 3: Risk Profile - Higher beta = higher risk = higher threshold
    if beta > 1.5:
        threshold += 0.10
        iterations += 2
        reasons.append(f"High volatility portfolio (β={beta:.2f}) requires stricter consensus")
    elif beta > 1.2:
        threshold += 0.05
        iterations += 1
        reasons.append(f"Above-market volatility (β={beta:.2f})")
    elif beta < 0.8:
        threshold -= 0.05
        reasons.append(f"Conservative portfolio (β={beta:.2f})")
    
    # Factor 4: ESG Compliance - Poor ESG needs careful rebalancing
    if esg_score < 50:
        threshold += 0.05
        iterations += 1
        reasons.append(f"Low ESG score ({esg_score:.0f}) needs compliance focus")
    elif esg_score > 75:
        reasons.append(f"Strong ESG score ({esg_score:.0f}) shows good governance")
    
    # Factor 5: Sector Concentration Risk
    sector_allocation = portfolio_data.get('sector_allocation', {})
    max_sector_weight = max(sector_allocation.values()) if sector_allocation else 0
    if max_sector_weight > 0.5:  # >50% in one sector
        threshold += 0.10
        iterations += 2
        sector_name = max(sector_allocation, key=sector_allocation.get)
        reasons.append(f"High sector concentration ({sector_name}: {max_sector_weight*100:.0f}%) increases risk")
    elif max_sector_weight > 0.4:  # >40% in one sector
        threshold += 0.05
        iterations += 1
        sector_name = max(sector_allocation, key=sector_allocation.get)
        reasons.append(f"Moderate sector concentration ({sector_name}: {max_sector_weight*100:.0f}%)")
    
    # Cap thresholds at sensible limits
    threshold = max(0.55, min(0.85, threshold))  # Keep between 55%-85%
    iterations = max(5, min(15, iterations))      # Keep between 5-15 iterations
    
    # Determine strategy based on final threshold
    if threshold >= 0.75:
        strategy = "Strict Consensus (High Bar)"
        explanation = "Requires 4 out of 5 agents to approve. Best for high-risk/high-value portfolios."
    elif threshold >= 0.65:
        strategy = "Balanced Consensus (Recommended)"
        explanation = "Requires 3-4 out of 5 agents to approve. Good balance of safety and efficiency."
    else:
        strategy = "Fast Consensus (Lower Bar)"
        explanation = "Requires 3 out of 5 agents to approve. Suitable for simpler portfolios."
    
    return {
        'recommended_threshold': round(threshold, 2),
        'recommended_iterations': iterations,
        'strategy': strategy,
        'explanation': explanation,
        'reasoning': reasons,
        'analysis': {
            'portfolio_value': total_value,
            'num_positions': num_positions,
            'beta': beta,
            'esg_score': esg_score,
            'max_sector_concentration': max_sector_weight
        }
    }

@app.route('/')
def index():
    """Main page"""
    log_activity("📱 User accessed main page")
    return render_template('index.html')

@app.route('/load_sample', methods=['POST'])
def load_sample():
    """Load sample portfolio"""
    log_activity("📊 Loading sample portfolio...")
    try:
        portfolio = create_sample_portfolio()
        log_activity(f"✅ Sample portfolio loaded: {len(portfolio.positions)} positions, ${portfolio.total_value:,.0f} value")
        
        portfolio_data = {
            'total_value': portfolio.total_value,
            'beta': portfolio.portfolio_beta,
            'esg_score': portfolio.average_esg_score,
            'num_positions': len(portfolio.positions),
            'cash': portfolio.cash,
            'policy_limits': portfolio.policy_limits,
            'positions': [
                {
                    'ticker': pos.ticker,
                    'shares': pos.shares,
                    'current_price': pos.current_price,
                    'cost_basis': pos.cost_basis,
                    'market_value': pos.market_value,
                    'sector': pos.sector,
                    'esg_score': pos.esg_score,
                    'beta': pos.beta
                }
                for pos in portfolio.positions
            ],
            'sector_allocation': portfolio.sector_allocation
        }
        session['portfolio_data'] = portfolio_data
        log_activity(f"   Tickers: {[p['ticker'] for p in portfolio_data['positions']]}")
        
        # Calculate recommended settings
        recommendation = calculate_recommended_threshold(portfolio_data)
        log_activity(f"   💡 Recommended: {recommendation['recommended_threshold']*100:.0f}% threshold, {recommendation['recommended_iterations']} iterations")
        
        return jsonify({
            'success': True, 
            'portfolio': portfolio_data,
            'recommendation': recommendation
        })
    except Exception as e:
        log_activity(f"❌ Error loading sample: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/optimization_progress', methods=['GET'])
def get_optimization_progress():
    """Poll optimization progress"""
    from flask import session as flask_session
    session_id = flask_session.get('session_id', 'default')
    
    if session_id in optimization_progress:
        return jsonify({'success': True, 'progress': optimization_progress[session_id]})
    else:
        return jsonify({'success': False, 'progress': None})

@app.route('/parse_text', methods=['POST'])
def parse_text():
    """Parse text description of portfolio"""
    try:
        data = request.json or {}
        text = data.get('text', '')
        log_activity("📝 Parsing portfolio text...")
        log_activity(f"   Text length: {len(text)} characters")
        
        # Import the Gemini-enhanced text parser with latest API
        from portfolio_swarm.text_parser_gemini import parse_portfolio_text
        portfolio = parse_portfolio_text(text)
        
        log_activity(f"✅ Successfully parsed {len(portfolio.positions)} positions")
        if len(portfolio.positions) > 0:
            log_activity(f"   Tickers: {[p.ticker for p in portfolio.positions]}")
        
        portfolio_data = {
            'total_value': portfolio.total_value,
            'beta': portfolio.portfolio_beta,
            'esg_score': portfolio.average_esg_score,
            'num_positions': len(portfolio.positions),
            'cash': portfolio.cash,
            'policy_limits': portfolio.policy_limits,
            'positions': [
                {
                    'ticker': pos.ticker,
                    'shares': pos.shares,
                    'current_price': pos.current_price,
                    'cost_basis': pos.cost_basis,
                    'market_value': pos.market_value,
                    'sector': pos.sector,
                    'esg_score': pos.esg_score,
                    'beta': pos.beta
                }
                for pos in portfolio.positions
            ],
            'sector_allocation': portfolio.sector_allocation
        }
        session['portfolio_data'] = portfolio_data
        
        # Calculate recommended settings
        recommendation = calculate_recommended_threshold(portfolio_data)
        log_activity(f"   💡 Recommended: {recommendation['recommended_threshold']*100:.0f}% threshold, {recommendation['recommended_iterations']} iterations")
        
        return jsonify({
            'success': True, 
            'portfolio': portfolio_data,
            'recommendation': recommendation
        })
    except Exception as e:
        log_activity(f"❌ Error parsing text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Upload and parse portfolio file (CSV, JSON, YAML)"""
    try:
        if 'file' not in request.files:
            log_activity("❌ No file in request")
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            log_activity("❌ Empty filename")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        log_activity(f"📁 Uploading file: {file.filename}")
        
        if not file.filename or not allowed_file(file.filename):
            log_activity(f"❌ Invalid file type: {file.filename}")
            return jsonify({'success': False, 'error': 'Invalid file type. Use CSV, JSON, or YAML'})
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        suffix = os.path.splitext(filename)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        log_activity(f"   Parsing {suffix} file...")
        
        # Parse the file
        parser = PortfolioParser()
        portfolio = parser.parse_file(tmp_path)
        
        log_activity(f"✅ File parsed: {len(portfolio.positions)} positions, ${portfolio.total_value:,.0f} value")
        if len(portfolio.positions) > 0:
            log_activity(f"   Tickers: {[p.ticker for p in portfolio.positions]}")
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Convert to session data
        portfolio_data = {
            'total_value': portfolio.total_value,
            'beta': portfolio.portfolio_beta,
            'esg_score': portfolio.average_esg_score,
            'num_positions': len(portfolio.positions),
            'cash': portfolio.cash,
            'policy_limits': portfolio.policy_limits,
            'positions': [
                {
                    'ticker': pos.ticker,
                    'shares': pos.shares,
                    'current_price': pos.current_price,
                    'cost_basis': pos.cost_basis,
                    'market_value': pos.market_value,
                    'sector': pos.sector,
                    'esg_score': pos.esg_score,
                    'beta': pos.beta
                }
                for pos in portfolio.positions
            ],
            'sector_allocation': portfolio.sector_allocation
        }
        session['portfolio_data'] = portfolio_data
        
        # Get validation warnings
        warnings = parser.validate_portfolio(portfolio)
        
        if warnings:
            log_activity(f"⚠️  {len(warnings)} validation warnings")
            for w in warnings:
                log_activity(f"     • {w}")
        
        # Calculate recommended settings
        recommendation = calculate_recommended_threshold(portfolio_data)
        log_activity(f"   💡 Recommended: {recommendation['recommended_threshold']*100:.0f}% threshold, {recommendation['recommended_iterations']} iterations")
        
        return jsonify({
            'success': True,
            'portfolio': portfolio_data,
            'warnings': warnings,
            'recommendation': recommendation
        })
    except Exception as e:
        log_activity(f"❌ Error uploading file: {str(e)}")
        import traceback
        log_activity(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/get_strategies', methods=['GET'])
def get_strategies():
    """Get available optimization strategies"""
    log_activity("🎯 Fetching available strategies...")
    try:
        strategies = []
        for strategy_type in StrategyType:
            if strategy_type == StrategyType.CUSTOM:
                continue
            strategy = get_strategy(strategy_type)
            
            # Determine risk level
            if strategy.max_drawdown_tolerance >= 0.30:
                risk_level = "High"
            elif strategy.max_drawdown_tolerance >= 0.18:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            strategies.append({
                'type': strategy_type.value,
                'name': strategy.name,
                'description': strategy.description,
                'target_beta': strategy.target_beta,
                'risk_level': risk_level,
                'max_drawdown': strategy.max_drawdown_tolerance,
                'min_esg': strategy.min_esg_score,
                'priorities': strategy.priorities
            })
        
        log_activity(f"✅ Loaded {len(strategies)} strategies")
        return jsonify({'success': True, 'strategies': strategies})
    except Exception as e:
        log_activity(f"❌ Error loading strategies: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_strategy', methods=['POST'])
def set_strategy():
    """Set the optimization strategy"""
    try:
        data = request.json or {}
        strategy_type = data.get('strategy_type', 'balanced')
        
        log_activity(f"🎯 Setting strategy: {strategy_type}")
        
        # Get the strategy
        try:
            strategy_enum = StrategyType(strategy_type)
            strategy = get_strategy(strategy_enum)
        except ValueError:
            strategy = get_strategy(StrategyType.BALANCED)
        
        # Store in session
        session['selected_strategy'] = {
            'type': strategy.strategy_type.value,
            'name': strategy.name,
            'description': strategy.description,
            'target_beta': strategy.target_beta,
            'priorities': strategy.priorities
        }
        
        log_activity(f"✅ Strategy set to: {strategy.name}")
        
        return jsonify({
            'success': True,
            'strategy': session['selected_strategy']
        })
    except Exception as e:
        log_activity(f"❌ Error setting strategy: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/optimize', methods=['POST'])
def optimize():
    """Run optimization"""
    import time
    import uuid
    start_time = time.time()
    
    try:
        data = request.json
        
        # Get or create session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        
        log_activity("\n" + "="*60)
        log_activity("🤖 STARTING OPTIMIZATION")
        log_activity("="*60)
        
        # Get portfolio
        portfolio_data = session.get('portfolio_data')
        if not portfolio_data:
            log_activity("❌ No portfolio loaded")
            return jsonify({'success': False, 'error': 'No portfolio loaded'})
        
        log_activity(f"📊 Portfolio: {portfolio_data['num_positions']} positions, ${portfolio_data['total_value']:,.0f}")
        
        # Reconstruct portfolio from session data
        positions = []
        for pos_data in portfolio_data['positions']:
            pos = Position(
                ticker=pos_data['ticker'],
                shares=pos_data['shares'],
                current_price=pos_data['current_price'],
                cost_basis=pos_data.get('cost_basis', pos_data['current_price']),
                acquisition_date=datetime.now() - timedelta(days=365),
                sector=pos_data['sector'],
                esg_score=pos_data['esg_score'],
                beta=pos_data.get('beta', 1.0)
            )
            positions.append(pos)
        
        # Create portfolio with cash and policy limits
        cash = portfolio_data.get('cash', 1000000.0)  # Default $1M if not specified
        policy_limits = portfolio_data.get('policy_limits', {"technology_limit": 30.0})
        
        portfolio = Portfolio(
            positions=positions,
            cash=cash,
            policy_limits=policy_limits
        )
        
        # Get configuration (data is guaranteed non-None from earlier check)
        config = data if data else {}
        question = config.get('question', 'Optimize my portfolio for better returns while managing risk')
        max_iterations = config.get('max_iterations', 10)
        min_iterations = config.get('min_iterations', 1)  # Minimum iterations before consensus allowed
        consensus_threshold = config.get('consensus_threshold', 0.6)
        
        log_activity(f"❓ Question: {question}")
        log_activity(f"⚙️  Iterations: min={min_iterations}, max={max_iterations}, Consensus threshold: {consensus_threshold}")
        
        # Create communication bus first
        bus = CommunicationBus()
        
        # Create agents based on selection (all need the bus)
        agents = []
        active_agents = []
        if config.get('use_market', True):
            agents.append(MarketAnalysisAgent(bus))
            active_agents.append('Market Analysis')
        if config.get('use_risk', True):
            agents.append(RiskAssessmentAgent(bus))
            active_agents.append('Risk Assessment')
        if config.get('use_tax', True):
            agents.append(TaxStrategyAgent(bus))
            active_agents.append('Tax Strategy')
        if config.get('use_esg', True):
            agents.append(ESGComplianceAgent(bus))
            active_agents.append('ESG Compliance')
        if config.get('use_trading', True):
            agents.append(AlgorithmicTradingAgent(bus))
            active_agents.append('Algorithmic Trading')
        
        # Validate minimum 2 agents for meaningful multi-agent debate
        if len(agents) < 2:
            log_activity(f"❌ Only {len(agents)} agent(s) selected - minimum 2 required!")
            return jsonify({
                'success': False,
                'error': f'Multi-agent debate requires at least 2 active agents ({len(agents)} selected). '
                         'A single agent automatically results in 100% consensus, defeating the purpose of swarm intelligence.'
            })
        
        log_activity(f"🤖 Active agents ({len(agents)}): {', '.join(active_agents)}")
        
        # Get selected strategy from session or config
        selected_strategy = None
        strategy_name = "Balanced"
        
        if 'selected_strategy' in session:
            strategy_data = session['selected_strategy']
            strategy_type_str = strategy_data.get('type', 'balanced')
            try:
                strategy_enum = StrategyType(strategy_type_str)
                selected_strategy = get_strategy(strategy_enum)
                strategy_name = selected_strategy.name
            except ValueError:
                selected_strategy = get_strategy(StrategyType.BALANCED)
                strategy_name = "Balanced"
        elif config.get('strategy_type'):
            try:
                strategy_enum = StrategyType(config.get('strategy_type'))
                selected_strategy = get_strategy(strategy_enum)
                strategy_name = selected_strategy.name
            except ValueError:
                selected_strategy = get_strategy(StrategyType.BALANCED)
                strategy_name = "Balanced"
        else:
            selected_strategy = get_strategy(StrategyType.BALANCED)
        
        log_activity(f"🎯 Using strategy: {strategy_name}")
        
        # Progress callback for real-time updates
        def progress_callback(iteration, phase, details):
            update_progress(session_id, iteration, max_iterations, phase, details)
            log_activity(f"   📈 Iteration {iteration}/{max_iterations} - {phase}: {details}")
        
        # Create orchestrator with progress callback and strategy
        orchestrator = SwarmOrchestrator(
            agents=agents,
            max_iterations=max_iterations,
            min_iterations=min_iterations,
            consensus_threshold=consensus_threshold,
            progress_callback=progress_callback,
            strategy=selected_strategy
        )
        
        log_activity("🚀 Running swarm optimization...")
        
        # Run optimization
        result = orchestrator.run_rebalancing_swarm(portfolio)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        log_activity("\n" + "-"*60)
        log_activity(f"✅ Optimization complete!")
        log_activity(f"   Time elapsed: {elapsed_time:.1f} seconds")
        log_activity(f"   Consensus reached: {result.approved}")
        log_activity(f"   Iterations: {result.iteration}")
        log_activity(f"   Final approval rate: {result.approval_rate:.2%}")
        
        if result.trade_plan:
            log_activity(f"   Trades proposed: {len(result.trade_plan.trades)}")
            for trade in result.trade_plan.trades:
                log_activity(f"      • {trade.action.upper()} {trade.ticker}: {trade.shares} shares")
        
        log_activity("\n📊 Agent Votes:")
        if result.votes:
            approve_count = sum(1 for v in result.votes if v.vote.value == "approve")
            reject_count = sum(1 for v in result.votes if v.vote.value == "reject")
            abstain_count = sum(1 for v in result.votes if v.vote.value == "abstain")
            
            log_activity(f"   Summary: ✅ {approve_count} Approve, ❌ {reject_count} Reject, ⚪ {abstain_count} Abstain")
            log_activity("")
            for vote in result.votes:
                agent_name = vote.agent_type.value.replace('_', ' ').title()
                vote_value = vote.vote.value
                symbol = "✅" if vote_value == "approve" else ("❌" if vote_value == "reject" else "⚪")
                log_activity(f"   {symbol} {agent_name}: {vote_value.upper()}")
                log_activity(f"      Rationale: {vote.rationale[:150]}..." if len(vote.rationale) > 150 else f"      Rationale: {vote.rationale}")
                if vote.concerns:
                    log_activity(f"      Concerns: {', '.join(vote.concerns[:2])}")
        else:
            log_activity("   No votes recorded")
        
        # Display AI cost tracking summary
        cost_summary = cost_tracker.get_summary()
        log_activity("\n💰 AI API Usage Cost:")
        log_activity(f"   Total Requests: {cost_summary['total_requests']}")
        log_activity(f"   Total Tokens: {cost_summary['total_tokens']:,}")
        log_activity(f"   Total Cost: ${cost_summary['total_cost_usd']:.6f}")
        
        log_activity("="*60 + "\n")
        
        # Format result with safe defaults
        cost_summary = cost_tracker.get_summary()
        # Convert 0-indexed iteration to 1-indexed for display (iteration 0 = "1 iteration completed")
        iterations_completed = (result.iteration + 1) if hasattr(result, 'iteration') else 0
        
        # Get iteration history for timeline
        iteration_history = orchestrator.iteration_history if hasattr(orchestrator, 'iteration_history') else []
        
        result_data = {
            'success': result.approved if hasattr(result, 'approved') else False,
            'iterations': iterations_completed,
            'max_iterations': max_iterations,
            'consensus_score': result.approval_rate if hasattr(result, 'approval_rate') else 0.0,
            'elapsed_time': elapsed_time,
            'trades': [
                {
                    'action': trade.action,
                    'ticker': trade.ticker,
                    'shares': trade.shares,
                    'price': trade.estimated_price,
                    'value': trade.notional_value,
                    'rationale': trade.rationale
                }
                for trade in result.trade_plan.trades
            ] if result.trade_plan and hasattr(result.trade_plan, 'trades') else [],
            'votes': [
                {
                    'agent': vote.agent_type.value.replace('_', ' ').title(),
                    'vote': vote.vote.value,
                    'rationale': vote.rationale
                }
                for vote in result.votes
            ] if result.votes else [],
            'trade_plan_summary': {
                'tax_liability': result.trade_plan.expected_tax_liability if result.trade_plan and hasattr(result.trade_plan, 'expected_tax_liability') else 0,
                'execution_cost': result.trade_plan.expected_execution_cost if result.trade_plan and hasattr(result.trade_plan, 'expected_execution_cost') else 0,
                'net_cost': result.trade_plan.net_cost if result.trade_plan and hasattr(result.trade_plan, 'net_cost') else 0,
                'timeline_days': result.trade_plan.execution_timeline_days if result.trade_plan and hasattr(result.trade_plan, 'execution_timeline_days') else 0
            } if result.trade_plan else None,
            'ai_cost_tracking': {
                'total_requests': cost_summary['total_requests'],
                'total_tokens': cost_summary['total_tokens'],
                'cost_usd': cost_summary['total_cost_usd'],
                'agent_breakdown': cost_summary['agent_breakdown']
            },
            'iteration_history': iteration_history,
            'portfolio_before': session.get('portfolio_data', {})
        }
        
        return jsonify(result_data)
    except Exception as e:
        log_activity(f"\n❌ OPTIMIZATION ERROR: {str(e)}")
        import traceback
        log_activity(traceback.format_exc())
        log_activity("="*60 + "\n")
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 Portfolio Swarm Optimizer - Flask UI")
    print("="*60)
    print("\n📡 Starting server...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("\n💡 Features:")
    print("   • Load sample portfolio")
    print("   • Parse text descriptions")
    print("   • Upload CSV/JSON/YAML files")
    print("   • Multi-agent optimization")
    print("   • Real-time terminal logging")
    print("\n📝 All UI actions will be logged below")
    print("💡 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)

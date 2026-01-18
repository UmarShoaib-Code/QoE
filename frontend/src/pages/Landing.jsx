import { Link } from 'react-router-dom'
import { FaChartBar, FaFileExcel, FaCheckCircle, FaCalculator, FaBuilding, FaShieldAlt, FaRocket, FaLock, FaArrowRight, FaDatabase, FaFilter } from 'react-icons/fa'
import './Landing.css'

const Landing = () => {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="header-content">
          <div className="logo">
            <FaChartBar /> QoE Tool
          </div>
          <div className="header-buttons">
            <Link to="/login" className="btn-signin">Sign In</Link>
            <Link to="/signup" className="btn-primary">Get Started</Link>
          </div>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Transform QuickBooks GL Data<br />Into Analyst-Ready Reports
          </h1>
          <p className="hero-subtitle">
            Process General Ledger exports from QuickBooks Desktop and QuickBooks Online. 
            Automatically validate, normalize, and generate professional Excel databooks with 
            EBITDA calculations and account mappings—ready for M&A due diligence.
          </p>
          <div className="hero-cta">
            <Link to="/signup" className="btn-primary btn-large">
              <FaRocket /> Start Processing GL Files
            </Link>
            <Link to="/login" className="btn-secondary btn-large">
              <FaLock /> Sign In
            </Link>
          </div>
        </div>
      </section>

      <section className="features-container">
        <div className="features-header">
          <h2>Complete GL Processing Pipeline</h2>
          <p>From raw QuickBooks exports to professional Excel databooks</p>
        </div>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaFileExcel /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">QuickBooks GL Ingestion</h3>
            <p className="feature-description">
              Automatically processes GL exports from QuickBooks Desktop and QuickBooks Online. 
              Handles account name normalization, parent/subaccount flattening, and removes 
              totals, subtotals, and opening balances.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaCheckCircle /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">Automated Data Validation</h3>
            <p className="feature-description">
              Validates debit/credit balance, date parsing accuracy, and transaction counts. 
              Provides detailed validation reports with key metrics and error identification 
              before proceeding to analysis.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaDatabase /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">Account Mapping & Categorization</h3>
            <p className="feature-description">
              Automatically categorizes accounts into standard categories: Revenue, COGS, 
              OpEx, Other Income/Expense, Taxes, Interest, D&A, and Balance Sheet. 
              Supports multi-level categorization for detailed analysis.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaCalculator /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">EBITDA Calculations</h3>
            <p className="feature-description">
              Automatically calculates Net Income, EBITDA, and Adjusted EBITDA with formula-based 
              calculations. Includes pivot-ready inputs for comprehensive financial analysis and 
              M&A due diligence.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaBuilding /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">Multi-Entity Consolidation</h3>
            <p className="feature-description">
              Process multiple GL files simultaneously and consolidate them by entity. 
              Perfect for companies with multiple subsidiaries or business units requiring 
              consolidated financial analysis.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <div className="feature-icon"><FaShieldAlt /></div>
              <div className="feature-icon-glow"></div>
            </div>
            <h3 className="feature-title">Professional Excel Output</h3>
            <p className="feature-description">
              Generates institutional-grade Excel databooks with multiple formatted tabs: 
              README, Validation Results, GL Clean Data, Account Mapping, EBITDA Calculations, 
              and Pivot Inputs—ready for audit and analysis.
            </p>
          </div>
        </div>
      </section>

      <section className="workflow-section">
        <div className="workflow-container">
          <h2>How It Works</h2>
          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="step-number">1</div>
              <h3>Upload GL Files</h3>
              <p>Upload your QuickBooks Desktop or QuickBooks Online GL export files. Support for multiple files and entities.</p>
            </div>
            <div className="workflow-step">
              <div className="step-number">2</div>
              <h3>Automatic Processing</h3>
              <p>Our engine normalizes account names, validates data quality, and categorizes accounts automatically.</p>
            </div>
            <div className="workflow-step">
              <div className="step-number">3</div>
              <h3>Review Validation</h3>
              <p>Review validation results, key metrics, and any warnings before generating your databook.</p>
            </div>
            <div className="workflow-step">
              <div className="step-number">4</div>
              <h3>Download Excel Databook</h3>
              <p>Download your professional Excel databook with all tabs formatted and ready for analysis.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <h2 className="cta-title">Ready to Process Your GL Data?</h2>
        <p className="cta-subtitle">
          Join M&A professionals who trust QoE Tool for accurate, fast, and reliable 
          General Ledger processing and analysis.
        </p>
        <div className="cta-buttons">
          <Link to="/signup" className="btn-primary btn-large">
            <FaRocket /> Get Started Free
          </Link>
          <Link to="/login" className="btn-secondary btn-large">
            <FaLock /> Sign In
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <p><strong>QoE Tool</strong> - Quality of Earnings Analysis Platform</p>
        <p className="footer-subtitle">
          Professional GL processing for M&A due diligence and financial analysis
        </p>
      </footer>
    </div>
  )
}

export default Landing

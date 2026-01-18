import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FaHome, FaSignOutAlt, FaChartBar, FaFolder, FaUpload, FaCheckCircle, FaTimesCircle, FaExclamationTriangle, FaDownload, FaSpinner, FaRocket, FaBuilding, FaCog } from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import './GLProcessing.css'

const STORAGE_KEY = 'qoe_projects'

const GLProcessing = () => {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [project, setProject] = useState(null)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [entityConfigs, setEntityConfigs] = useState({})
  const [sourceSystem, setSourceSystem] = useState('QuickBooks Online')
  const [processingStatus, setProcessingStatus] = useState('idle')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [validationResult, setValidationResult] = useState(null)
  const [processedData, setProcessedData] = useState(null)
  const [excelFileUrl, setExcelFileUrl] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProject()
  }, [projectId])

  const loadProject = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const projects = JSON.parse(stored)
        const projectIdNum = parseInt(projectId)
        const foundProject = projects.find(p => p.id === projectIdNum)
        if (foundProject) {
          setProject(foundProject)
        } else {
          console.error('Project not found')
          navigate('/dashboard')
        }
      } else {
        console.error('No projects found in localStorage')
        navigate('/dashboard')
      }
    } catch (error) {
      console.error('Failed to load project from localStorage:', error)
      navigate('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files)
    setUploadedFiles(files)
    const configs = {}
    files.forEach(file => {
      const defaultEntity = file.name.replace(/_GL/g, '').replace(/_/g, ' ').replace(/\.[^/.]+$/, '')
      configs[file.name] = defaultEntity
    })
    setEntityConfigs(configs)
  }

  const handleEntityChange = (filename, entityName) => {
    setEntityConfigs({
      ...entityConfigs,
      [filename]: entityName
    })
  }

  const handleProcess = async () => {
    if (uploadedFiles.length === 0) return
    
    const missingEntities = uploadedFiles.filter(f => !entityConfigs[f.name]?.trim())
    if (missingEntities.length > 0) {
      alert(`Please provide entity names for: ${missingEntities.map(f => f.name).join(', ')}`)
      return
    }

    setProcessingStatus('processing')
    setProcessingProgress(10)
    
    const progressInterval = setInterval(() => {
      setProcessingProgress(prev => {
        if (prev >= 90) return prev
        return prev + Math.random() * 15
      })
    }, 500)
    
    try {
      const formData = new FormData()
      uploadedFiles.forEach(file => {
        formData.append('files', file)
      })
      formData.append('source_system', sourceSystem)
      
      const configsArray = Object.entries(entityConfigs).map(([filename, entityName]) => ({
        filename,
        entity_name: entityName
      }))
      formData.append('entity_configs', JSON.stringify(configsArray))

      const response = await api.post(`/projects/${projectId}/process`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token') || '1'}`
        }
      })

      clearInterval(progressInterval)
      setProcessingProgress(100)
      
      setTimeout(() => {
        setValidationResult(response.data.validation_result)
        setProcessedData(response.data.processed_data)
        setProcessingStatus('completed')
        setProcessingProgress(0)
        
        if (response.data.excel_file_url) {
          setExcelFileUrl(response.data.excel_file_url)
        }
      }, 300)
    } catch (error) {
      clearInterval(progressInterval)
      setProcessingStatus('error')
      setProcessingProgress(0)
      alert('Processing failed: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDownload = async () => {
    if (!excelFileUrl || downloading) return
    
    setDownloading(true)
    
    try {
      const url = excelFileUrl.startsWith('http') 
        ? excelFileUrl 
        : excelFileUrl.startsWith('/api') 
          ? `http://localhost:8000${excelFileUrl.replace('/api', '')}`
          : `http://localhost:8000${excelFileUrl}`
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || '1'}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to download file')
      }
      
      const contentLength = response.headers.get('content-length')
      const total = contentLength ? parseInt(contentLength, 10) : 0
      
      const reader = response.body.getReader()
      const chunks = []
      let receivedLength = 0
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        chunks.push(value)
        receivedLength += value.length
        
        if (total > 0) {
          const progress = Math.min(95, (receivedLength / total) * 100)
          setProcessingProgress(progress)
        }
      }
      
      const blob = new Blob(chunks)
      setProcessingProgress(100)
      
      setTimeout(() => {
        const blobUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = blobUrl
        link.download = excelFileUrl.split('/').pop() || 'GL_Databook.xlsx'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(blobUrl)
        setDownloading(false)
        setProcessingProgress(0)
      }, 200)
    } catch (error) {
      console.error('Download failed:', error)
      setDownloading(false)
      setProcessingProgress(0)
      alert('Failed to download file: ' + (error.message || 'Unknown error'))
    }
  }

  if (loading) {
    return (
      <div className="gl-processing-page">
        <div className="loading-container">
          <LoadingSpinner text="Loading project..." />
        </div>
      </div>
    )
  }

  return (
    <div className="gl-processing-page">
      <aside className="processing-sidebar">
        <div className="sidebar-header">
          <h2><FaFolder /> {project?.title || 'Project'}</h2>
          <p>Project ID: {projectId}</p>
        </div>
        <div className="sidebar-content">
          <button onClick={() => navigate('/dashboard')} className="sidebar-button">
            <FaHome /> Dashboard
          </button>
          <button onClick={() => navigate('/')} className="sidebar-button">
            <FaHome /> Home
          </button>
          <button onClick={logout} className="sidebar-button">
            <FaSignOutAlt /> Logout ({user?.username})
          </button>
        </div>
      </aside>

      <main className="processing-main">
        <header className="processing-header">
          <h1><FaChartBar /> QoE Tool - {project?.title || 'Project'}</h1>
          <p>Quality of Earnings Analysis - General Ledger Processing Platform</p>
        </header>

        <div className="processing-content">
          <section className="upload-section">
            <h2><FaUpload /> Step 1: Upload GL Files</h2>
            <div className="upload-area">
              <input
                type="file"
                id="file-upload"
                multiple
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" className="upload-label">
                {uploadedFiles.length > 0
                  ? <><FaCheckCircle /> {uploadedFiles.length} file(s) selected</>
                  : 'Click to upload Excel GL File(s)'}
              </label>
              <p className="upload-hint">
                Upload one or multiple QuickBooks GL export files (QuickBooks Desktop or QuickBooks Online)
              </p>
            </div>

            {uploadedFiles.length > 0 && (
              <>
                <div className="files-list">
                  {uploadedFiles.map((file, idx) => (
                    <div key={idx} className="file-item">
                      <div className="file-info">
                        <strong>{file.name}</strong>
                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="entity-config">
                  <h3><FaBuilding /> Entity Configuration</h3>
                  {uploadedFiles.map((file, idx) => (
                    <div key={idx} className="entity-input-group">
                      <label>Entity name for: {file.name}</label>
                      <input
                        type="text"
                        value={entityConfigs[file.name] || ''}
                        onChange={(e) => handleEntityChange(file.name, e.target.value)}
                        placeholder="Enter entity name..."
                      />
                    </div>
                  ))}
                </div>

                <div className="source-system-config">
                  <h3><FaCog /> Processing Configuration</h3>
                  <select
                    value={sourceSystem}
                    onChange={(e) => setSourceSystem(e.target.value)}
                    className="source-select"
                  >
                    <option value="QuickBooks Online">QuickBooks Online</option>
                    <option value="QuickBooks Desktop">QuickBooks Desktop</option>
                  </select>
                </div>

                <button
                  onClick={handleProcess}
                  disabled={processingStatus === 'processing'}
                  className="btn-primary btn-process"
                >
                  {processingStatus === 'processing' ? <><FaSpinner className="spinning" /> Processing...</> : <><FaRocket /> Process GL Files</>}
                </button>
              </>
            )}
          </section>

          {processingStatus === 'processing' && (
            <div className="processing-status">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${processingProgress}%` }}></div>
              </div>
              <p>Processing your GL files... {Math.round(processingProgress)}%</p>
            </div>
          )}

          {validationResult && (
            <section className="validation-section">
              <h2><FaCheckCircle /> Step 2: Validation Results</h2>
              <div className={`validation-banner ${validationResult.is_valid ? 'success' : 'error'}`}>
                <h3>{validationResult.is_valid ? <><FaCheckCircle /> VALIDATION PASSED</> : <><FaTimesCircle /> VALIDATION FAILED</>}</h3>
                <p>
                  {validationResult.is_valid
                    ? 'Your GL data has been successfully validated and is ready for processing.'
                    : 'Please review the errors below and fix your GL file before proceeding.'}
                </p>
              </div>

              {validationResult.key_metrics && (
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-label">Total Transactions</div>
                    <div className="metric-value">
                      {validationResult.key_metrics.total_transactions?.toLocaleString() || 0}
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Total Debits</div>
                    <div className="metric-value">
                      ${validationResult.key_metrics.total_debits?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Total Credits</div>
                    <div className="metric-value">
                      ${validationResult.key_metrics.total_credits?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Difference</div>
                    <div className="metric-value">
                      ${validationResult.key_metrics.debit_credit_difference?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                </div>
              )}

              {!validationResult.is_valid && validationResult.errors && (
                <div className="errors-section">
                  <h3><FaExclamationTriangle /> Error Messages</h3>
                  {validationResult.errors.map((error, idx) => (
                    <div key={idx} className="error-item">
                      <strong>Error {idx + 1}:</strong>
                      <p>{error}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {validationResult?.is_valid && excelFileUrl && (
            <section className="download-section">
              <h2><FaDownload /> Step 3: Download Excel Databook</h2>
              <div className="download-card">
                <p><FaCheckCircle /> Excel databook generated successfully!</p>
                {downloading && (
                  <div className="processing-status" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${processingProgress}%` }}></div>
                    </div>
                    <p>Downloading file... {Math.round(processingProgress)}%</p>
                  </div>
                )}
                <button 
                  onClick={handleDownload} 
                  disabled={downloading}
                  className="btn-primary btn-download"
                >
                  {downloading ? <><FaSpinner className="spinning" /> Downloading...</> : <><FaDownload /> Download Excel Databook</>}
                </button>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}

export default GLProcessing



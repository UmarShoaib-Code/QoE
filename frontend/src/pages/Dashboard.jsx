import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FaHome, FaSignOutAlt, FaChartBar, FaFolder, FaPlus, FaMinus, FaFolderOpen, FaTrash, FaCalendarAlt, FaFileAlt, FaChartPie } from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import LoadingSpinner from '../components/LoadingSpinner'
import './Dashboard.css'

const STORAGE_KEY = 'qoe_projects'

const Dashboard = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newProject, setNewProject] = useState({
    title: '',
    description: ''
  })

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsedProjects = JSON.parse(stored)
        setProjects(parsedProjects)
      } else {
        setProjects([])
      }
    } catch (error) {
      console.error('Failed to load projects from localStorage:', error)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  const saveProjects = (projectsToSave) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projectsToSave))
      setProjects(projectsToSave)
    } catch (error) {
      console.error('Failed to save projects to localStorage:', error)
      alert('Failed to save project. Please try again.')
    }
  }

  const handleCreateProject = (e) => {
    e.preventDefault()
    if (!newProject.title.trim()) return

    const newProjectData = {
      id: Date.now(), // Simple ID generation
      title: newProject.title.trim(),
      description: newProject.description.trim(),
      created_at: new Date().toISOString(),
      files: [],
      databooks: []
    }

    const updatedProjects = [...projects, newProjectData]
    saveProjects(updatedProjects)
    setNewProject({ title: '', description: '' })
    setShowCreateForm(false)
  }

  const handleDeleteProject = (projectId) => {
    console.log('handleDeleteProject called with projectId:', projectId)
    if (!window.confirm('Are you sure you want to delete this project?')) {
      console.log('Delete cancelled by user')
      return
    }

    console.log('Deleting project:', projectId)
    const updatedProjects = projects.filter(p => p.id !== projectId)
    console.log('Updated projects:', updatedProjects)
    saveProjects(updatedProjects)
    console.log('Project deleted successfully')
  }

  const handleOpenProject = (projectId) => {
    console.log('handleOpenProject called with projectId:', projectId)
    try {
      navigate(`/project/${projectId}`)
    } catch (error) {
      console.error('Navigation error:', error)
      window.location.href = `/project/${projectId}`
    }
  }

  return (
    <div className="dashboard-page">
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <div className="user-greeting">
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div>
              <h2>Welcome back</h2>
              <p className="username">{user?.username || 'User'}</p>
            </div>
          </div>
        </div>
        <div className="sidebar-content">
          <button onClick={() => navigate('/')} className="sidebar-button">
            <FaHome /> Home
          </button>
          <button onClick={logout} className="sidebar-button">
            <FaSignOutAlt /> Logout
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <h1><FaChartBar /> Dashboard - My Projects</h1>
        </header>

        <div className="dashboard-content">
          <div className="create-project-section">
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="btn-primary"
            >
              {showCreateForm ? <FaMinus /> : <FaPlus />} Create New Project
            </button>

            {showCreateForm && (
              <form onSubmit={handleCreateProject} className="create-project-form">
                <div className="form-group">
                  <label>Project Title *</label>
                  <input
                    type="text"
                    value={newProject.title}
                    onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
                    placeholder="e.g., Q4 2024 Analysis"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Description (Optional)</label>
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    placeholder="Brief description of this project..."
                    rows="3"
                  />
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn-primary">Create Project</button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="projects-section">
            <h2><FaFolder /> Your Projects</h2>
            {loading ? (
              <LoadingSpinner text="Loading projects..." />
            ) : projects.length === 0 ? (
              <div className="empty-state">
                <p><strong>No projects yet!</strong></p>
                <p>Create your first project using the "Create New Project" section above to start analyzing your GL data.</p>
              </div>
            ) : (
              <div className="projects-grid">
                {projects.map((project) => (
                  <div key={project.id} className="project-card">
                    <div className="project-header">
                      <div className="project-title"><FaFolderOpen /> {project.title}</div>
                    </div>
                    <div className="project-meta">
                      <div className="meta-item">
                        <FaCalendarAlt /> {new Date(project.created_at).toLocaleDateString()}
                      </div>
                      <div className="meta-item">
                        <FaFileAlt /> {project.files?.length || 0} files
                      </div>
                      <div className="meta-item">
                        <FaChartPie /> {project.databooks?.length || 0} reports
                      </div>
                    </div>
                    {project.description && (
                      <div className="project-description">{project.description}</div>
                    )}
                    <div className="project-actions">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          console.log('Open button clicked for project:', project.id)
                          handleOpenProject(project.id)
                        }}
                        className="btn-primary btn-small"
                      >
                        <FaFolderOpen /> Open Project
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          console.log('Delete button clicked for project:', project.id)
                          handleDeleteProject(project.id)
                        }}
                        className="btn-danger btn-small"
                      >
                        <FaTrash /> Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard



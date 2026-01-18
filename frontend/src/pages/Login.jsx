import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FaLock, FaArrowLeft, FaExclamationCircle } from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'
import './Auth.css'

const Login = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const handleQuickLogin = () => {
    const email = formData.email || 'demo@example.com'
    const username = email.split('@')[0] || 'demo'
    
    const mockUser = {
      id: 1,
      email: email,
      username: username,
      full_name: 'Demo User'
    }
    
    const mockToken = '1'
    
    localStorage.setItem('token', mockToken)
    localStorage.setItem('user', JSON.stringify(mockUser))
    api.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`
    
    window.location.href = '/dashboard'
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    handleQuickLogin()
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1><FaLock /> Welcome Back</h1>
          <p>Login to access your QoE Tool dashboard</p>
        </div>

        <Link to="/" className="back-link"><FaArrowLeft /> Back to Home</Link>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your.email@example.com"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
            />
          </div>

          {error && <div className="error-message"><FaExclamationCircle /> {error}</div>}

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
            <Link to="/" className="btn-secondary">Cancel</Link>
          </div>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/signup" className="auth-link">Sign up here</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login



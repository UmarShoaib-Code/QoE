import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FaChartBar, FaArrowLeft, FaExclamationCircle } from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import './Auth.css'

const SignUp = () => {
  const navigate = useNavigate()
  const { signup } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    fullName: '',
    password: '',
    confirmPassword: ''
  })
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    setErrors([])
  }

  const validate = () => {
    const newErrors = []
    
    if (!formData.email) {
      newErrors.push('Email is required')
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.push('Please enter a valid email address')
    }
    
    if (!formData.username) {
      newErrors.push('Username is required')
    } else if (formData.username.length < 3) {
      newErrors.push('Username must be at least 3 characters')
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.push('Username can only contain letters, numbers, and underscores')
    }
    
    if (!formData.password) {
      newErrors.push('Password is required')
    } else if (formData.password.length < 8) {
      newErrors.push('Password must be at least 8 characters')
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.push('Passwords do not match')
    }
    
    return newErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationErrors = validate()
    
    if (validationErrors.length > 0) {
      setErrors(validationErrors)
      return
    }
    
    setLoading(true)
    const result = await signup(
      formData.email,
      formData.username,
      formData.password,
      formData.fullName || null
    )
    
    setLoading(false)
    
    if (result.success) {
      navigate('/login')
    } else {
      setErrors([result.error || 'Failed to create account'])
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1><FaChartBar /> Create Account</h1>
          <p>Join QoE Tool and start analyzing your financial data</p>
        </div>

        <Link to="/" className="back-link"><FaArrowLeft /> Back to Home</Link>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Email Address *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your.email@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Username *</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choose a username"
              required
            />
          </div>

          <div className="form-group">
            <label>Full Name (Optional)</label>
            <input
              type="text"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="John Doe"
            />
          </div>

          <div className="form-group">
            <label>Password *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Minimum 8 characters"
              required
            />
          </div>

          <div className="form-group">
            <label>Confirm Password *</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Re-enter password"
              required
            />
          </div>

          {errors.length > 0 && (
            <div className="error-messages">
              {errors.map((error, idx) => (
                <div key={idx} className="error-message"><FaExclamationCircle /> {error}</div>
              ))}
            </div>
          )}

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Account'}
            </button>
            <Link to="/" className="btn-secondary">Cancel</Link>
          </div>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Login here</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SignUp



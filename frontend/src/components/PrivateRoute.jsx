import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
  const token = localStorage.getItem('token')
  const userData = localStorage.getItem('user')
  const isAuthenticated = user || (token && userData)

  if (loading) {
    return <div>Loading...</div>
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default PrivateRoute



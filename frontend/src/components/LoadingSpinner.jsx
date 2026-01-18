import { FaSpinner } from 'react-icons/fa'
import './LoadingSpinner.css'

const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
  return (
    <div className={`loading-spinner loading-spinner-${size}`}>
      <FaSpinner className="spinning" />
      {text && <span>{text}</span>}
    </div>
  )
}

export default LoadingSpinner


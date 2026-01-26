import { useState } from 'react'
import './App.css'

function App() {
  const [formData, setFormData] = useState({
    school_name: '',
    school_address: '',
    examination_name: '',
    reporting_time: '08:30 a.m.',
    entry_time: '08:45 a.m.',
    cooloff_time: '09:00 a.m. to 09:15 a.m.',
    reading_time: '09:15 a.m. to 09:30 a.m.',
    writing_time: '09:30 a.m. to 11:30 a.m.',
    students_file: null,
    timetable_file: null,
    photos_file: null,
    logo_file: null,
    signature_file: null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = (e) => {
    const { name } = e.target
    const file = e.target.files[0]
    setFormData(prev => ({ ...prev, [name]: file }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const formDataToSend = new FormData()
      formDataToSend.append('school_name', formData.school_name)
      formDataToSend.append('school_address', formData.school_address)
      formDataToSend.append('examination_name', formData.examination_name)
      formDataToSend.append('reporting_time', formData.reporting_time)
      formDataToSend.append('entry_time', formData.entry_time)
      formDataToSend.append('cooloff_time', formData.cooloff_time)
      formDataToSend.append('reading_time', formData.reading_time)
      formDataToSend.append('writing_time', formData.writing_time)
      formDataToSend.append('request_id', `req_${Date.now()}`)
      
      if (formData.students_file) {
        formDataToSend.append('students', formData.students_file)
      }
      if (formData.timetable_file) {
        formDataToSend.append('timetable', formData.timetable_file)
      }
      if (formData.photos_file) {
        formDataToSend.append('photos', formData.photos_file)
      }
      if (formData.logo_file) {
        formDataToSend.append('logo', formData.logo_file)
      }
      if (formData.signature_file) {
        formDataToSend.append('signature', formData.signature_file)
      }

      // Use environment variable for API URL, fallback to relative URL for dev proxy
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      const fetchUrl = `${apiBaseUrl}/api/generate`
      const response = await fetch(fetchUrl, {
        method: 'POST',
        body: formDataToSend
      })

      if (!response.ok) {
        let errorMessage = 'Failed to generate hall tickets'
        let errorDetails = null
        try {
          const errorData = await response.json()
          errorMessage = errorData.error || errorMessage
          errorDetails = errorData.details || errorData.message
        } catch (e) {
          errorMessage = `Server error: ${response.status} ${response.statusText}`
        }
        
        // Create detailed error message
        if (errorDetails) {
          if (Array.isArray(errorDetails)) {
            errorMessage += '\n\n' + errorDetails.join('\n')
          } else {
            errorMessage += '\n\n' + errorDetails
          }
        }
        
        throw new Error(errorMessage)
      }

      // Download the zip file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'hall_tickets.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccess(true)
    } catch (err) {
      console.error('Error:', err)
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        setError('Cannot connect to server. Make sure the backend is running on http://localhost:5001')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="container">
        <header>
          <h1>🎓 Hall Ticket Generator</h1>
          <p>Generate professional hall tickets for your students</p>
        </header>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-sections-row">
            <div className="form-section">
              <h2>School Information</h2>
              <div className="form-group">
                <label htmlFor="school_name">School Name *</label>
                <input
                  type="text"
                  id="school_name"
                  name="school_name"
                  value={formData.school_name}
                  onChange={handleInputChange}
                  required
                  placeholder="Enter school name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="school_address">School Address *</label>
                <textarea
                  id="school_address"
                  name="school_address"
                  value={formData.school_address}
                  onChange={handleInputChange}
                  required
                  placeholder="Enter school address"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label htmlFor="examination_name">Examination Name</label>
                <input
                  type="text"
                  id="examination_name"
                  name="examination_name"
                  value={formData.examination_name}
                  onChange={handleInputChange}
                  placeholder="e.g., ANNUAL EXAMINATION ADMIT CARD"
                />
                <small>Leave empty to use default: "ANNUAL EXAMINATION ADMIT CARD"</small>
              </div>
              <div className="form-group">
                <label htmlFor="logo_file">School Logo (Optional)</label>
                <input
                  type="file"
                  id="logo_file"
                  name="logo_file"
                  accept=".png,.jpg,.jpeg"
                  onChange={handleFileChange}
                />
                <small>School logo image (PNG/JPG)</small>
              </div>
              <div className="form-group">
                <label htmlFor="signature_file">Principal Signature (Optional)</label>
                <input
                  type="file"
                  id="signature_file"
                  name="signature_file"
                  accept=".png,.jpg,.jpeg"
                  onChange={handleFileChange}
                />
                <small>Principal signature image (PNG/JPG)</small>
              </div>
            </div>

            <div className="form-section">
              <h2>Examination Timing (Optional)</h2>
            <div className="form-group">
              <label htmlFor="reporting_time">Reporting Time</label>
              <input
                type="text"
                id="reporting_time"
                name="reporting_time"
                value={formData.reporting_time}
                onChange={handleInputChange}
                placeholder="e.g., 08:30 a.m."
              />
            </div>
            <div className="form-group">
              <label htmlFor="entry_time">Entry to Exam Hall</label>
              <input
                type="text"
                id="entry_time"
                name="entry_time"
                value={formData.entry_time}
                onChange={handleInputChange}
                placeholder="e.g., 08:45 a.m."
              />
            </div>
            <div className="form-group">
              <label htmlFor="cooloff_time">Cool-off Time</label>
              <input
                type="text"
                id="cooloff_time"
                name="cooloff_time"
                value={formData.cooloff_time}
                onChange={handleInputChange}
                placeholder="e.g., 09:00 a.m. to 09:15 a.m."
              />
            </div>
            <div className="form-group">
              <label htmlFor="reading_time">Reading Time</label>
              <input
                type="text"
                id="reading_time"
                name="reading_time"
                value={formData.reading_time}
                onChange={handleInputChange}
                placeholder="e.g., 09:15 a.m. to 09:30 a.m."
              />
            </div>
            <div className="form-group">
              <label htmlFor="writing_time">Writing Time</label>
              <input
                type="text"
                id="writing_time"
                name="writing_time"
                value={formData.writing_time}
                onChange={handleInputChange}
                placeholder="e.g., 09:30 a.m. to 11:30 a.m."
              />
            </div>
            <small>Leave empty to use default timings</small>
            </div>
          </div>

          <div className="form-section">
            <h2>Upload Files</h2>
            <div className="form-group">
              <label htmlFor="students_file">Student Details Excel *</label>
              <input
                type="file"
                id="students_file"
                name="students_file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                required
              />
              <small>Excel file with student details (multiple sheets, one per class)</small>
            </div>
            <div className="form-group">
              <label htmlFor="timetable_file">Timetable Excel *</label>
              <input
                type="file"
                id="timetable_file"
                name="timetable_file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                required
              />
              <small>Excel file with exam timetable</small>
            </div>
            <div className="form-group">
              <label htmlFor="photos_file">Student Photos (ZIP) *</label>
              <input
                type="file"
                id="photos_file"
                name="photos_file"
                accept=".zip"
                onChange={handleFileChange}
                required
              />
              <small>ZIP file containing class folders with student photos [named with their admn no]</small>
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              <strong>Success!</strong> Hall tickets generated and downloaded.
      </div>
          )}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Generating...' : 'Generate Hall Tickets'}
        </button>
        </form>
      </div>
    </div>
  )
}

export default App

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
    show_photo_box: true,
    students_file: null,
    timetable_file: null,
    photos_file: null,
    logo_file: null,
    signature_file: null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})

  const validateField = (name, value) => {
    switch (name) {
      case 'school_name':
        if (!value || value.trim().length === 0) {
          return 'School name is required'
        }
        if (value.trim().length < 3) {
          return 'School name must be at least 3 characters'
        }
        return null
      case 'school_address':
        if (!value || value.trim().length === 0) {
          return 'School address is required'
        }
        if (value.trim().length < 10) {
          return 'School address must be at least 10 characters'
        }
        return null
      default:
        return null
    }
  }

  const getFieldDisplayName = (fieldName) => {
    const fieldNames = {
      'school_name': 'School name',
      'school_address': 'School address',
      'students_file': 'Student details Excel file',
      'timetable_file': 'Timetable Excel file',
      'photos_file': 'Student photos ZIP file',
      'logo_file': 'School logo',
      'signature_file': 'Principal signature'
    }
    return fieldNames[fieldName] || fieldName
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    
    // Validate field
    const error = type === 'checkbox' ? null : validateField(name, value)
    setFieldErrors(prev => ({
      ...prev,
      [name]: error
    }))
    
    setFormData(prev => {
      const newData = { ...prev, [name]: type === 'checkbox' ? checked : value }
      // If photo box is turned off, clear the photos file
      if (name === 'show_photo_box' && !checked) {
        newData.photos_file = null
        // Reset the file input
        const fileInput = document.getElementById('photos_file')
        if (fileInput) {
          fileInput.value = ''
        }
        // Clear photos file error
        setFieldErrors(prev => ({
          ...prev,
          photos_file: null
        }))
      }
      return newData
    })
  }

  const validateFile = (file, allowedTypes, maxSizeMB = 50, isRequired = false, fieldName = '') => {
    // If file is required but not provided
    if (isRequired && !file) {
      const displayName = getFieldDisplayName(fieldName)
      return `${displayName} is required`
    }
    
    // If no file and not required, no error
    if (!file) {
      return null
    }
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    const allowedExtensions = allowedTypes.map(type => type.replace('.', '').toLowerCase())
    const fileExt = fileExtension.replace('.', '').toLowerCase()
    
    if (!allowedExtensions.includes(fileExt)) {
      return `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`
    }
    
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    if (file.size > maxSizeBytes) {
      return `File size exceeds ${maxSizeMB}MB limit`
    }
    
    return null
  }

  const handleFileChange = (e) => {
    const { name } = e.target
    const file = e.target.files[0]
    
    // Only validate file type and size on change, not required status
    // Required validation happens on form submit (before Generate button)
    let error = null
    if (file) {
      if (name === 'students_file' || name === 'timetable_file') {
        error = validateFile(file, ['.xlsx', '.xls'], 50, false, name)
      } else if (name === 'photos_file') {
        error = validateFile(file, ['.zip'], 100, false, name)
      } else if (name === 'logo_file' || name === 'signature_file') {
        error = validateFile(file, ['.png', '.jpg', '.jpeg'], 10, false, name)
      }
    } else {
      // Clear error if file is removed (required status will be checked on submit)
      error = null
    }
    
    // Update errors: show type/size errors immediately, clear when valid file is selected
    // Required errors are only set on form submit, not here
    setFieldErrors(prev => {
      const newErrors = { ...prev }
      if (error) {
        // File has type/size error
        newErrors[name] = error
      } else if (file) {
        // Valid file selected - clear any errors (including required errors from previous submit)
        delete newErrors[name]
      } else {
        // File removed - clear type/size errors, but required errors will show on next submit
        if (prev[name] && !prev[name].includes('required') && !prev[name].includes('is required')) {
          delete newErrors[name]
        }
      }
      return newErrors
    })
    
    setFormData(prev => ({ ...prev, [name]: file }))
  }

  const handleFileRemove = (fieldName) => {
    setFormData(prev => ({ ...prev, [fieldName]: null }))
    // Clear field error
    setFieldErrors(prev => ({
      ...prev,
      [fieldName]: null
    }))
    // Reset the file input
    const fileInput = document.getElementById(fieldName)
    if (fileInput) {
      fileInput.value = ''
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Validate form before submission
    const errors = {}
    
    // Validate required text fields
    const schoolNameError = validateField('school_name', formData.school_name)
    if (schoolNameError) errors.school_name = schoolNameError
    
    const schoolAddressError = validateField('school_address', formData.school_address)
    if (schoolAddressError) errors.school_address = schoolAddressError
    
    // Validate required files - show error if not selected (only on submit before Generate)
    const studentsFileError = validateFile(formData.students_file, ['.xlsx', '.xls'], 50, true, 'students_file')
    if (studentsFileError) {
      errors.students_file = studentsFileError
    }
    
    const timetableFileError = validateFile(formData.timetable_file, ['.xlsx', '.xls'], 50, true, 'timetable_file')
    if (timetableFileError) {
      errors.timetable_file = timetableFileError
    }
    
    // Validate photos file only if photo box is enabled
    if (formData.show_photo_box) {
      const photosFileError = validateFile(formData.photos_file, ['.zip'], 100, true, 'photos_file')
      if (photosFileError) {
        errors.photos_file = photosFileError
      }
    }
    
    // Validate optional files (not required, but check type/size if provided)
    if (formData.logo_file) {
      const fileError = validateFile(formData.logo_file, ['.png', '.jpg', '.jpeg'], 10, false, 'logo_file')
      if (fileError) errors.logo_file = fileError
    }
    
    if (formData.signature_file) {
      const fileError = validateFile(formData.signature_file, ['.png', '.jpg', '.jpeg'], 10, false, 'signature_file')
      if (fileError) errors.signature_file = fileError
    }
    
    setFieldErrors(errors)
    
    if (Object.keys(errors).length > 0) {
      setError('Please fix the errors in the form before submitting')
      // Scroll to first error
      setTimeout(() => {
        const firstErrorField = Object.keys(errors)[0]
        const errorElement = document.getElementById(firstErrorField) || 
                           document.querySelector(`[name="${firstErrorField}"]`)
        if (errorElement) {
          errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
          errorElement.focus()
        }
      }, 100)
      return
    }
    
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
      formDataToSend.append('show_photo_box', formData.show_photo_box ? 'true' : 'false')
      formDataToSend.append('request_id', `req_${Date.now()}`)
      
      if (formData.students_file) {
        formDataToSend.append('students', formData.students_file)
      }
      if (formData.timetable_file) {
        formDataToSend.append('timetable', formData.timetable_file)
      }
      // Only send photos file if photo box is enabled
      if (formData.show_photo_box && formData.photos_file) {
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

        <form onSubmit={handleSubmit} className="form" noValidate>
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
                  placeholder="Enter school name"
                  className={fieldErrors.school_name ? 'input-error' : ''}
                />
                {fieldErrors.school_name && (
                  <span className="field-error">{fieldErrors.school_name}</span>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="school_address">School Address *</label>
                <textarea
                  id="school_address"
                  name="school_address"
                  value={formData.school_address}
                  onChange={handleInputChange}
                  placeholder="Enter school address"
                  rows="3"
                  className={fieldErrors.school_address ? 'input-error' : ''}
                />
                {fieldErrors.school_address && (
                  <span className="field-error">{fieldErrors.school_address}</span>
                )}
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
                <small>Leave empty to use default: "ADMIT CARD"</small>
              </div>
              <div className="form-group">
                <label htmlFor="logo_file">School Logo (Optional)</label>
                <input
                  type="file"
                  id="logo_file"
                  name="logo_file"
                  accept=".png,.jpg,.jpeg"
                  onChange={handleFileChange}
                  className={fieldErrors.logo_file ? 'input-error' : ''}
                />
                {fieldErrors.logo_file && (
                  <span className="field-error">{fieldErrors.logo_file}</span>
                )}
                {formData.logo_file && (
                  <div className="file-display">
                    <span className="file-name">{formData.logo_file.name}</span>
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={() => handleFileRemove('logo_file')}
                    >
                      ✕
                    </button>
                  </div>
                )}
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
                  className={fieldErrors.signature_file ? 'input-error' : ''}
                />
                {fieldErrors.signature_file && (
                  <span className="field-error">{fieldErrors.signature_file}</span>
                )}
                {formData.signature_file && (
                  <div className="file-display">
                    <span className="file-name">{formData.signature_file.name}</span>
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={() => handleFileRemove('signature_file')}
                    >
                      ✕
                    </button>
                  </div>
                )}
                <small>Principal signature image (PNG/JPG)</small>
              </div>
            </div>

            <div className="form-section">
              <h2>Examination Timing (Optional)</h2>
              <div className="timing-fields-grid">
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
                className={fieldErrors.students_file ? 'input-error' : ''}
              />
              {fieldErrors.students_file && (
                <span className="field-error">{fieldErrors.students_file}</span>
              )}
              {formData.students_file && (
                <div className="file-display">
                  <span className="file-name">{formData.students_file.name}</span>
                  <button
                    type="button"
                    className="remove-file-btn"
                    onClick={() => handleFileRemove('students_file')}
                  >
                    ✕
                  </button>
                </div>
              )}
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
                className={fieldErrors.timetable_file ? 'input-error' : ''}
              />
              {fieldErrors.timetable_file && (
                <span className="field-error">{fieldErrors.timetable_file}</span>
              )}
              {formData.timetable_file && (
                <div className="file-display">
                  <span className="file-name">{formData.timetable_file.name}</span>
                  <button
                    type="button"
                    className="remove-file-btn"
                    onClick={() => handleFileRemove('timetable_file')}
                  >
                    ✕
                  </button>
                </div>
              )}
              <small>Excel file with exam timetable</small>
            </div>
            <div className="form-group">
              <label htmlFor="show_photo_box" className="switch-label">
                <span>Include student photo on hall tickets</span>
                <div className="switch-container">
                  <input
                    type="checkbox"
                    id="show_photo_box"
                    name="show_photo_box"
                    checked={formData.show_photo_box}
                    onChange={handleInputChange}
                    className="switch-input"
                  />
                  <span className="switch-slider"></span>
                </div>
              </label>
            </div>
            {formData.show_photo_box && (
              <div className="form-group">
                <label htmlFor="photos_file">Student Photos (ZIP) *</label>
                <input
                  type="file"
                  id="photos_file"
                  name="photos_file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className={fieldErrors.photos_file ? 'input-error' : ''}
                />
                {fieldErrors.photos_file && (
                  <span className="field-error">{fieldErrors.photos_file}</span>
                )}
                {formData.photos_file && (
                  <div className="file-display">
                    <span className="file-name">{formData.photos_file.name}</span>
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={() => handleFileRemove('photos_file')}
                    >
                      ✕
                    </button>
                  </div>
                )}
                <small>ZIP file containing class folders with student photos [named with their admn no]</small>
              </div>
            )}
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
